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

    def __init__(self, step_ui_path):
        super().__init__()

        custom_information = Gtk.Builder()
        custom_information.add_from_file(step_ui_path)
        custom_modal = custom_information.get_object("custom_modal")

        self.modal_placeholder.pack_start(custom_modal, True, True, 0)
