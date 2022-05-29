import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

ui_dir = os.path.dirname(os.path.realpath(__file__))

@Gtk.Template(filename=os.path.join(ui_dir, "step_information.ui"))
class StepInformation(Gtk.Dialog):
    __gtype_name__ = "StepInformation"
    ok_btn = Gtk.Template.Child()
    title = Gtk.Template.Child()
    text = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

    def update(self, title, text, ok_button_pressed_callback):
        self.ok_button_pressed_callback = ok_button_pressed_callback
        print(self.title)
        print(self.text)
        self.title.set_label(title)
        self.text.set_label(text)

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

    @Gtk.Template.Callback()
    def on_next_button_pressed(self, button):
        self.next_button_callback()

    @Gtk.Template.Callback()
    def on_back_button_pressed(self, button):
        self.back_button_callback()
