from qubes_tutorial.gui.modal import ModalWindow

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def setup_modal(template_path, title, next_button_label, back_button_label=None):
    window = ModalWindow(template_path, title, next_button_label, back_button_label)
    window.show_all()

    Gtk.main()
