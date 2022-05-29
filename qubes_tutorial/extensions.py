import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import inspect

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import qubes_tutorial.interactions as interactions

tutorial_enabled = False

def if_tutorial_enabled(func):
    """
    Function decorator that runs the function only if a tutorial is running
    """
    def decorator(*args, **kwargs):
        if tutorial_enabled:
            return func(*args, **kwargs)
    return decorator

def tutorial_register_decorator(interaction_name):
    """
    If the tutorial mode is enabled, it informs the tutorial of these calls
    """
    def tutorial_register_decorator(func):
        def wrapper(*args):
            func(*args)
            tutorial_register(interaction_name)
        return wrapper
    return tutorial_register_decorator

@if_tutorial_enabled
def tutorial_register(name: str, subject: str="", arguments: str=""):
    if tutorial_enabled:
        interactions.register(name, subject, arguments)

class TutorialExtension(dbus.service.Object):
    """
    External component that interacts with the tutorial.

    Usage:
      methods starting by "do_" will be endpoints for receiving messages from
      the tutorial.
    """

    __bus_name__ =  "org.qubes.tutorial.extensions"

    @classmethod
    def make_do_methods_dbus_services(cls):
        """
        Marks all methods starting with "do_" as dbus service methods
        """
        for name, member in inspect.getmembers(cls):
            if (inspect.ismethod(member) or inspect.isfunction(member))\
                and name.startswith('do_'):
                setattr(cls, name, dbus.service.method(cls.__bus_name__)(member))
        return cls

    def __init__(self, component_name):
        # FIXME find better way than globals
        global tutorial_enabled
        tutorial_enabled = True

        DBusGMainLoop(set_as_default=True)
        self.make_do_methods_dbus_services()
        bus = dbus.service.BusName(self.__bus_name__, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus, f'/{component_name}')