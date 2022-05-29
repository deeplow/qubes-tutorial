import logging
import argparse
import sys
from queue import Queue

import utils
import watchers
from interactions import Interaction

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
    watchers.init_watchers(scope, interactions_q)

    if args.create:
        create_tutorial(args.create, scope, interactions_q)
    else:
        start_tutorial("tutorial.tut", scope, interactions_q)

    watchers.stop_watchers(scope)


def start_tutorial(infile, scope, interactions_q):
    logging.info("starting tutorial")
    tutorial = Tutorial(infile)

    # TODO global logs monitoring

    step = tutorial.get_first_step()
    while not step.is_last():
        logging.info('currently on step "{}"'.format(step.name))
        interaction = interactions_q.get(block=True)

        if step.transition(interaction) == None:
            logging.debug("interaction does not transition")
            continue

        step = tutorial.get_next(step, interaction)

def create_tutorial(outfile, scope, interactions_q):
    logging.info("creating tutorial")

    tutorial = Tutorial()

    try:
        watchers.init_watchers(scope, interactions_q)
        # TODO global logs monitoring

        input("Press ctrl+c to stop")

    except KeyboardInterrupt:
        utils.gen_report(interactions_q)

def init_gui():
    pass


class TutorialStep:
    """ Represents a current step in a tutorial """

    transitions = {} # map: interaction -> step

    def __init__(self, name: str):
        self.name = name

    def is_last(self):
        return self.name == "end"

    def add_transition(self, interaction: Interaction,
                             target_step: TutorialStep):
        interactions = self.transitions.get(target_step)
        if interactions == None:
            self.transitions[target_step] = [interaction]
        else:
            self.transitions[target_step].append(interaction)

    def transition(self, interaction: Interaction):
        for possible_interaction in self.transitions.keys():
            if possible_interaction == interaction: # FIXME in the future check if is subset
                return self.transitions.get(possible_interaction)
        return None

class Tutorial:
    """ Represents a tutorial's steps and their transitions

    The tutorial is internally represented as a graph
    where system states are nodes and edges are interactions.

    "Steps" are the nodes and "interactions" are the arcs
    """

    create_mode = False

    step_map = {} # maps a step's name to a step object

    def __init__(self, infile=None):
        if not infile:
            self.create_mode = True
            self.add_first_step()

    def _load(self, infile):
        # FIXME remove hardcoded

        # First create all Nodes, only then edges
        pass

    def add_first_step(self) -> None:
        pass

    def get_first_step(self) -> None:
        return self.step_map.get("start")

    def add_step(self, step_name: str, step: TutorialStep) -> None:
        if step_name not in self.step_map.keys():
            self.step_map[step_name] = TutorialStep(step_name)
        else:
            logging.error("Step {} has been defined twice".format(step_name))

    def get_step(self, step_name: str) -> TutorialStep:
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

if __name__ == "__main__":
    main()
