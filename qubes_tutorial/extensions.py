import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import inspect

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

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

def get_extension_method(component, method_name):
    bus_name       = TutorialExtension.get_bus_name_from_component_name(component)
    interface_name = TutorialExtension.get_interface_name()
    object_path    = TutorialExtension.get_object_path()
    proxy = dbus.SessionBus()\
                .get_object(bus_name, object_path)\
                .get_dbus_method(method_name, interface_name)
    return proxy


class TutorialExtension(dbus.service.Object):
    """
    External component that interacts with the tutorial.

    Usage:
      methods starting by "do_" will be endpoints for receiving messages from
      the tutorial.
    """

    __bus_name__    = "org.qubes.tutorial.extensions"
    __object_path__ = "/"

    @classmethod
    def get_bus_name_from_component_name(cls, component_name):
        return f"{cls.__bus_name__}.{component_name}"

    @classmethod
    def get_interface_name(cls):
        return cls.__bus_name__

    @classmethod
    def get_object_path(cls):
        return cls.__object_path__

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

        bus_name = self.get_bus_name_from_component_name(component_name)
        bus = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus, self.get_object_path())


class GtkTutorialExtension(TutorialExtension):

    HIGHLIGHT_CSS = b"""
    @keyframes animated-highlight {
    from { box-shadow: inset 0px 0px 4px  @theme_selected_bg_color; }
    to   { box-shadow: inset 0px 0px 10px @theme_selected_bg_color; }
    }

    .highlighted {
    animation: animated-highlight 1s infinite alternate;
    }
    """

    def __init__(self, component_name):
        super().__init__(component_name)
        self._add_highlight_style()

    def _add_highlight_style(self):
        screen = Gdk.Screen.get_default()
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(self.HIGHLIGHT_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

def widget_highlight(widget):
    widget.get_style_context().add_class("highlighted")

def widget_highlight_remove(widget):
    widget.get_style_context().remove_class("highlighted")

