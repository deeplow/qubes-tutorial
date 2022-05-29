from qubes_tutorial.gui.modal import ModalWindow

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def setup_modal(template_path, title,
                next_button_label, next_button_callback,
                back_button_label=None, back_button_callback=None):
    window = ModalWindow(template_path, title,
                         next_button_label, next_button_callback,
                         back_button_label, back_button_callback)
    window.show_all()

    Gtk.main()
