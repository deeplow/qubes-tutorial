import logging
import argparse
import sys
from queue import Queue

import utils
import watchers

interactions = []

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(
            description='Integrated tutorials tool for Qubes OS')

    action = parser.add_mutually_exclusive_group(required=True)

    action.add_argument('--create',
                        type=argparse.FileType('w', encoding='UTF-8'),
                        nargs='?',
                        default=sys.stdout,
                        help='Create a tutorial')

    action.add_argument('--load',
                        nargs=1,
                        default='tutorial.yaml',
                        help='Loading a tutorial from a file')

    parser.add_argument('-s', '--scope',
                        type=str,
                        help='qubes affected (e.g. --scope=personal,work)')

    args = parser.parse_args()

    scope = list()
    if args.scope:
        scope = [x.strip() for x in args.scope.split(",")]

    interactions_q = Queue()

    if args.create:
        create_tutorial(args.create, scope, interactions_q)

def start_tutorial():
    logging.info("starting tutorial")
    load_tutorial()

def create_tutorial(outfile, scope, interactions_q):
    logging.info("creating tutorial")

    try:
        watchers.init_watchers(scope, interactions_q)
        # TODO global logs monitoring

        input("Press ctrl+c to stop")

    except KeyboardInterrupt:
        utils.gen_report(interactions_q)
    finally:
        watchers.stop_watchers(scope)


def load_tutorial():
    logging.info("loading tutorial")

def init_gui():
    pass


if __name__ == "__main__":
    main()
