import unittest
import qubes_tutorial.tutorial as tutorial
import qubes_tutorial.interactions as interactions
from unittest.mock import Mock
import os
import re
from queue import Queue

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

class TestTutorial(unittest.TestCase):

    def setUp(self):
        self.tutorial = tutorial.Tutorial()

    def test_001_add_step(self):
        step = tutorial.Step("step1")
        self.tutorial.add_step(step)

        self.assertEqual(
            self.tutorial.get_step("step1"),
            step)

    def test_002_add_step_twice(self):
        step = tutorial.Step("step1")

        self.tutorial.add_step(step)
        self.assertRaises(tutorial.TutorialDuplicateStepException,
                          self.tutorial.add_step, step)

    def test_010_add_transition(self):
        step1 = tutorial.Step("step1")
        step2 = tutorial.Step("step2")
        interaction = Mock()

        step1.add_transition(interaction, step2)

        next_step = step1.next(interaction)
        self.assertEqual(next_step, step2)

    def test__011_add_duplicate_transition(self):
        step1 = tutorial.Step("step1")
        step2 = tutorial.Step("step2")
        step3 = tutorial.Step("step3")
        interaction = Mock()

        step1.add_transition(interaction, step2)
        self.assertRaises(tutorial.TutorialDuplicateTransitionException,
                          step1.add_transition, interaction, step3)

    def test_012_ignored_transition(self):
        step = tutorial.Step("step1")
        interaction = Mock()
        ignored_interaction = Mock()

        step.add_transition(interaction, "step2")

        next_step = step.next(ignored_interaction)
        self.assertIsNone(next_step)

    def test_050_start_tutorial_linear(self):
        """All interactions move to the next step

            step-1 ----> step-2 ----> ... ----> step-n
                    (1)          (2)       (3)
        """

        # GIVEN a tutorial where all interaction move to the next step
        num_steps = 10
        tut = Mock()
        interactions_list = [] # builder for interactions_q
        previous_step = None
        last_step = None

        for step_n in range(1, num_steps+1):
            step = tutorial.Step("step-{}".format(step_n))

            if step_n == 1:
                tut.get_first_step = Mock(return_value=step)
            else:
                interaction = Mock()
                interactions_list.append(interaction)
                previous_step.add_transition(interaction, step)

            if step_n == num_steps:
                step.is_last = Mock(return_value=True)
                last_step = step
            else:
                step.is_last = Mock(return_value=False)

            previous_step = step

        interactions_q = Mock()
        interactions_q.get = Mock()
        interactions_q.get.side_effect = interactions_list

        # WHEN the tutorial is ran
        tutorial.start_tutorial(tut, interactions_q)

        # THEN went through same n. of interactions as the best-case scenario
        self.assertEqual(interactions_q.get.call_count, num_steps-1)

        # THEN reached last step
        self.assertEqual(last_step.is_last.call_count, 1)

    def test_051_start_tutorial_linear_next_step_every_2_interactions(self):
            """Every second interaction moves to the next step

              step-1 -----> step-2 --> ... --> step-n
               |   ^  (2)   |   ^
               |(1)|        |(3)|
               +---+        +---+
              """

            # GIVEN a tutorial where every second interaction is useful
            num_steps = 10
            tut = Mock()
            interactions_list = [] # builder for interactions_q
            previous_step = None
            last_step = None

            for step_n in range(1, num_steps+1):
                step = tutorial.Step("step-{}".format(step_n))

                if step_n == 1:
                    tut.get_first_step = Mock(return_value=step)
                    first_step = step
                else:
                    interaction_real = Mock()
                    interactions_list.append(interaction_real)
                    previous_step.add_transition(interaction_real, step)

                if step_n == num_steps:
                    step.is_last = Mock(return_value=True)
                    last_step = step
                else:
                    step.is_last = Mock(return_value=False)

                previous_step = step
                interaction_fake = Mock()
                interactions_list.append(interaction_fake)

            interactions_q = Mock()
            interactions_q.get = Mock()
            interactions_q.get.side_effect = interactions_list

            # WHEN running tutorial
            tutorial.start_tutorial(tut, interactions_q)

            # THEN went through more interactions than best-case scenario
            self.assertGreater(interactions_q.get.call_count,
                               num_steps-1)

            # THEN went through less interactions than worst-case scenario
            self.assertLess(interactions_q.get.call_count,
                            len(interactions_list))

            # THEN reached last step
            self.assertEqual(last_step.is_last.call_count, 1)


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


class TestTutorialDeserialization(unittest.TestCase):

    def setUp(self):
        self.tut = tutorial.Tutorial()

    @property
    def test_name(self):
        method_full_name = self.id()
        return re.match(".*(test_.*)", method_full_name).group(1)

    def get_test_data_path(self, test_name, extension):
        cwd = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(cwd, "test_tutorial_data",
                            "{}.{}".format(test_name, extension))

    def load_test_data(self, test_name, extension):
        """
        Loads test data from file located in:
          - test_tutorial_data/[test_XXX_name].md or .yaml
        """
        test_data_path = self.get_test_data_path(test_name, extension)
        if os.path.exists(test_data_path):
            with open(test_data_path, 'r') as f:
                return f.read()
        raise Exception("Could not find file test data file at \"{}\""\
                            .format(test_data_path))

    def test_001_load_from_yaml_simple(self):
        test_data = self.load_test_data(self.test_name, "yaml")
        self.tut.load_as_yaml(test_data)

    def test_002_load_from_yaml_simple_file(self):
        test_data_path = self.get_test_data_path(self.test_name, "yaml")
        self.tut.load_as_file(test_data_path)


class TestTutorialIncluded(unittest.TestCase):

    def _load_tutorial(self, file_path):
        """
        Loads tutorial from a path relative to the tests directory
        """
        cwd = os.path.dirname(os.path.realpath(__file__))
        tut_path = os.path.join(cwd, file_path)
        tut_path = os.path.abspath(tut_path)
        tut = tutorial.TutorialDebuggable()
        tut.load_as_file(tut_path)
        return tut

    def test_onboarding_tutorial_1(self):
        tut = self._load_tutorial(
            "../included_tutorials/onboarding-tutorial-1/README.md",
        )
        for i, interactions in enumerate(tut.generate_successful_interaction_sequences()):
            logging.info("interaction path " + str(i))
            interactions_q = Queue()
            for interaction in interactions:
                interactions_q.put(interaction)
            tut.start(interactions_q)
