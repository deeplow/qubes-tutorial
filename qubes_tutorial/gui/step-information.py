import gi

gi.require_version("Gtk", "3.0")
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk
import cairo


class StepIndicator(Gtk.Window):
    def __init__(self, text):
        Gtk.Window.__init__(self)
        self.set_border_width(10)
        self.set_default_size(400, 200)

        self.set_style()

        # making the window transparent
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        # removing all window decorations
        self.set_decorated(False)

        self.create_dummy_boxes()
        self.create_popover(text)

    def create_dummy_boxes(self):
        """ Creates dummy pointable objects at the edges of the window """

        self.dummy_top_left = Gtk.Image.new_from_file("images/alpha_1px.png")
        self.dummy_top_right = Gtk.Image.new_from_file("images/alpha_1px.png")
        self.dummy_bottom_left = Gtk.Image.new_from_file("images/alpha_1px.png")
        self.dummy_bottom_right = Gtk.Image.new_from_file("images/alpha_1px.png")

        dummy_box_top = Gtk.HBox()
        dummy_box_bottom = Gtk.HBox()

        dummy_box_top.pack_start(self.dummy_top_left, False, False, 0)
        dummy_box_top.pack_end(self.dummy_top_right, False, False, 0)
        dummy_box_bottom.pack_start(self.dummy_bottom_left, False, False, 0)
        dummy_box_bottom.pack_end(self.dummy_bottom_right, False, False, 0)

        dummy_box = Gtk.VBox()
        dummy_box.set_name("dummy_box")
        dummy_box.pack_start(dummy_box_top, False, False, 0)
        dummy_box.pack_end(dummy_box_bottom, False, False, 0)

        self.add(dummy_box)

    def create_popover(self, text):
        self.popover = Gtk.Popover.new(self.dummy_top_left)
        vbox = Gtk.VBox()

        popover_text = Gtk.Label(label=text)
        popover_text.set_use_markup(True)
        popover_text.set_name("popover_text")

        popover_subtext = Gtk.Label(label=text)
        popover_subtext.set_use_markup(True)
        popover_subtext.set_name("popover_subtext")

        vbox.pack_start(popover_text, False, True, 0)
        vbox.pack_start(popover_subtext, False, True, 0)
        vbox.show_all()

        self.popover.add(vbox)

        self.popover.popup()
        self.popover.popdown()
        self.popover.popup()

    def set_style(self):
        css = b"""
#dummy_box {
    margin-top:    -12px;
    margin-bottom: -12px;
    margin-right:   20px;
    margin-left:    20px;
}
#popover_text {
    padding: 20px 20px 10px 20px;
    font-weight: bold;
    font-size: 17px;
}
#popover_subtext {
    padding: 0px 20px 20px 20px;
    font-size: 15px;
}
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

win = StepIndicator("Some random text here")
win.show_all()
Gtk.main()
