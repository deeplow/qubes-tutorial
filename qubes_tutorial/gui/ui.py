import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def setup_step_information(title, text, callback):
    dialog = Gtk.MessageDialog(
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(text)
    dialog.run()
    dialog.destroy()
    callback()

modal_dir_path = os.path.dirname(os.path.realpath(__file__))
modal_path = os.path.join(modal_dir_path, "modal.ui")

@Gtk.Template(filename=modal_path)
class ModalWindow(Gtk.Window):
    __gtype_name__ = "ModalWindow"
    modal_placeholder = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def update(self, step_ui_path, title,
                 next_button_label, next_button_callback,
                 back_button_label=None, back_button_callback=None):

        custom_information = Gtk.Builder()
        custom_information.add_from_file(step_ui_path)
        custom_modal = custom_information.get_object("custom_modal")
        self.modal_placeholder.pack_start(custom_modal, True, True, 0)

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
