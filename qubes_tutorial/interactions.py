import qubes_tutorial.utils as utils

import logging
import yaml
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

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
    def register_interaction(self,
                             name: str,
                             subject: str,
                             arguments: str):
        logging.info("Registered interaction:\n\t-{}\n\t-{}\n\t-{}".format(
            name, subject, arguments))

        # must empy str instead of none since D-Bus doesn't support it
        if subject == "":
            self.interactions_q.put("{}".format(name))
        elif arguments == "":
            self.interactions_q.put("{}:{}".format(name, subject))
        else:
            self.interactions_q.put("{}:{}:{}".format(name, subject, arguments))

def register(name: str, subject: str="", arguments: str=""):
    """
    Registers an interaction on the tutorial
    """
    bus = dbus.SessionBus()
    logging.info("sending interaction")
    proxy = bus.get_object('org.qubes.tutorial.interactions', '/',
                           # introspect disabled since when combined with
                           # method call with "ignore_reply" parameter
                           # there is a bug where it simply does not send it
                           introspect=False)
    register_interaction_proxy =\
        proxy.get_dbus_method('register_interaction',
                              'org.qubes.tutorial.interactions')

    # "ignore_reply" to avoid deadlocks between simulatenously listenning and
    # emmiting dbus components
    register_interaction_proxy(name, subject, arguments, ignore_reply=True)

class Interaction():
    """ Defines an iteraction """

    def __init__(self, interaction_type):
        self.type = interaction_type

    def __eq__(self, other):
        return self.type == other.type

    def __hash__(self):
        return self.type.__hash__()

    def gen_report(self):
        return "generic step"

    def dump(self):
        return self.__dict__

class QubeInteraction(Interaction):
    """ Interaction inside one qube """
    def __init__(self, interaction_type, vm):
        self.vm = vm
        super().__init__(interaction_type)

class InterQubeInteraction(Interaction):
    """ Interaction from one qube to another """
    def __init__(self, interaction_type):
        super().__init__(interaction_type)

class CreateWindowInteraction(QubeInteraction):
    """ Window was opened """

    def __init__(self, vm, dom0_window_id):
        super().__init__("create-window", vm)

        self.id = dom0_window_id
        self.title = utils.get_window_title(self.id)

    def gen_report(self):
        return [
                "**[{}]** Window opened \"{}\"".format(self.vm, self.title),
               ]

class CloseWindowInteraction(QubeInteraction):
    """ Window was closed """

    def __init__(self, vm, dom0_window_id):
        super().__init__("close-window", vm)

        self.id = dom0_window_id
        #self.title = utils.get_window_title(self.id)

    def gen_report(self):
        return [
                "**[{}]** Window closed ".format(self.id)
               ]


class QrexecPolicyInteraction(InterQubeInteraction):
    """ Qrexec (inter-qube) was checked against Policy """

    def __init__(self, success, policy, source, target):

        if success:
            super().__init__("qrexec-policy-allow")
        else:
            super().__init__("qrexec-policy-reject")

        self.success = success
        self.policy = policy
        self.source = source
        self.target = target

    def gen_report(self):
        # TODO consider when policy is successfull but the execussion itself fails
        # e.g.: qubes.FileCopy but target already has file w/ same name
        action = '"{}" ({} -> {})'.format(self.policy, self.source, self.target)
        if self.success:
            return ["Inter-qube action: " + action]
        else:
            return ["Rejected inter-qube action: " + action]


class InteractionException(Exception):
    def __init__(self, message="Exception occured in an interaction."):
        super().__init__(message)
