import logging
import re
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

    # FIXME SANITIZE
    untrusted_wininfo = subprocess.check_output(
        'xwininfo -id {}'.format(winid),
        shell=True)

    # FIXME add "<unnamed window>" case
    return re.search('"([^"]+)', str(untrusted_wininfo)).group(1)

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

    untrusted_wininfo = subprocess.check_output(
        'xwininfo -id {}'.format(winid),
        shell=True)

    return "Map State: IsViewable" in str(untrusted_wininfo)
