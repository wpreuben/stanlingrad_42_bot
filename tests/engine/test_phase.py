import unittest

from engine.errors import InvalidActionError
from engine.phase import next_phase
from engine.types import Phase, Side


class PhaseTests(unittest.TestCase):
    def test_rule_3_turn_order(self):
        turn, phase, side = 1, Phase.WEATHER, Side.NONE
        actual = []
        for _ in range(12):
            turn, phase, side = next_phase(turn, phase, side)
            actual.append((turn, phase, side))
        self.assertEqual(actual, [
            (1, Phase.INITIAL, Side.AXIS),
            (1, Phase.MOVEMENT, Side.AXIS),
            (1, Phase.COMBAT, Side.AXIS),
            (1, Phase.RECOVERY, Side.AXIS),
            (1, Phase.SUPPLY, Side.AXIS),
            (1, Phase.INITIAL, Side.SOVIET),
            (1, Phase.MOVEMENT, Side.SOVIET),
            (1, Phase.COMBAT, Side.SOVIET),
            (1, Phase.RECOVERY, Side.SOVIET),
            (1, Phase.SUPPLY, Side.SOVIET),
            (1, Phase.VICTORY, Side.NONE),
            (2, Phase.WEATHER, Side.NONE),
        ])

    def test_invalid_phase_side_pair_is_rejected(self):
        with self.assertRaises(InvalidActionError):
            next_phase(1, Phase.COMBAT, Side.NONE)
