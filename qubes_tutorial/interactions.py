import qubes_tutorial.utils

class Interaction:
    """ Defines an iteraction """

    def __init__(self):
        pass

    def gen_report(self):
        return "generic step"

class QubeInteraction(Interaction):
    """ Interaction inside one qube """
    def __init__(self, vm):
        self.vm = vm
        super().__init__()

class InterQubeInteraction(Interaction):
    """ Interaction from one qube to another """
    pass

class CreateWindowInteraction(QubeInteraction):
    """ Window was opened """

    def __init__(self, vm, dom0_window_id):
        super().__init__(vm)

        self.id = dom0_window_id
        utils.screenshot_window(self.id)
        self.title = utils.get_window_title(self.id)

    def gen_report(self):
        return [
                "**[{}]** Window opened \"{}\"".format(self.vm, self.title),
                "![]({}.png)".format(self.id)
               ]

class CloseWindowInteraction(QubeInteraction):
    """ Window was closed """

    def __init__(self, vm, dom0_window_id):
        super().__init__(vm)

        self.id = dom0_window_id
        #self.title = utils.get_window_title(self.id)

    def gen_report(self):
        return [
                "**[{}]** Window closed ".format(self.id)
               ]


class QrexecPolicyInteraction(InterQubeInteraction):
    """ Qrexec (inter-qube) was checked against Policy """

    def __init__(self, success, policy, source, target):
        self.success = success
        self.policy = policy
        self.source = source
        self.target = target

    def gen_report(self):
        # TODO consider when policy is successfull but the execussion itself fails
        # e.g.: qubes.FileCopy but target already has file w/ same name
        action = '"{}" ({} -> {})'.format(self.policy, self.source, self.target)
        if self.success:
            return ["Inter-qube action: " + action]
        else:
            return ["Rejected inter-qube action: " + action]

