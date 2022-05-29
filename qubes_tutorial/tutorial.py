import argparse
import asyncio
from collections import OrderedDict
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import json
import yaml
import logging
from queue import Queue
import os
import sys
import subprocess
import time

from gi.repository import GLib

import qubes_tutorial.utils as utils
import qubes_tutorial.watchers as watchers
from qubes_tutorial.interactions import Interaction

interactions = []

def start_tutorial(tutorial_path):
    try:
        print("staring ui as separate process...")
        tutorial_dir_path = os.path.dirname(tutorial_path)
        import qubes_tutorial.app
        parent_module_path =  os.path.dirname(os.path.dirname(
                                os.path.realpath(qubes_tutorial.app.__file__)))
        ui = subprocess.Popen(
            ["python3", "-m", qubes_tutorial.app.__name__,
                        "--dir", tutorial_dir_path],
            cwd=parent_module_path
        )

        # start controller only after UI initializes
        time.sleep(0.5)
        print("staring controller...")
        tutorial = Tutorial()
        tutorial.load_as_file(tutorial_path)
        tutorial.start()

    finally:
        ui.kill()

def create_tutorial(outfile, scope):
    interactions_q = Queue()
    watchers.start_interaction_logger(scope, interactions_q)

    # TODO tutorial creation logic

    watchers.stop_interaction_logger(scope)

def create_tutorial(outfile, scope, interactions_q):
    logging.info("creating tutorial")

    tutorial = Tutorial()

    try:
        watchers.start_interaction_logger(scope, interactions_q)
        # TODO global logs monitoring

        input("Press ctrl+c to stop")

    except KeyboardInterrupt:
        utils.gen_report(interactions_q)


class Step:
    """ Represents a current step in a tutorial """

    def __init__(self, name: str, ui_dict: dict=None):
        self.name = name
        self.transitions = OrderedDict() # map: interaction -> step
        self.ui_dict = ui_dict

    def setup(self):
        """
        Initialize the step
        """

        # Sends a notification to the tutorial UI that it should update
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.qubes.tutorial.ui', '/')
        setup_ui = proxy.get_dbus_method('setup_ui', 'org.qubes.tutorial.ui')
        logging.info(setup_ui(self.ui_dict))

    def get_name(self):
        return self.name

    def is_first(self):
        return self.name == "start"

    def is_last(self):
        return self.name == "end"

    def add_transition(self, interaction: Interaction, target_step):
        if self.has_transition(interaction):
            raise TutorialDuplicateTransitionException(self, target_step)

        self.transitions[interaction] = target_step

    def has_transition(self, interaction: Interaction):
        for tentative_interaction in self.transitions.keys():
            if interaction == tentative_interaction:
                return True
        return False

    def get_next_steps(self):
        """
        Returns the steps to which the current node can transition.
        """
        return self.transitions.values()

    def get_possible_interactions(self):
        return self.transitions.keys()

    def next(self, interaction: Interaction):
        for possible_interaction in self.transitions.keys():
            if possible_interaction == interaction: # FIXME in the future check if is subset
                return self.transitions.get(possible_interaction)
        return None

    def dump(self):
        dump = { "name": self.name }
        if len(self.transitions) > 0:
            dump["transitions"] = [t.dump() for t in self.transitions]

        return dump


class Tutorial:
    """ Represents a tutorial's steps and their transitions

    The tutorial is internally represented as a graph
    where system states are nodes and edges are interactions.

    "Steps" are the nodes and "interactions" are the arcs
    """

    def __init__(self, interactions_q=None):
        self.tutorial_dir = None
        self.step_map = OrderedDict() # maps a step's name to a step object
        if interactions_q is None:
            self.interactions_q = Queue()
        else:
            self.interactions_q = interactions_q
        TutorialInteractionsListener(self.interactions_q)

        # setup tutorial loop
        #   Currently dbus-python only supports Glib event loop (can't have our own)
        #   https://dbus.freedesktop.org/doc/dbus-python/tutorial.html#setting-up-an-event-loop
        #
        #   Given that we use dbus to handle interactions, we have to use GLib.
        self.loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(self.loop)
        self.main_context = GLib.MainContext.default()

    def check_integrity(self):
        """
        Checks if the tutorial makes sense
        """
        # has a first and last step
        self.get_step("start")
        self.get_step("end")

        # TODO last step is reachable from first step

        # TODO is a directed acyclic graph

        # TODO has no dead-ends

        # TODO all steps are reachable

    def get_scope(self):
        """
        Returns the list of VMs that are affected by the tutorial
        """
        # TODO complete function by parsing all VMs and components in all steps
        return []

    def load_as_yaml(self, yaml_text):
        """
        Loads tutorial data from a list of steps
        """
        steps_data = yaml.safe_load(yaml_text)

        # create all steps (nodes)
        steps = []
        for step_data in steps_data:
            step = Step(step_data['name'], step_data['ui'])
            self.add_step(step)
        self.add_step(Step('end'))

        # add all transitions (edges)
        for step_data in steps_data:
            current_step = self.get_step(step_data['name'])
            for transition in step_data['transitions']:
                next_step = self.get_step(transition['step'])
                interaction = transition['interaction']
                interaction = Interaction(interaction)
                self.add_transition(current_step, interaction, next_step)

        self.check_integrity()

    def load_as_file(self, file_path):
        if file_path.endswith("yaml") or file_path.endswith("yml"):
            self.tutorial_dir = os.path.dirname(file_path)
            self._load_as_file_yaml(file_path)
        elif file_path.endswith("md"):
            self.tutorial_dir = os.path.dirname(file_path)
            self._load_as_file_literate_yaml(file_path)
        else:
            raise Exception("File not found: {}".format(file_path))

    def _load_as_file_yaml(self, file_path):
        with open(file_path, 'r') as f:
            return f.read()

    def _load_as_file_literate_yaml(self, file_path):
        """
        Load tutorial from a literate markdown-yaml file
        """
        md_text = ""
        yaml_text = ""
        with open(file_path, 'r') as f:
            md_text = f.readlines()

        # extract YAML blocks from Markdown
        in_yaml_block = False
        for md_line in md_text:
            if "```yaml" in md_line:
                in_yaml_block = True
            elif in_yaml_block:
                if md_line == "```\n":
                    in_yaml_block = False
                else:
                    yaml_text += md_line

        self.load_as_yaml(yaml_text)

    def save_as_text(self):
        tutorial = {
            "steps": [step.dump() for step in self.step_map.values()]
        }
        return yaml.safe_dump(tutorial)

    def save_as_file(self, outfile):
        with open(outfile, 'w'):
            tutorial_text = self.save_as_text()
            outfile.write(json.dumps(tutorial_text))

    def start(self):
        """
        Plays the tutorial
        """
        logging.info("starting tutorial")

        self.current_step = self.get_first_step()
        self.current_step.setup()

        #watchers.start_interaction_logger(self.get_scope(), interactions_q)
        self.glib_update(self.main_context, self.loop)
        self.loop.run_forever()

    def stop_loop(self):
        self.loop.close()
        #watchers.stop_interaction_logger(self.get_scope())

    def glib_update(self, main_context, loop):
        while main_context.pending():
            main_context.iteration(False)

        self.process_interactions()
        self.loop.call_later(.01, self.glib_update, main_context, loop)

    def process_interactions(self):
        while not self.interactions_q.empty():
            logging.info('currently on step "{}"'.format(self.current_step.name))

            interaction = self.interactions_q.get()
            logging.info("processed interaction " + str(interaction))

            if not self.current_step.has_transition(interaction):
                logging.debug("interaction does not transition")
                continue

            next_step = self.current_step.next(interaction)
            if next_step.is_last():
                pass # FIXME do something
            else:
                self.current_step = next_step

                # FIXME add the following to GLib idle
                self.current_step.setup()

    def add_step(self, step: Step) -> None:
        if step.name not in self.step_map.keys():
            self.step_map[step.name] = step
        else:
            raise TutorialDuplicateStepException(step.name)
            logging.error("Step {} has been defined twice".format(step.name))

    def get_first_step(self) -> Step:
        return self.step_map.get("start")

    def get_last_step(self) -> Step:
        return self.step_map.get("end")

    def get_step(self, step_name: str):
        return self.step_map.get(step_name)

    def get_steps(self):
        return self.step_map.values()

    def add_transition(self, source_step: Step, interaction: Interaction,
                       target_step: Step) -> None:

        if not source_step:
            logging.error("Source step {} need to be created before\
                trying to add interaction to it".format(source_step.get_name()))
            return
        elif not target_step:
            logging.error("Target step {} need to be created before\
                trying to add interaction to it".format(target_step.get_name()))
            return

        source_step.add_transition(interaction, target_step)

    def has_transition(self, source_step_name: str, interaction: Interaction, target_step_name: str) -> bool:
        source_step = self.get_step(source_step_name)

        if source_step:
            return source_step.has_transition(interaction, target_step_name)
        else:
            return False

    def get_next(self, node: str, interaction: Interaction) -> str:
        if node == "start":
            return "node1"
        if node == "node1":
            return "node2"
        if node == "node2":
            return "end"

class TutorialDebuggable(Tutorial):

    def generate_successful_interaction_sequences(self):
        """
        Returns the lists with all the possible interaction sequences (excluding
        cycles) that take the user from the start until the end.
        """

        success_interaction_sequences = []
        start_step = self.get_first_step()
        end_step = self.get_last_step()

        def find_all_interaction_paths(current_step, visited_steps, path):
            visited_steps.append(current_step)

            if current_step == end_step:
                success_interaction_sequences.append(path.copy())
            else:
                for interaction in current_step.get_possible_interactions():
                    next_step = current_step.next(interaction)
                    if next_step not in visited_steps:
                        path.append(interaction)
                        find_all_interaction_paths(next_step, visited_steps, path)

            if len(path) > 0:
                path.pop()
            visited_steps.remove(current_step)

        visited = []
        path = []
        find_all_interaction_paths(start_step, visited, path)

        return success_interaction_sequences

class TutorialException(Exception):
    def __init__(self, message="Exception occured in the tutorial."):
        super().__init__(message)

class TutorialDuplicateStepException(TutorialException):
    def __init__(self, step_name: str):
        message = "Step '{}' is duplicated".format(step_name)
        super().__init__(message)

class TutorialDuplicateTransitionException(TutorialException):
    def __init__(self, source_step: Step, target_step: Step):
        message = "Step '{}' already has a transition to step '{}'".\
            format(source_step.name, target_step.name)
        super().__init__(message)

class TutorialInteractionsListener(dbus.service.Object):

    def __init__(self, interactions_q):
        self.interactions_q = interactions_q

        # start dbus loop
        DBusGMainLoop(set_as_default=True)

        # setup dbus for listening for events
        bus_name = dbus.service.BusName("org.qubes.tutorial.interactions",
                                        bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/')

    @dbus.service.method('org.qubes.tutorial.interactions')
    def register_interaction(self, interaction_str):
        logging.info("Registered interaction " + str(interaction_str))
        interaction = Interaction(interaction_str)
        self.interactions_q.put(interaction)
        return "registered interaction"


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(
            description='Integrated tutorials tool for Qubes OS')

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--create', '-c',
                        type=argparse.FileType('w', encoding='UTF-8'),
                        metavar="FILE",
                        help='Create a tutorial')

    action_group.add_argument('--load', '-l',
                        type=str,
                        metavar="FILE",
                        help='Load a tutorial from a .yaml or literate .md.'\
                            + "\nFor example 'qubes_tutorial/included_tutorials/onboarding-tutorial-1/README.md'")

    parser.add_argument('--scope', '-s',
                        type=str,
                        help='qubes affected (e.g. --scope=personal,work)')

    args = parser.parse_args()

    scope = list()
    if args.scope:
        scope = [x.strip() for x in args.scope.split(",")]

    if args.create:
        create_tutorial(args.create, scope)
    elif args.load:
        start_tutorial(args.load)


if __name__ == '__main__':
    main()
