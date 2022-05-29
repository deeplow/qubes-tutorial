import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


@Gtk.Template(filename="modal.ui")
class ModalWindow(Gtk.Window):
    __gtype_name__ = "modalWindow"

window = ModalWindow()
window.show()

Gtk.main()