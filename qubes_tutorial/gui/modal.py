import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

modal_builder = Gtk.Builder()
modal_builder.add_from_file("modal.ui")

window = modal_builder.get_object("modal_window")

custom_information = Gtk.Builder()
custom_information.add_from_file('../included_tutorials/onboarding/step_1.ui')
custom_modal = custom_information.get_object("custom_modal")

placeholder = modal_builder.get_object("modal_placeholder")
placeholder.pack_start(custom_modal, True, True, 0)

window.show_all()

Gtk.main()