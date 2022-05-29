import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import inspect

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

import qubes_tutorial.interactions as interactions


EXT_INTERFACE_NAME = "org.qubes.tutorial.extensions"
EXT_OBJ_PATH = "/"

tutorial_enabled = False

def if_tutorial_enabled(func):
    """
    Function decorator that runs the function only if a tutorial is running
    """
    def decorator(*args, **kwargs):
        if tutorial_enabled:
            return func(*args, **kwargs)
    return decorator

def register(interaction_name):
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
    """
    Obtains a proxy method for calling a tutorial command in the component
    """
    bus_name       = _get_bus_name_from_component_name(component)
    interface_name = EXT_INTERFACE_NAME
    object_path    = EXT_OBJ_PATH
    proxy = dbus.SessionBus()\
                .get_object(bus_name, object_path)\
                .get_dbus_method(method_name, interface_name)
    return proxy

def enable_extension(component_name):
    enable_extension_proxy = \
        get_extension_method(component_name, "enable_tutorial")
    enable_extension_proxy()

def disable_extension(component_name):
    disable_extension_proxy = \
        get_extension_method(component_name, "disable_tutorial")
    disable_extension_proxy()

def _get_bus_name_from_component_name(component_name):
    return f"{EXT_INTERFACE_NAME}.{component_name}"


class TutorialExtension(dbus.service.Object):
    """
    External component that interacts with the tutorial.

    Usage:
      methods starting by "do_" will be endpoints for receiving messages from
      the tutorial.
    """

    @classmethod
    def make_do_methods_dbus_services(cls):
        """
        Marks all methods starting with "do_" as dbus service methods
        """
        for name, member in inspect.getmembers(cls):
            if (inspect.ismethod(member) or inspect.isfunction(member))\
                and name.startswith('do_'):
                setattr(cls, name, dbus.service.method(EXT_INTERFACE_NAME)(member))
        return cls

    def __init__(self, component_name):
        self.component_name = component_name
        self.start_dbus_service()
        self.do_methods_as_dbus_services = False

    def start_dbus_service(self):
        DBusGMainLoop(set_as_default=True)
        bus_name = _get_bus_name_from_component_name(self.component_name)
        bus = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus, EXT_OBJ_PATH)

    @dbus.service.method(EXT_INTERFACE_NAME)
    def enable_tutorial(self):
        # FIXME find better way than globals
        global tutorial_enabled
        tutorial_enabled = True
        if not self.do_methods_as_dbus_services:
            self.do_methods_as_dbus_services = True
            self.make_do_methods_dbus_services()

    @dbus.service.method(EXT_INTERFACE_NAME)
    def disable_tutorial(self):
        global tutorial_enabled
        tutorial_enabled = False
        self.cleanup()
        # TODO find way to remove do_* dbus methods
        # using self.remove_from_connection() doesn't solve it since it woul
        # also remove the

    def cleanup(self):
        """
        Abstract method to add functions to remove the tutorial
        modifications to the component
        """
        pass


class GtkTutorialExtension(TutorialExtension):

    HIGHLIGHT_CSS = b"""
    @keyframes animated-highlight {
    from { box-shadow: inset 0px 0px 4px  @theme_selected_bg_color; }
    to   { box-shadow: inset 0px 0px 10px @theme_selected_bg_color; }
    }

    @keyframes animated-highlight-wrong {
    from { box-shadow: inset 0px 0px 4px  #f44933; }
    to   { box-shadow: inset 0px 0px 10px #f44933; }
    }

    .highlighted {
    animation: animated-highlight 1s infinite alternate;
    }
    .highlighted-wrong {
    animation: animated-highlight-wrong 1s infinite alternate;
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

def widget_highlight_wrong(widget):
    widget.get_style_context().add_class("highlighted-wrong")

def widget_highlight_remove(widget):
    widget.get_style_context().remove_class("highlighted")
    widget.get_style_context().remove_class("highlighted-wrong")

