import gi

gi.require_version("Gtk", "3.0")
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk
import cairo


class StepIndicator(Gtk.Window):
    def __init__(self, text, x, y):
        Gtk.Window.__init__(self)
        self.set_border_width(10)

        self._set_style()

        # making the window transparent
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        # removing all window decorations
        self.set_decorated(False)

        self._create_dummy_boxes()
        self._create_popover(text)

        self.show_all()

        # Functions that require widget to be already rendered
        self._position_on_screen(x, y)
        self._make_clickthrough()

    def _position_on_screen(self, x, y):
        """ Positions popover arrow over specified point on the screen

        Only works after widget.show_all()
        """
        window = self.get_window()
        window.fullscreen()

        # select the corner to which the popover is pointing
        primary_monitor = self.get_screen().get_display().get_primary_monitor()
        height = primary_monitor.get_geometry().height
        width  = primary_monitor.get_geometry().width
        shifted_x = x - width  / 2
        shifted_y = y - height / 2
        target = None

        if shifted_x >= 0:
            if shifted_y <= 0:  # 1st quadrant
                target = self.dummy_top_right
            else:               # 4th quadrant
                target = self.dummy_bottom_right
        else:
            if shifted_y <= 0:  # 2nd quadrant
                target = self.dummy_top_left
            else:               # 3rd quadrant
                target = self.dummy_bottom_left

        self.popover.set_relative_to(target)

        # TODO adjust window size
        # TODO move window to correct location
        # self.move(x, y)

    def _create_dummy_boxes(self):
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

    def _create_popover(self, text):
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

    def _set_style(self):
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

    def _make_clickthrough(self):
        """ Make window clickthrough

        Only works after widget.show_all()
        """

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0 , 0)
        surface_ctx = cairo.Context(surface)
        region = Gdk.cairo_region_create_from_surface(surface)
        self.input_shape_combine_region(region)


win = StepIndicator("Some random text here", 0, 0)

Gtk.main()
