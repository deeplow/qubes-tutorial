import unittest
import qubes_tutorial.tutorial as tutorial
from mock import Mock

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
