import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

modal_dir_path = os.path.dirname(os.path.realpath(__file__))
modal_path = os.path.join(modal_dir_path, "modal.ui")

@Gtk.Template(filename=modal_path)
class ModalWindow(Gtk.Window):
    __gtype_name__ = "ModalWindow"
    modal_placeholder = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def __init__(self, step_ui_path, next_button_label, back_button_label=None):
        super().__init__()

        custom_information = Gtk.Builder()
        custom_information.add_from_file(step_ui_path)
        custom_modal = custom_information.get_object("custom_modal")
        self.modal_placeholder.pack_start(custom_modal, True, True, 0)

        if back_button_label is None:
            self.back_button.set_label("") # FIXME make invisible
        else:
            self.back_button.set_label("<u>{}</u>".format(back_button_label))
        self.next_button.set_label(next_button_label)
