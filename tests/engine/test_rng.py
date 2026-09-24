import unittest

from engine.rng import roll_d6
from engine.types import RngState


class RngTests(unittest.TestCase):
    def test_same_seed_and_counter_reproduce_die_and_event(self):
        first = roll_d6(RngState(428193, 0), "combat")
        second = roll_d6(RngState(428193, 0), "combat")
        self.assertEqual(first, second)
        self.assertEqual(first[1].draw_count, 1)

    def test_reason_changes_event_but_not_die(self):
        combat = roll_d6(RngState(428193, 0), "combat")
        weather = roll_d6(RngState(428193, 0), "weather")
        self.assertEqual(combat[0], weather[0])
        self.assertNotEqual(combat[2], weather[2])

    def test_first_ten_rolls_match_fixed_sequence(self):
        state = RngState(428193, 0)
        values = []
        for _ in range(10):
            value, state, _ = roll_d6(state, "test")
            values.append(value)
        self.assertEqual(values, [3, 3, 6, 1, 2, 3, 4, 1, 6, 4])
        self.assertEqual(state.draw_count, 10)
