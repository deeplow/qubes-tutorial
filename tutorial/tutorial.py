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

    node = tutorial.get_first_node()
    while node != "end":
        logging.info('currently on node "{}"'.format(node))
        interaction = interactions_q.get(block=True)

        if not tutorial.has_transition(node, interaction):
            logging.debug("interaction does not transition")
            continue

        node = tutorial.get_next(node, interaction)

def create_tutorial(outfile, scope, interactions_q):
    logging.info("creating tutorial")

    try:
        watchers.init_watchers(scope, interactions_q)
        # TODO global logs monitoring

        input("Press ctrl+c to stop")

    except KeyboardInterrupt:
        utils.gen_report(interactions_q)

def init_gui():
    pass


class Tutorial:
    def __init__(self, infile):
        pass

    def get_first_node(self):
        return "start"

    def has_transition(self, node: str, interaction: Interaction) -> bool:
        return True

    def get_next(self, node: str, interaction: Interaction) -> str:
        if node == "start":
            return "node1"
        if node == "node1":
            return "node2"
        if node == "node2":
            return "end"

if __name__ == "__main__":
    main()
