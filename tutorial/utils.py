import logging
import Xlib
import Xlib.display
import subprocess

def gen_report(q, file="report.md"):
    """ Generates a user activity report """

    interactions = [q.get() for _ in range(q.qsize())]
    logging.info("Generating report...")

    report = ""

    for step_n, interaction in enumerate(interactions):
        print("[{}] {}".format(step_n, interaction.gen_report()))
        int_rep = interaction.gen_report()
        line = "{}. {}\n\n".format(step_n, int_rep[0])
        report += line
        for line in int_rep[1:]:
            report += "    {}\n".format(line)
        report += "\n"

    with open(file,'w') as f:
        f.write(report)

    logging.info("Finished generating report...")

def get_window_title(winid):
    """ Obtains the window title """

    # TODO check if needs sanitization
    winid_int = int(winid, 16) # convert str to hex
    dpy = Xlib.display.Display()
    win = dpy.create_resource_object('window', winid_int)
    atom_id = dpy.intern_atom('WM_NAME')

    # Not well documented process. Solved with the help of
    # https://stackoverflow.com/questions/9465651/how-can-i-read-an-x-property-using-python-xlib
    window_prop = win.get_full_property(atom_id, property_type=0)
    if window_prop:
        untrusted_win_name = window_prop.value  # type: Union[str, bytes]
        if isinstance(untrusted_win_name, bytes):
            # Apparently COMPOUND_TEXT is so arcane that this is how
            # tools like xprop deal with receiving it these days
            untrusted_win_name = untrusted_win_name.decode('latin1', 'replace')
        return untrusted_win_name

    return "<unnamed window>"

def enable_vm_debug(vm):
    """ enables debug mode for VM """

    try:
        command = ["qvm-prefs", "--set", vm, "debug", "True"]
        subprocess.check_output(command)
        logging.debug("enabled debug mode for qube {}".format(vm))
    except subprocess.CalledProcessError:
        logging.error("failed to enable debug mode for qube {}".format(vm))

def disable_vm_debug(vm):
    """ enables debug mode for VM """

    try:
        command = ["qvm-prefs", "--set", vm, "debug", "False"]
        subprocess.check_output(command)
        logging.debug("disabled debug mode for qube {}".format(vm))
    except subprocess.CalledProcessError:
        logging.error("failed to disable debug mode for qube {}".format(vm))

def window_viewable(winid):
    """ Checks if an windows is viewable """

    winid_int = int(winid, 16) # convert str to hex
    dpy = Xlib.display.Display()
    win = dpy.create_resource_object('window', winid_int)
    attr = win.get_attributes()

    if attr.map_state == 0:
        return False
    else:
        return True

def screenshot_window(dom0_window_id="0x0"):
    """
    Saves a screenshot of a particular window id
    """
    logging.debug("saving screenshot of {}".format(dom0_window_id))

    try:

        command = ["xwd", "-id", dom0_window_id]
        xwd_data = subprocess.check_output(command, stderr=None)

        with open("{}.xwd".format(dom0_window_id), 'wb') as f:
                f.write(xwd_data)

        command = ["convert",
                "{}.xwd".format(dom0_window_id),
                "{}.png".format(dom0_window_id)
                ]

        subprocess.check_output(command).decode()

        command = ["rm", "{}.xwd".format(dom0_window_id)]

        subprocess.check_output(command).decode()

    except subprocess.CalledProcessError:
        logging.error("failed to take screenshot of window \
                    {} (probably unimportant)".format(dom0_window_id))

