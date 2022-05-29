from qubes_tutorial.gui.modal import ModalWindow

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def setup_modal(template_path):
    window = ModalWindow(template_path)
    window.show_all()

    Gtk.main()
