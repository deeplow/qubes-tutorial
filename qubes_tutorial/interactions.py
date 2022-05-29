import logging
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
