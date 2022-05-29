import unittest
import qubes_tutorial.tutorial as tutorial
import qubes_tutorial.interactions as interactions
from unittest.mock import Mock

class TestTutorial(unittest.TestCase):

    def setUp(self):
        self.tutorial = tutorial.Tutorial()

    def test_add_step(self):
        step = tutorial.Step("step1")
        self.tutorial.add_step(step)

        self.assertEqual(
            self.tutorial.get_step("step1"),
            step)

    def test_add_step_twice(self):
        step = tutorial.Step("step1")

        self.tutorial.add_step(step)
        self.assertRaises(tutorial.TutorialDuplicateStepException,
                          self.tutorial.add_step, step)

    def test_add_transition(self):
        step1 = tutorial.Step("step1")
        step2 = tutorial.Step("step2")
        interaction = Mock()

        step1.add_transition(interaction, step2)

        next_step = step1.next(interaction)
        self.assertEqual(next_step, step2)

    def test_add_duplicate_transition(self):
        step1 = tutorial.Step("step1")
        step2 = tutorial.Step("step2")
        step3 = tutorial.Step("step3")
        interaction = Mock()

        step1.add_transition(interaction, step2)
        self.assertRaises(tutorial.TutorialDuplicateTransitionException,
                          step1.add_transition, interaction, step3)

    def test_ignored_transition(self):
        step = tutorial.Step("step1")
        interaction = Mock()
        ignored_interaction = Mock()

        step.add_transition(interaction, "step2")

        next_step = step.next(ignored_interaction)
        self.assertIsNone(next_step)

class TestTutorialSerialization(unittest.TestCase):

    def test_save(self):
        result = """\
steps:
- name: start
  transitions:
  - type: sample-interaction
  - policy: qubes.FileCopy
    source: work
    success: true
    target: personal
    type: qrexec-policy-allow
- name: middle
- name: end
"""

        tut = tutorial.Tutorial()
        step_start  = tutorial.Step("start")
        step_middle = tutorial.Step("middle")
        step_end    = tutorial.Step("end")

        tut.add_step(step_start)
        tut.add_step(step_middle)
        tut.add_step(step_end)

        interact1 = interactions.Interaction("sample-interaction")
        interact2 = interactions.QrexecPolicyInteraction(True, \
            "qubes.FileCopy", "work", "personal")

        step_start.add_transition(interact1, step_middle)
        step_start.add_transition(interact2, step_end)

        self.assertEqual(tut.save_as_text(), result)

