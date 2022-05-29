import os
import enum
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

ui_dir = os.path.dirname(os.path.realpath(__file__))

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
        screen_width    = self.get_screen().width()
        screen_height = self.get_screen().height()
        self.move(screen_width/2 - widget_width/2, screen_height/2 - widget_height/2)

    @Gtk.Template.Callback()
    def on_next_button_pressed(self, button):
        self.next_button_callback()

    @Gtk.Template.Callback()
    def on_back_button_pressed(self, button):
        self.back_button_callback()
