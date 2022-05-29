import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

@Gtk.Template(filename="modal.ui")
class ModalWindow(Gtk.Window):
    __gtype_name__ = "ModalWindow"
    modal_placeholder = Gtk.Template.Child()

    def __init__(self, step_ui_path):
        super().__init__()

        custom_information = Gtk.Builder()
        custom_information.add_from_file('../' + step_ui_path)
        custom_modal = custom_information.get_object("custom_modal")

        self.modal_placeholder.pack_start(custom_modal, True, True, 0)


window = ModalWindow('included_tutorials/onboarding/step_1.ui')
window.show_all()

Gtk.main()
