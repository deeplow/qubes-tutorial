import unittest
import qubes_tutorial.tutorial as tutorial

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