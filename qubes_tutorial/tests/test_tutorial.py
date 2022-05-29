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

    def test_start_tutorial_linear(self):
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

    def test_start_tutorial_linear_next_step_every_2_interactions(self):
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

