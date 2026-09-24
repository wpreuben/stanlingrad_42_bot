import unittest
from dataclasses import FrozenInstanceError

from engine.types import GameState, Phase, RngState, Side, UnitState


class StateTests(unittest.TestCase):
    def test_external_unit_mapping_change_does_not_change_state(self):
        units = {"axis-2a-hq": UnitState("axis-2a-hq", "1300", 1, ())}
        state = GameState("v2025_04", "fall_blau", 1, Phase.INITIAL,
                          Side.AXIS, "clear_weather", units, {}, RngState(7, 0), None, ())
        units.clear()
        self.assertIn("axis-2a-hq", state.units)
        with self.assertRaises(TypeError):
            state.units["axis-2a-hq"] = UnitState("axis-2a-hq", "1301", 1, ())

    def test_unit_fields_cannot_be_reassigned(self):
        unit = UnitState("axis-2a-hq", "1300", 1, ())
        with self.assertRaises(FrozenInstanceError):
            unit.location = "1301"
