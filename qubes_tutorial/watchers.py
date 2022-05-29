import logging
import sys,os
import time
import re
from queue import Queue
import threading
import systemd.journal

from qubes_tutorial.interactions import *
import qubes_tutorial.utils

watchers = list()
watchers_threads = list()

def init_watchers(scope: list, interactions_q: Queue):
    """ starts log readers and other sensors """
    # start sensors
    # start interactions processor
    logging.info("initializing sensors")


    def _start_watcher(watcher):
        global watchers
        global watchers_threads

        watchers.append(watcher)
        watcher_thread = threading.Thread(target=watcher.run, daemon=True)
        watchers_threads.append(watcher_thread)
        watcher_thread.start()

    # vm-specific logs monitoring
    for vm in scope:
        utils.enable_vm_debug(vm)

        _start_watcher(
            GuidLogWatcher(interactions_q, vm))

    # qrexec monitoring
    _start_watcher(
        QrexecWatcher(interactions_q, scope))

def stop_watchers(scope: list):

    for vm in scope:
        utils.disable_vm_debug(vm)

class AbstractWatcher:
    """ Generic log reader """

    def __init__(self, interactions_q):
        self.interactions_q = interactions_q
        self.terminate = False

    def run(self):
        pass

    def stop(self):
        self.terminate = True

    def process_line(self, line):
        pass

class LogWatcher(AbstractWatcher):
    """ Reads logs from a file """

    log_file = "/dev/null"
    def __init__(self, log_file, interactions_q):
        self.log_file = log_file
        logging.info("Watching log {}".format(self.log_file))

        super().__init__(interactions_q)


    def run(self):
        with open(self.log_file, 'r') as f:
            f.seek(0, os.SEEK_END) # ignore old logs (start from end)
            while not self.terminate:
                line = ''
                while not self.terminate and (len(line) == 0 or line[-1] != '\n'):
                    tail = f.readline()
                    if tail == '':
                        time.sleep(0.01)
                        continue
                    line += tail
                self.process_line(line)

class GuidLogWatcher(LogWatcher):
    """ Reads logs from guid interactions for qube """

    def __init__(self, interactions_q, vm):
        log_file = "/var/log/qubes/guid.{}.log".format(vm)
        self.vm = vm
        super().__init__(log_file, interactions_q)

    def process_line(self, line):
        if "Created 0x" in line:
            self.process_line_create(line)

        elif "XDestroyWindow" in line:
            self.process_line_destroy(line)

    def process_line_create(self, line):
        dom0_window_id = re.search("0x[0-9a-f]+", line).group()
        logging.debug("Created window (id: {})".format(dom0_window_id))

        if "x/y -100/-100" in line:
            # Hidden windows (TODO understand)
            #   these are windows of the whole VM's screen
            pass
        elif not utils.window_viewable(dom0_window_id):
            logging.error("ignoring window {} \
                (not viewable)".format(dom0_window_id))
        else:
            time.sleep(0.1) # give window time to fully setup
            self.interactions_q.put(CreateWindowInteraction(self.vm, dom0_window_id))

    def process_line_destroy(self, line):
        dom0_window_id = re.search("0x[0-9a-f]+", line).group()
        logging.debug("Destroyed window (id: {})".format(dom0_window_id))

        self.interactions_q.put(CloseWindowInteraction(self.vm, dom0_window_id))

class AbstractSysLogWatcher(AbstractWatcher):
    """ Reads logs from syslog """

    def __init__(self, interactions_q):
        super().__init__(interactions_q)
        self.journal = systemd.journal.Reader()

    def run(self):
        self.journal.seek_tail()
        while not self.terminate:
            event = self.journal.wait(100)
            if event == systemd.journal.APPEND:
                for entry in self.journal:
                    self.process_line(entry['MESSAGE'])

class QrexecWatcher(AbstractSysLogWatcher):
    """ Reads Qrexec policy log from syslog """

    def __init__(self, interactions_q, scope):
        super().__init__(interactions_q)
        self.journal.add_match(_COMM='qrexec-policy')
        self.scope = scope

        # VM name regex: https://github.com/QubesOS/qubes-core-admin/blob/df6407/qubes/vm/__init__.py#L56
        vm_name_re = "[a-zA-Z][a-zA-Z0-9_-]*"
        policy_re = "[\\.a-zA-Z0-9_-]+"
        qrexec_success_re = "allowed to (?P<target>{})".format(vm_name_re)
        qrexec_fail_re = "(?P<fail_reason>.*)"

        self.qrexec_re = re.compile("(?P<policy>{}): (?P<source>{}) -> [@]?{}: ({}|{})"\
            .format(policy_re, vm_name_re, vm_name_re, qrexec_success_re, qrexec_fail_re))

    def process_line(self, line):
        action = self.qrexec_re.search(line)
        policy = action.group("policy")
        source = action.group("source")
        target = action.group("target")
        fail_reason = action.group("fail_reason")

        if source in self.scope: # only consider in scope actions initiated by vm in scope
            if fail_reason:
                # FIXME the target may be None. Instead replace by the intended target
                logging.info("\n\tdecision: deny\n\tpolicy: {}\n\tsource: {}\n\ttarget: {}".format(policy, source, target))
                self.interactions_q.put(QrexecPolicyInteraction(False, policy, source, target))
            else:
                logging.info("\n\tdecision: allow\n\tpolicy: {}\n\tsource: {}\n\ttarget: {}".format(policy, source, target))
                self.interactions_q.put(QrexecPolicyInteraction(True, policy, source, target))
