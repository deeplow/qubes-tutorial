import logging
import argparse
import sys
from queue import Queue
import yaml
import json
from collections import OrderedDict

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

import qubes_tutorial.utils as utils
import qubes_tutorial.watchers as watchers
from qubes_tutorial.interactions import Interaction

interactions = []

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(
            description='Integrated tutorials tool for Qubes OS')

    parser.add_argument('--create', '-c',
                        type=argparse.FileType('w', encoding='UTF-8'),
                        metavar="FILE",
                        help='Create a tutorial')

    parser.add_argument('--scope', '-s',
                        type=str,
                        help='qubes affected (e.g. --scope=personal,work)')

    args = parser.parse_args()

    scope = list()
    if args.scope:
        scope = [x.strip() for x in args.scope.split(",")]

    interactions_q = Queue()
    watchers.init_watchers(scope)

    if args.create:
        create_tutorial(args.create, scope, interactions_q)
    else:
        tutorial = Tutorial()
        start_tutorial(tutorial, interactions_q)

    watchers.stop_interaction_logger(scope)


def start_tutorial(tutorial, interactions_q):
    logging.info("starting tutorial")

    # TODO global logs monitoring

    step = tutorial.get_first_step()
    while not step.is_last():
        logging.info('currently on step "{}"'.format(step.name))
        interaction = interactions_q.get(block=True)

        if not step.has_transition(interaction):
            logging.debug("interaction does not transition")
            continue

        step = step.next(interaction)

def create_tutorial(outfile, scope, interactions_q):
    logging.info("creating tutorial")

    tutorial = Tutorial()

    try:
        watchers.start_interaction_logger(scope, interactions_q)
        # TODO global logs monitoring

        input("Press ctrl+c to stop")

    except KeyboardInterrupt:
        utils.gen_report(interactions_q)

def init_gui():
    pass


class Step:
    """ Represents a current step in a tutorial """

    def __init__(self, name: str):
        self.name = name
        self.transitions = OrderedDict() # map: interaction -> step

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

    def __init__(self):
        self.step_map = OrderedDict() # maps a step's name to a step object

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


    def load_as_yaml(self, yaml_text):
        """
        Loads tutorial data from a list of steps
        """
        steps_data = yaml.safe_load(yaml_text)

        # create all steps (nodes)
        steps = []
        for step_data in steps_data:
            step = Step(step_data['name'])
            self.add_step(step)
        self.add_step(Step('end'))

        # add all transitions (edges)
        for step_data in steps_data:
            step = self.get_step(step_data['name'])
            for transition in step_data['transitions']:
                next_step = self.get_step(transition['step'])
                interaction_type = transition['interaction_type']
                interaction = Interaction(interaction_type)

        self.check_integrity()

    def load_as_file(self, file_path):
        if file_path.endswith("yaml") or file_path.endswith("yml"):
            self._load_as_file_yaml(file_path)
        elif file_path.endswith("md"):
            self._load_as_file_literate_yaml(file_path)
        else:
            import pudb; pu.db
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

    def get_first_step(self) -> None:
        return self.step_map.get("start")

    def add_step(self, step: Step) -> None:
        if step.name not in self.step_map.keys():
            self.step_map[step.name] = step
        else:
            raise TutorialDuplicateStepException(step.name)
            logging.error("Step {} has been defined twice".format(step.name))

    def get_step(self, step_name: str):
        return self.step_map.get(step_name)

    def add_transition(self, source_step_name: str, interaction: Interaction,
                       target_step_name: str) -> None:

        source_step = self.step_map.get(source_step_name)
        target_step = self.step_map.get(target_step_name)

        if not source_step:
            logging.error("Source step {} need to be created before\
                trying to add interaction to it".format(source_step_name))
            return
        elif not target_step:
            logging.error("Target step {} need to be created before\
                trying to add interaction to it".format(target_step_name))
            return

        source_step.add_transition(interaction, target_step)
        target_step.add_transition(interaction, source_step)


    """
    def has_transition(self, source_step_name: str, interaction: Interaction, target_step_name: str) -> bool:
        source_step = self.get_step(source_step_name)

        if source_step:
            return source_step.has_transition(interaction, target_step_name)
        else:
            return False
    """

    def get_next(self, node: str, interaction: Interaction) -> str:
        if node == "start":
            return "node1"
        if node == "node1":
            return "node2"
        if node == "node2":
            return "end"

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

class TutorialApp(Gtk.Application):

    def __init__(self):
        super().__init__()
        self.set_application_id("org.qubes.qui.Tutorial")
        print("ran this")

    def do_activate(self):
        print("do activate")



if __name__ == "__main__":
    t = Tutorial()
    t.load_as_file("qubes_tutorial/included_tutorials/onboarding-tutorial-1/README.md")
    t.start_tutorial()
    #main()
    #app = TutorialApp()
    #app.run()
