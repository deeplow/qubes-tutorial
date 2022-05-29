import threading
import argparse
import logging
import os
import time

# typing imports
from queue import Queue

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, GLib

from qubes_tutorial.tutorial import Tutorial
import qubes_tutorial.gui.ui as ui

def app_main(tutorial_path, tutorial=None):
    #win = Gtk.Window(default_height=50, default_width=300)
    #win.connect("destroy", Gtk.main_quit)
    #modal_window = ui.ModalWindow()
    #modal_window.show()

    def setup_ui_modal(ui_item_dict: dict):
        print("displaying step UI\n\t" + str(ui_item_dict))
        #if True:
        #    tutorial.handle_interaction("click main button")
        #    return
        def on_next_button_pressed():
            modal_window.close()
            tutorial.handle_interaction("click main button")

        def on_back_button_pressed():
            modal_window.close()
            tutorial.handle_interaction("click secondary button")


        template = ui_item_dict['template']
        template_path = os.path.join(tutorial.tutorial_dir, template)
        title = ui_item_dict.get('title')
        next_button_label = ui_item_dict.get('next_button')
        back_button_label = ui_item_dict.get('back_button')
        window = ui.ModalWindow()
        modal_window.setup(template_path, title,
                    next_button_label, on_next_button_pressed,
                    back_button_label, on_back_button_pressed)
        modal_window.show_all()
        Gtk.main()
        print("skdsajdsakdjskd")


    def setup_ui(ui_dict, interactions_q):
        print("calling setup")
        #for i in range(10):
            #ui_item_dict = {'type': 'modal', 'title': '', 'template': 'custom_ui/step_1.ui', 'next_button': str(i), 'back_button': 'Skip tutorial,\ndo later'}
            #GLib.idle_add(setup_ui_modal, ui_item_dict)
            #time.sleep(0.2)

        for ui_item_dict in ui_dict:
            ui_type = ui_item_dict['type']

            if ui_type == "modal":
                # FIXME make thread-safe with events
                #self.idle_add(self.setup_ui_modal, data=ui_item_dict)
                GLib.idle_add(setup_ui_modal, ui_item_dict, priority=GLib.PRIORITY_HIGH_IDLE)
                #self.setup_ui_modal(ui_item_dict)
            elif ui_type == "step_information":
                #self._setup_ui_step_information(ui_item_dict, interactions_q)
                pass
            else:
                raise Exception("UI of type '{}' not recognized.".format(
                    ui_type))

    tutorial = Tutorial(ui_setup_callback=setup_ui)
    tutorial.load_as_file(tutorial_path)
    threading.Thread(target=tutorial.start).start()




class TutorialApp(Gtk.Application):

    def __init__(self, tutorial_path, tutorial=None):
        super().__init__()
        self.set_application_id("org.qubes.qui.Tutorial")

        self.tutorial = Tutorial(ui_setup_callback=self.setup_ui)
        self.tutorial.load_as_file(tutorial_path)

    def do_interaction(self, arg):
        print("method handler for `interaction' called with argument", arg)

    def do_activate(self):
        print("do activate")
        threading.Thread(target=self.tutorial.start).start()

    def setup_ui(self, ui_dict, interactions_q):
        for ui_item_dict in ui_dict:
            ui_type = ui_item_dict['type']
            if ui_type == "modal":
                # FIXME make thread-safe with events
                help(TutorialApp)
                #self.idle_add(self.setup_ui_modal, data=ui_item_dict)
                GLib.idle_add(self.setup_ui_modal, data=ui_item_dict)
                #self.setup_ui_modal(ui_item_dict)
            elif ui_type == "step_information":
                #self._setup_ui_step_information(ui_item_dict, interactions_q)
                pass
            else:
                raise Exception("UI of type '{}' not recognized.".format(
                    ui_type))

    def setup_ui_modal(self, ui_item_dict: dict):
        print("YOOOOOLLLLO1!!")

        """
        ## IGNORE ABOVE
        def on_next_button_pressed():
            self.tutorial.interactions_q.put(
                Interaction("click main button"))

        def on_back_button_pressed():
            self.tutorial.interactions_q.put(
                Interaction("click secondary button"))

        template = ui_item_dict['template']
        template_path = os.path.join(self.tutorial.tutorial_dir, template)
        title = ui_item_dict.get('title')
        next_button_label = ui_item_dict.get('next_button')
        back_button_label = ui_item_dict.get('back_button')
        window = ui.ModalWindow(template_path, title,
                    next_button_label, on_next_button_pressed,
                    back_button_label, on_back_button_pressed)
        window.present()
        """

    def _setup_ui_step_information(self, ui_item_dict, interactions_q):

        def on_ok_button_pressed():
            interactions_q.put(Interaction("click OK"))

        title = ui_item_dict.get('title')
        text  = ui_item_dict.get('text')
        ui.setup_step_information(title, text, on_ok_button_pressed)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(
            description='Integrated tutorials tool for Qubes OS')

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--create', '-c',
                        type=argparse.FileType('w', encoding='UTF-8'),
                        metavar="FILE",
                        help='Create a tutorial')

    action_group.add_argument('--load', '-l',
                        type=str,
                        metavar="FILE",
                        help='Load a tutorial from a .yaml or literate .md.'\
                            + "\nFor example 'qubes_tutorial/included_tutorials/onboarding-tutorial-1/README.md'")

    parser.add_argument('--scope', '-s',
                        type=str,
                        help='qubes affected (e.g. --scope=personal,work)')

    args = parser.parse_args()

    scope = list()
    if args.scope:
        scope = [x.strip() for x in args.scope.split(",")]

    if args.create:
        create_tutorial(args.create, scope)
    elif args.load:
        #app = TutorialApp(tutorial_path=args.load)
        #app.run()
        app_main(tutorial_path=args.load)

if __name__ == "__main__":
    main()
