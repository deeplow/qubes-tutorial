import qubes_tutorial.utils as utils
import yaml

class Interaction():
    """ Defines an iteraction """

    def __init__(self, interaction_type):
        self.type = interaction_type

    def __eq__(self, other):
        return self.type == other.type

    def __hash__(self):
        return self.type.__hash__()

    def gen_report(self):
        return "generic step"

    def dump(self):
        return self.__dict__

class QubeInteraction(Interaction):
    """ Interaction inside one qube """
    def __init__(self, interaction_type, vm):
        self.vm = vm
        super().__init__(interaction_type)

class InterQubeInteraction(Interaction):
    """ Interaction from one qube to another """
    def __init__(self, interaction_type):
        super().__init__(interaction_type)

class CreateWindowInteraction(QubeInteraction):
    """ Window was opened """

    def __init__(self, vm, dom0_window_id):
        super().__init__("create-window", vm)

        self.id = dom0_window_id
        self.title = utils.get_window_title(self.id)

    def gen_report(self):
        return [
                "**[{}]** Window opened \"{}\"".format(self.vm, self.title),
               ]

class CloseWindowInteraction(QubeInteraction):
    """ Window was closed """

    def __init__(self, vm, dom0_window_id):
        super().__init__("close-window", vm)

        self.id = dom0_window_id
        #self.title = utils.get_window_title(self.id)

    def gen_report(self):
        return [
                "**[{}]** Window closed ".format(self.id)
               ]


class QrexecPolicyInteraction(InterQubeInteraction):
    """ Qrexec (inter-qube) was checked against Policy """

    def __init__(self, success, policy, source, target):

        if success:
            super().__init__("qrexec-policy-allow")
        else:
            super().__init__("qrexec-policy-reject")

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


class InteractionException(Exception):
    def __init__(self, message="Exception occured in an interaction."):
        super().__init__(message)
