import argparse
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import dbus.service
import logging
import os
from queue import Queue

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

import qubes_tutorial.gui.ui as ui


class TutorialUI(dbus.service.Object):

    def __init__(self, tutorial_dir):
        self.tutorial_dir = tutorial_dir

        # setup dbus listening to requests for UI changes
        DBusGMainLoop(set_as_default=True)
        ui_bus = dbus.service.BusName("org.qubes.tutorial.ui",
                                            bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, ui_bus, '/')

        # ui update event queue
        self.event_q = Queue()

        # setup user interface
        #self.builder = Gtk.Builder()
        #dir_path = os.path.dirname(os.path.realpath(__file__))
        #ui_path = os.path.join(dir_path, 'tutorial.glade')
        #self.builder.add_from_file(ui_path)
        self.setup_widgets()
        self.connect_signals()

        Gtk.main()

    def send_interaction(self, interaction_str):
        """Configures DBus proxy to communicate with tutorial loop"""

        bus = dbus.SessionBus()
        logging.info("sending interaction")
        proxy = bus.get_object('org.qubes.tutorial.interactions', '/')
        register_interaction_proxy =\
            proxy.get_dbus_method('register_interaction', 'org.qubes.tutorial.interactions')
        register_interaction_proxy(interaction_str)

    def setup_widgets(self):
        self.modal = ui.ModalWindow()
        self.step_info = ui.StepInformation()
        self.widgets = [
            self.modal,
            self.step_info
        ]
        #self.tutorial_info = self.builder.get_object("TutorialInformation")
        #self.tutorial_info_ok_btn = self.builder.get_object('tutorial_info_ok_btn')
        #self.tutorial_modal.show_all()
        #self.tutorial_info.show_all()

    def connect_signals(self):
        # modal_next
        # modal_back
        #self.tutorial_info_ok_btn.connect(
        #    'clicked', self.on_clicked_tutorial_info_ok_btn)
        # task_exit
        return

    #def on_clicked_tutorial_info_ok_btn(self,button):
        #logging.info("Moving to next step")
        #bus = dbus.SessionBus()
        #logging.info("sending interaction")
        #proxy = bus.get_object('org.qubes.tutorial.interactions', '/')
        #register_interaction = proxy.get_dbus_method('register_interaction', 'org.qubes.tutorial.interactions')
        #register_interaction("next_step")


    @dbus.service.method('org.qubes.tutorial.ui')
    def setup_ui(self, ui_dict):
        self.event_q.put(ui_dict)
        GLib.idle_add(self.update_ui)
        return "setup in progress"

    def update_ui(self):
        while not self.event_q.empty():
            event = self.event_q.get()
            self.process_ui_change(event)
        return False

    def process_ui_change(self, ui_dict):
        logging.info("processing some UI change")
        logging.info(ui_dict)

        for widget in self.widgets:
            widget.hide()

        for ui_item_dict in ui_dict:
            ui_type = ui_item_dict['type']
            if ui_type == "modal":
                self.setup_ui_modal(ui_item_dict)
            elif ui_type == "step_information":
                self.setup_ui_step_information(ui_item_dict)
                pass
            else:
                raise Exception("UI of type '{}' not recognized.".format(
                    ui_type))

    def setup_ui_modal(self, ui_item_dict: dict):
        logging.debug("setting up ui modal")

        def on_next_button_pressed():
            # FIXME send interaction "click main button"
            self.send_interaction("click main button")

        def on_back_button_pressed():
            # FIXME send interaction "click secondary button"
            self.send_interaction("click secondary button")

        template = ui_item_dict['template']
        template_path = os.path.join(self.tutorial_dir, template)
        logging.debug(template_path)
        title = ui_item_dict.get('title')
        next_button_label = ui_item_dict.get('next_button')
        back_button_label = ui_item_dict.get('back_button')
        self.modal.update(template_path, title,
                          next_button_label, on_next_button_pressed,
                          back_button_label, on_back_button_pressed)

    def setup_ui_step_information(self, ui_item_dict):
        def on_ok_button_pressed():
            self.send_interaction("click OK")

        title = ui_item_dict.get('title')
        text  = ui_item_dict.get('text')
        has_ok_btn = ui_item_dict.get('has_ok_btn')
        if has_ok_btn == "True":
            self.step_info.update(title, text, on_ok_button_pressed)
        elif has_ok_btn == "False":
            self.step_info.update(title, text)
        else:
            logging.error("unknown value for 'has_ok_btn'")

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

    a = TutorialUI(args.dir)
    logging.info("waiting for interactions...")

if __name__ == "__main__":
    main()
