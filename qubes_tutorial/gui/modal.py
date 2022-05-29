import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

@Gtk.Template(filename='welcome_page.ui')
class CustomModal(Gtk.Box):

    __gtype_name__ = 'CustomModal'

    button_ok_text = GObject.Property(type=str, default="Next")

    def __init__(self):
        super().__init__()


@Gtk.Template(filename="modal.ui")
class ModalWindow(Gtk.Window):
    __gtype_name__ = "ModalWindow"

    _custom_modal = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self._custom_modal.props.button_ok_text = "Continue »"
        print("button_ok_text:", self._custom_modal.props.button_ok_text)


window = ModalWindow()
window.show()

Gtk.main()