import argparse
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import dbus.service
import logging
import os
import enum
from queue import Queue
import pkg_resources

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import qubes_tutorial.interactions as interactions

ui_dir = os.path.dirname(os.path.realpath(__file__))

class TutorialUIDbusService(dbus.service.Object):

    def __init__(self, tutorial_dir):
        self.tutorial_dir = tutorial_dir

        # setup dbus listening to requests for UI changes
        DBusGMainLoop(set_as_default=True)
        ui_bus = dbus.service.BusName("org.qubes.tutorial.ui",
                                            bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, ui_bus, '/')

        # ui update event queue
        self.event_q = Queue()

        self.setup_styling()
        self.setup_widgets()

        Gtk.main()

    def setup_styling(self):
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_path(pkg_resources.resource_filename(
            __name__, 'tutorial-styling.css'))
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def setup_widgets(self):
        self.modal = ModalWindow()
        self.step_info = StepInformation()
        self.current_task = CurrentTaskInfo()

        self.hideable_widgets = [
            self.modal,
            self.step_info
        ]

    @dbus.service.method('org.qubes.tutorial.ui')
    def setup_ui(self, ui_dict):
        self.event_q.put(ui_dict)
        GLib.idle_add(self.update_ui)
        return "setup in progress"

    def update_ui(self):
        while not self.event_q.empty():
            event = self.event_q.get()
            self.process_ui_change(event)
        return False

    def process_ui_change(self, ui_dict):
        logging.info("processing some UI change")
        logging.info(ui_dict)

        for widget in self.hideable_widgets:
            widget.hide()

        for ui_item_dict in ui_dict:
            ui_type = ui_item_dict['type']
            if ui_type == "modal":
                self.setup_ui_modal(ui_item_dict)
            elif ui_type == "step_information":
                self.setup_ui_step_information(ui_item_dict)
            elif ui_type == "current_task":
                self.setup_ui_current_task(ui_item_dict)
            elif ui_type == "none":
                pass
            else:
                raise Exception("UI of type '{}' not recognized.".format(
                    ui_type))


    def setup_ui_modal(self, ui_item_dict: dict):
        logging.debug("setting up ui modal")

        def on_next_button_pressed():
            interactions.register("tutorial:next")

        def on_back_button_pressed():
            interactions.register("tutorial:back")

        template = ui_item_dict['template']
        template_path = os.path.join(self.tutorial_dir, template)
        logging.debug(template_path)
        title = ui_item_dict.get('title')
        next_button_label = ui_item_dict.get('next_button')
        back_button_label = ui_item_dict.get('back_button')
        self.modal.update(template_path, title,
                          next_button_label, on_next_button_pressed,
                          back_button_label, on_back_button_pressed)

    def setup_ui_step_information(self, ui_item_dict):
        def on_ok_button_pressed():
            interactions.register("tutorial:next")

        title = ui_item_dict.get('title')
        text  = ui_item_dict.get('text')
        has_ok_btn = ui_item_dict.get('has_ok_btn')
        if has_ok_btn == "True":
            self.step_info.update(title, text, on_ok_button_pressed)
        elif has_ok_btn == "False":
            self.step_info.update(title, text)
        else:
            logging.error("unknown value for 'has_ok_btn'")

    def setup_ui_current_task(self, ui_item_dict):
        """Informs the user of the current task

        Has two UI elements. When shown the first time, it shows centered on
        screen the goal of the current task. When the user has acknowledged,
        it will show on the bottom-right corner as a reminder.
        """
        task_number  = int(ui_item_dict.get('task_number'))
        task_description  = ui_item_dict.get('task_description')

        def on_ok():
            interactions.register("tutorial:next")

        def on_exit():
            interactions.register("tutorial:exit")

        self.current_task.update(task_number, task_description, on_ok, on_exit)


@Gtk.Template(filename=os.path.join(ui_dir, "current_task.ui"))
class CurrentTaskInfo(Gtk.Dialog):
    """Current Task Information

    Shows the user information of the current task they're performing.

    Has the following lifecycle
        1. starts hidden (since no task has been given to the user yet)
        2. show front and center "OK" dialog box with the current task
        3. once "OK" pressed, it moves to bottom-right muted with an extra
         button to exit the tutorial
    """

    __gtype_name__ = "CurrentTaskInfo"
    ok_btn = Gtk.Template.Child()
    exit_btn = Gtk.Template.Child()
    title = Gtk.Template.Child()
    text = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.set_keep_above(True)
        self.hide() # starts hidden

    def update(self, task_n, text, ok_callback, exit_callback):
        # becomes foreground when it is updated
        self.title.set_label("Task {}".format(task_n))
        self.text.set_label(text)

        self.move_to_center()
        self.show_all()
        self.exit_btn.hide()

        self.ok_callback = ok_callback
        self.exit_callback = exit_callback

        # FIXME add "(last one)" when it's the last
        # FIXME add "X of Y" so users can keep track of progress

    def move_to_corner(self):
        self.set_gravity(Gdk.Gravity.SOUTH_EAST)
        (widget_width, widget_height) = self.get_size()
        screen_width    = self.get_screen().width()
        screen_height = self.get_screen().height()
        self.move( screen_width - widget_width, screen_height - widget_height)

    def move_to_center(self):
        self.set_gravity(Gdk.Gravity.SOUTH_EAST)
        (widget_width, widget_height) = self.get_size()
        screen_width    = self.get_screen().width()
        screen_height = self.get_screen().height()
        self.move(screen_width/2 - widget_width/2, screen_height/2 - widget_height/2)

    @Gtk.Template.Callback()
    def on_ok_btn_pressed(self, button):
        self.ok_btn.hide()
        self.exit_btn.show()

        self.move_to_corner()

        self.ok_callback()

    @Gtk.Template.Callback()
    def on_exit(self, button):
        self.exit_callback()


@Gtk.Template(filename=os.path.join(ui_dir, "step_information.ui"))
class StepInformation(Gtk.Dialog):
    __gtype_name__ = "StepInformation"
    ok_btn = Gtk.Template.Child()
    title = Gtk.Template.Child()
    text = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.set_keep_above(True)

    def update(self, title, text, ok_button_pressed_callback=None):
        self.title.set_label(title)
        self.text.set_label(text)
        self.show_all()

        if ok_button_pressed_callback is None:
            self.ok_btn.hide()
        else:
            self.ok_button_pressed_callback = ok_button_pressed_callback

    @Gtk.Template.Callback()
    def on_ok_btn_pressed(self, button):
        self.ok_button_pressed_callback()

@Gtk.Template(filename=os.path.join(ui_dir, "modal.ui"))
class ModalWindow(Gtk.Window):
    __gtype_name__ = "ModalWindow"
    modal_placeholder = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.custom_modal = None
        self.set_keep_above(True)
        self.set_decorated(False)

    def update(self, step_ui_path, title,
                 next_button_label, next_button_callback,
                 back_button_label=None, back_button_callback=None):

        custom_information = Gtk.Builder()
        custom_information.add_from_file(step_ui_path)

        if self.custom_modal:
            previous_ui = self.custom_modal
            self.modal_placeholder.remove(previous_ui)

        self.custom_modal = custom_information.get_object("custom_modal")
        self.modal_placeholder.pack_start(self.custom_modal, True, True, 0)

        self.title_label.set_label(title)
        self.next_button.set_label(next_button_label)
        self.next_button_callback = next_button_callback
        self.back_button.set_label(back_button_label)
        self.back_button_callback = back_button_callback
        self.move_to_center()
        self.show_all()

    def move_to_center(self):
        self.set_gravity(Gdk.Gravity.SOUTH_EAST)
        (widget_width, widget_height) = self.get_size()
        screen_width  = self.get_screen().width()
        screen_height = self.get_screen().height()
        self.move(screen_width/2 - widget_width/2, screen_height/2 - widget_height/2)

    @Gtk.Template.Callback()
    def on_next_button_pressed(self, button):
        self.next_button_callback()

    @Gtk.Template.Callback()
    def on_back_button_pressed(self, button):
        self.back_button_callback()


def main():
    log_fmt = "%(module)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    parser = argparse.ArgumentParser(
            description='User interface for Qubes Tutorial')

    parser.add_argument('--dir',
                        type=str,
                        required=True,
                        metavar="PATH",
                        help='Location of tutorial directory')

    args = parser.parse_args()

    a = TutorialUIDbusService(args.dir)
    logging.info("waiting for interactions...")

if __name__ == "__main__":
    main()
