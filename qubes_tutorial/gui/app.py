import argparse
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import dbus.service
import logging
import os
import enum
from queue import Queue
import pkg_resources

import gi
gi.require_version("Gtk", "3.0")
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

import cairo

import qubes_tutorial.interactions as interactions

ui_dir = os.path.dirname(os.path.realpath(__file__))

class TutorialUIDbusService(dbus.service.Object):

    def __init__(self, tutorial_dir):
        self.tutorial_dir = tutorial_dir

        # setup dbus listening to requests for UI changes
        DBusGMainLoop(set_as_default=True)
        ui_bus = dbus.service.BusName("org.qubes.tutorial.ui",
                                            bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, ui_bus, '/')

        # ui update event queue
        self.event_q = Queue()

        self.setup_styling()
        self.setup_widgets()

        Gtk.main()

    def setup_styling(self):
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_path(pkg_resources.resource_filename(
            __name__, 'tutorial-styling.css'))
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def setup_widgets(self):
        self.modal = ModalWindow()
        self.step_info = StepInformation()
        self.step_info_pointing = StepInformationPointing()
        self.current_task = CurrentTaskInfo()

        self.enabled_widgets = []

    @dbus.service.method('org.qubes.tutorial.ui')
    def set_num_tasks(self, num_tasks):
        self.current_task.set_num_tasks(num_tasks)

    @dbus.service.method('org.qubes.tutorial.ui')
    def setup_ui(self, ui_dict):
        self.event_q.put(ui_dict)
        GLib.idle_add(self.update_ui)
        return "setup in progress"

    @dbus.service.method('org.qubes.tutorial.ui')
    def teardown_ui(self):
        logging.info("processing UI teardown")
        for widget in self.enabled_widgets:
            if widget == self.current_task:
                # current task is always on-screen
                continue
            widget.teardown()
            widget.hide()
            self.enabled_widgets.remove(widget)
        return "completed UI teardown"

    def update_ui(self):
        while not self.event_q.empty():
            event = self.event_q.get()
            self.process_ui_change(event)
        return False

    def process_ui_change(self, ui_dict):
        logging.info("processing some UI change")
        logging.info(ui_dict)
        new_task = False

        for ui_item_dict in ui_dict:
            ui_type = ui_item_dict['type']
            if ui_type == "modal":
                self.setup_ui_modal(ui_item_dict)
                self.enabled_widgets += [self.modal]
            elif ui_type == "step_information":
                self.setup_ui_step_information(ui_item_dict)
                self.enabled_widgets += [self.step_info]
            elif ui_type == "step_information_pointing":
                self.setup_ui_step_information_pointing(ui_item_dict)
                self.enabled_widgets += [self.step_info_pointing]
            elif ui_type == "new_task":
                new_task = True
                self.setup_ui_current_task(ui_item_dict)
                self.enabled_widgets += [self.current_task]
            elif ui_type == "no_more_tasks":
                self.current_task.teardown()
                self.current_task.hide()
            elif ui_type == "none":
                self.enabled_widgets = []
            else:
                raise Exception("UI of type '{}' not recognized.".format(
                    ui_type))

        if not new_task:
            self.current_task.move_to_corner()

    def setup_ui_modal(self, ui_item_dict: dict):
        logging.debug("setting up ui modal")

        def on_next_button_pressed():
            interactions.register("tutorial:next")

        def on_back_button_pressed():
            interactions.register("tutorial:back")

        template = ui_item_dict['template']
        template_path = os.path.join(self.tutorial_dir, template)
        logging.debug(template_path)
        title = ui_item_dict.get('title')
        next_button_label = ui_item_dict.get('next_button')
        back_button_label = ui_item_dict.get('back_button')
        backdrop_enabled_str = ui_item_dict.get('backdrop_enabled', "False")
        backdrop_enabled = backdrop_enabled_str == "True"
        self.modal.update(template_path, title,
                          next_button_label, on_next_button_pressed,
                          back_button_label, on_back_button_pressed,
                          backdrop_enabled)

    def setup_ui_step_information(self, ui_item_dict):
        def on_ok_button_pressed():
            interactions.register("tutorial:next")

        title = ui_item_dict.get('title')
        text  = ui_item_dict.get('text')
        align_vertical = ui_item_dict.get('align_vertical', 'center')
        align_horizontal = ui_item_dict.get('align_horizontal', 'center')
        has_ok_btn = ui_item_dict.get('has_ok_btn')
        if has_ok_btn == "True":
            self.step_info.update(title, text, align_horizontal, align_vertical,
                                  on_ok_button_pressed)
        elif has_ok_btn == "False":
            self.step_info.update(title, text, align_horizontal, align_vertical)
        else:
            logging.error("unknown value for 'has_ok_btn'")

    def setup_ui_step_information_pointing(self, ui_item_dict):
        title = ui_item_dict.get('title')
        text  = ui_item_dict.get('text')
        x = int(ui_item_dict.get('x_coord'))
        y = int(ui_item_dict.get('y_coord'))
        corner = ui_item_dict.get('point_to_corner')
        self.step_info_pointing.update(title, text, x, y, corner)

    def setup_ui_current_task(self, ui_item_dict):
        """Informs the user of the current task

        Has two UI elements. When shown the first time, it shows centered on
        screen the goal of the current task. When the user has acknowledged,
        it will show on the bottom-right corner as a reminder.
        """
        task_description  = ui_item_dict.get('task_description', "")

        def on_ok():
            interactions.register("tutorial:next")

        def on_exit():
            interactions.register("tutorial:exit")

        self.current_task.update(task_description, on_ok, on_exit)


class TutorialUIInterface:
    """
    Methods required by any Tutorial UI element
    """

    def update(self, *args, **kwargs):
        """
        Updating the widget's contents
        """
        pass

    def teardown(self):
        """
        What needs to be run when the widget is no longer being displayed
        """
        pass

class TutorialWindow(Gtk.Window, TutorialUIInterface):

    def __init__(self):
        super().__init__()
        self.set_keep_above(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)

        primary_monitor = self.get_screen().get_display().get_primary_monitor()
        self.screen_width = primary_monitor.get_geometry().width
        self.screen_height = primary_monitor.get_geometry().height

    def make_widget_transparent(self, widget):
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            widget.set_visual(visual)
        widget.set_app_paintable(True)

    def move_to_center(self):
        self.set_gravity(Gdk.Gravity.SOUTH_EAST)
        (widget_width, widget_height) = self.get_size()
        self.move(self.screen_width/2 - widget_width/2, self.screen_height/2 - widget_height/2)


@Gtk.Template(filename=os.path.join(ui_dir, "current_task.ui"))
class CurrentTaskInfo(TutorialWindow):
    """Current Task Information

    Shows the user information of the current task they're performing.

    Has the following lifecycle
        1. starts hidden (since no task has been given to the user yet)
        2. show front and center "OK" dialog box with the current task
        3. once "OK" pressed, it moves to bottom-right muted with an extra
         button to exit the tutorial
    """

    __gtype_name__ = "CurrentTaskInfo"
    button = Gtk.Template.Child()
    title = Gtk.Template.Child()
    text = Gtk.Template.Child()

    STATE_CENTER = enum.auto()
    STATE_CORNER = enum.auto()

    def __init__(self):
        super().__init__()
        self.connect_signals()
        self.state = self.STATE_CENTER
        self.task_num = 0
        self.num_tasks = 0

    def connect_signals(self):
        self.button.connect('clicked', self.on_btn_pressed)

    def update(self, text, ok_callback, exit_callback):
        self.text.set_label(text)
        self.task_num = self.task_num + 1
        self.title.set_label(f"Task {self.task_num}")

        # becomes foreground when it is updated
        self.move_to_center()
        self.show_all()
        self.set_keep_above(True)
        self.button.set_label("OK")
        self.button.get_style_context().add_class("blue_button")

        self.ok_callback = ok_callback
        self.exit_callback = exit_callback

        # FIXME add "(last one)" when it's the last
        # FIXME add "X of Y" so users can keep track of progress

    def set_num_tasks(self, num_tasks):
        self.num_tasks = num_tasks

    def move_to_center(self):
        self.state = self.STATE_CENTER
        super().move_to_center()

    def move_to_corner(self):
        """
        Moves the current task information to the corner so that the user can
        always glance down to see the task description or exit the tutorial
        """
        self.state = self.STATE_CORNER
        self.title.set_label(f"Task {self.task_num} of {self.num_tasks}")
        self.button.get_style_context().remove_class("blue_button")
        self.button.set_label("exit tutorial")
        self.set_gravity(Gdk.Gravity.SOUTH_EAST)
        (widget_width, widget_height) = self.get_size()
        self.move(self.screen_width  - widget_width,
                  self.screen_height - widget_height)

    def on_btn_pressed(self, button):
        if self.state == self.STATE_CORNER:
            self.exit_callback()
        else:
            self.move_to_corner()
            self.ok_callback()


@Gtk.Template(filename=os.path.join(ui_dir, "step_information.ui"))
class StepInformation(TutorialWindow):
    __gtype_name__ = "StepInformation"
    ok_btn = Gtk.Template.Child()
    title = Gtk.Template.Child()
    text = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.connect_signals()

    def connect_signals(self):
        self.ok_btn.connect('clicked', self.on_ok_btn_pressed)

    def update(self, title, text,
               align_horizontal="center", align_vertical="center",
               ok_button_pressed_callback=None):
        self.title.set_label(title)
        self.text.set_label(text)
        self.show_all()

        if ok_button_pressed_callback is None:
            self.ok_btn.hide()
        else:
            self.ok_button_pressed_callback = ok_button_pressed_callback

        self.align_vertical(align_horizontal, align_vertical)

    def on_ok_btn_pressed(self, button):
        self.ok_button_pressed_callback()

    def align_vertical(self, align_horizontal, align_vertical):
        self.set_gravity(Gdk.Gravity.NORTH_EAST)
        (widget_width, widget_height) = self.get_size()
        x = None
        y = None

        if "%" in align_horizontal:
            percent = int(align_horizontal.strip('%'))
            x = (percent/100) * self.screen_width - widget_width/2
        else:
            if align_horizontal == "left":
                x = self.screen_width/4 - widget_width/2
            elif align_horizontal == "center":
                x = self.screen_width/2 - widget_width/2
            elif align_horizontal == "right":
                x = 3*self.screen_width/4 - widget_width/2

        if "%" in align_vertical:
            percent = int(align_vertical.strip('%'))
            y = (percent/100) * self.screen_width - widget_height/2
        else:
            if align_vertical == "top":
                y = self.screen_height/4 - widget_height/2
            elif align_vertical == "center":
                y = self.screen_height/2 - widget_height/2
            elif align_vertical == "bottom":
                y = 3*self.screen_height/4 - widget_height/2

        if x is None:
            raise Exception("x must be either a percentage (e.g. 20%) or 'left',"\
                            "'center' or 'right'")
        if y is None:
            raise Exception("y must be either a percentage or 'top',"\
                            "'center' or 'bottom'")
        self.move(x, y)


class StepInformationPointing(TutorialWindow):
    """
    Indicates information about the current step, but instead of having to be
    acknowledged by the user via an "OK" button, it directly points to
    a coordinate on the screen.
    """
    def __init__(self):
        super().__init__()
        self.set_border_width(10)
        self.make_widget_transparent(self)
        self._create_dummy_boxes()

    def update(self, text, subtext, x, y, corner):
        self._create_popover(text, subtext)
        self.show_all()
        # Functions that require widget to be already rendered
        self._position_on_screen(x, y, corner)
        self._make_clickthrough()

    def teardown(self):
        # NOTE: popdown to make there isn't an invisible popup preventing the
        # user from clicking anywehere else on the tutorial UI
        self.popover.popdown()

    def _position_on_screen(self, x, y, corner):
        """
        Positions popover arrow over specified point on the screen. Then
        points to the corner.

        NOTE: Only works after widget.show_all()
        """
        win_width  = 500
        win_height = 200
        self.resize(win_width, win_height)
        target = None

        if x < 0:
            x = self.screen_width + x
        if y < 0:
            y = self.screen_height + y

        if corner == "top right":
            target = self.dummy_top_right
            self.move(x - win_width, y)
        elif corner == "top left":
            target = self.dummy_top_left
            self.move(x, y)
        else:
            raise Exception("corner must be one of 'top left' or 'top right'")
        self.popover.set_relative_to(target)

    def _create_dummy_boxes(self):
        """ Creates dummy pointable objects at the edges of the window """
        image = os.path.join(ui_dir, "images", "alpha_1px.png")

        self.dummy_top_left = Gtk.Image.new_from_file(image)
        self.dummy_top_right = Gtk.Image.new_from_file(image)
        self.dummy_bottom_left = Gtk.Image.new_from_file(image)
        self.dummy_bottom_right = Gtk.Image.new_from_file(image)

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

    def _create_popover(self, text, subtext):
        self.popover = Gtk.Popover.new(self.dummy_top_left)
        vbox = Gtk.VBox()

        self.popover_text = Gtk.Label()
        self.popover_text.set_use_markup(True)
        self.popover_text.set_name("popover_text")

        self.popover_subtext = Gtk.Label()
        self.popover_subtext.set_use_markup(True)
        self.popover_subtext.set_name("popover_subtext")

        vbox.pack_start(self.popover_text, False, True, 0)
        vbox.pack_start(self.popover_subtext, False, True, 0)
        vbox.show_all()

        self.popover.add(vbox)
        self.popover_text.set_text(text)
        self.popover_subtext.set_text(subtext)
        self.popover.popup()

    def _make_clickthrough(self):
        """ Make window clickthrough

        Only works after widget.show_all()
        """
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0 , 0)
        surface_ctx = cairo.Context(surface)
        region = Gdk.cairo_region_create_from_surface(surface)
        self.input_shape_combine_region(region)


@Gtk.Template(filename=os.path.join(ui_dir, "modal.ui"))
class ModalWindow(TutorialWindow):
    __gtype_name__ = "ModalWindow"
    modal_placeholder = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.custom_modal = None
        self.create_backdrop()
        self.connect_signals()

    def connect_signals(self):
        self.next_button.connect('clicked', self.on_next_button_pressed)
        self.back_button.connect('clicked', self.on_back_button_pressed)

    def create_backdrop(self):
        """
        Darkens the screen behind the modal window
        """
        self.backdrop = Gtk.Window()

        # enable compositing so it can be translucent
        self.make_widget_transparent(self.backdrop)

        self.backdrop.fullscreen()

        drawingarea = Gtk.DrawingArea()
        self.backdrop.add(drawingarea)
        drawingarea.connect('draw', self.backdrop_draw)
        drawingarea.set_opacity(0.4)
        self.set_transient_for(self.backdrop)
        self.set_modal(True)

    def backdrop_draw(self, drawing_area, ctx):
        rect = ctx.rectangle(0, 0, self.screen_width, self.screen_height)
        ctx.set_source_rgb(0, 0, 0)
        ctx.fill()

    def update(self, step_ui_path, title,
                 next_button_label, next_button_callback,
                 back_button_label=None, back_button_callback=None,
                 backdrop_enabled=False):

        custom_information = Gtk.Builder()
        custom_information.add_from_file(step_ui_path)

        if self.custom_modal:
            previous_ui = self.custom_modal
            self.modal_placeholder.remove(previous_ui)

        self.custom_modal = custom_information.get_object("custom_modal")
        self.modal_placeholder.pack_start(self.custom_modal, True, True, 0)

        self.title_label.set_label(title)
        self.next_button.set_label(next_button_label)
        self.next_button_callback = next_button_callback
        self.back_button.set_label(back_button_label)
        self.back_button_callback = back_button_callback
        self.move_to_center()
        if backdrop_enabled:
            self.backdrop.show_all()
        self.show_all()
        if back_button_label:
            self.back_button.set_visible(True)
        else:
            self.back_button.set_visible(False)

    def on_next_button_pressed(self, button):
        self.next_button_callback()
        self.backdrop.hide()

    def on_back_button_pressed(self, button):
        self.back_button_callback()
        self.backdrop.hide()

def main():
    log_fmt = "%(module)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    parser = argparse.ArgumentParser(
            description='User interface for Qubes Tutorial')

    parser.add_argument('--dir',
                        type=str,
                        required=True,
                        metavar="PATH",
                        help='Location of tutorial directory')

    args = parser.parse_args()

    a = TutorialUIDbusService(args.dir)
    logging.info("waiting for interactions...")

if __name__ == "__main__":
    main()
