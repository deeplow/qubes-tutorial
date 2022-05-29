import logging
import sys,os
import time
import re
from queue import Queue
import threading
import systemd.journal
import asyncio

from qubes_tutorial.interactions import *
import qubes_tutorial.utils as utils

watchers = list()
watchers_threads = list()

class InteractionLogger:
    """Singleton class manging all watchers"""

    def __init__(self, scope: list):
        self.interactions = Queue()

        self.watchers = []

        # vm-specific logs monitoring
        for vm in scope:
            utils.enable_vm_debug(vm)
            self.watchers.append(
                GuidLogWatcher(vm))

        # qrexec monitoring
        self.watchers.append(
            QrexecWatcher(scope))

    def run(self):
        for watcher in self.watchers:
            self.interactions.put(Interaction("FIXME something"))

    def get_interaction(self):
        """gets the next interaction """

def start_interaction_logger(scope, interactions_q):
    global interactor
    interactor = InteractionLogger(scope)

    interactor_thread = threading.Thread(target=interactor.run, daemon=True)
    interactor_thread.start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    finally:
        loop.close()


async def run():
    pass
    #async for i in ticker(1, 10):
    #    print(i)

def stop_interaction_logger(scope: list):
    for vm in scope:
        utils.disable_vm_debug(vm)

class AbstractWatcher:
    """ Generic log reader """

    def __init__(self):
        self.terminate = False

    def run(self):
        pass

    def stop(self):
        self.terminate = True

    def generate_interaction(self, line):
        pass

class LogWatcher(AbstractWatcher):
    """ Reads logs from a file """

    log_file_path = "/dev/null"
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        logging.info("Watching log {}".format(self.log_file_path))
        super().__init__()

    def run(self):
        while not os.path.exists(self.log_file_path):
            logging.info("Non-existant log file: {}".format(self.log_file_path))
            logging.info("  waiting for it to be created")
            yield None

        with open(self.log_file_path, 'r') as f:
            #f.seek(0, os.SEEK_END) # ignore old logs (start from end)
            while not self.terminate:
                line = self.loop(f)
                yield self.generate_interaction(line)

    def loop(self, file):
            line = ''
            while not self.terminate and (len(line) == 0 or line[-1] != '\n'):
                tail = file.readline()
                if tail == '':
                    time.sleep(0.01)
                    continue
                line += tail
            yield line



class GuidLogWatcher(LogWatcher):
    """ Reads logs from guid interactions for qube """

    def __init__(self, vm):
        log_file_path = "/var/log/qubes/guid.{}.log".format(vm)
        self.vm = vm
        super().__init__(log_file_path)

    def generate_interaction(self, line):
        if "Created 0x" in line:
            self.process_line_create(line)

        elif "XDestroyWindow" in line:
            self.process_line_destroy(line)

    def process_line_create(self, line):
        dom0_window_id = re.search("0x[0-9a-f]+", line).group()
        logging.debug("Created window (id: {})".format(dom0_window_id))

        if not utils.window_viewable(dom0_window_id):
            logging.error("ignoring window {} \
                (not viewable)".format(dom0_window_id))
        #elif "x/y -100/-100" in line:
            # Hidden windows (TODO understand)
            #   these are windows of the whole VM's screen
            #logging.debug("Hidden Window... ignoring (id: {})"\
            #    .format(dom0_window_id))
        else:
            time.sleep(0.1) # give window time to fully setup
            yield CreateWindowInteraction(self.vm, dom0_window_id)

    def process_line_destroy(self, line):
        dom0_window_id = re.search("0x[0-9a-f]+", line).group()
        logging.debug("Destroyed window (id: {})".format(dom0_window_id))

        yield CloseWindowInteraction(self.vm, dom0_window_id)

class AbstractSysLogWatcher(AbstractWatcher):
    """ Reads logs from syslog """

    def __init__(self):
        super().__init__()
        self.journal = systemd.journal.Reader()

    def run(self):
        self.journal.seek_tail()
        while not self.terminate:
            event = self.journal.wait(100)
            if event == systemd.journal.APPEND:
                for entry in self.journal:
                    self.generate_interaction(entry['MESSAGE'])

class QrexecWatcher(AbstractSysLogWatcher):
    """ Reads Qrexec policy log from syslog """

    def __init__(self, scope):
        super().__init__()
        self.journal.add_match(_COMM='qrexec-policy')
        self.scope = scope

        # VM name regex: https://github.com/QubesOS/qubes-core-admin/blob/df6407/qubes/vm/__init__.py#L56
        vm_name_re = "[a-zA-Z][a-zA-Z0-9_-]*"
        policy_re = "[\\.a-zA-Z0-9_-]+"
        qrexec_success_re = "allowed to (?P<target>{})".format(vm_name_re)
        qrexec_fail_re = "(?P<fail_reason>.*)"

        self.qrexec_re = re.compile("(?P<policy>{}): (?P<source>{}) -> [@]?{}: ({}|{})"\
            .format(policy_re, vm_name_re, vm_name_re, qrexec_success_re, qrexec_fail_re))

    def generate_interaction(self, line):
        action = self.qrexec_re.search(line)
        policy = action.group("policy")
        source = action.group("source")
        target = action.group("target")
        fail_reason = action.group("fail_reason")

        if source in self.scope: # only consider in scope actions initiated by vm in scope
            if fail_reason:
                # FIXME the target may be None. Instead replace by the intended target
                logging.info("\n\tdecision: deny\n\tpolicy: {}\n\tsource: {}\n\ttarget: {}".format(policy, source, target))
                yield QrexecPolicyInteraction(False, policy, source, target)
            else:
                logging.info("\n\tdecision: allow\n\tpolicy: {}\n\tsource: {}\n\ttarget: {}".format(policy, source, target))
                yield QrexecPolicyInteraction(True, policy, source, target)
