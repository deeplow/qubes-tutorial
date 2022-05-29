# Onboarding tutorial
#
# Note: In the future this should be implemented as a static file / folder.

from qubes_tutorial.tutorial import Tutorial, Step
from qubes_tutorial.interactions import Interaction

class OnboardingTutorial(Tutorial):

    def __init__(self):
        super().__init__()
