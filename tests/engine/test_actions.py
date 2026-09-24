import unittest
from dataclasses import replace

from engine.actions import EndPhaseAction
from engine.catalog import Catalog, ScenarioDef
from engine.engine import Engine
from engine.errors import CatalogError, InvalidActionError, UnsupportedRuleError
from engine.types import GameState, Phase, RngState, Side


class ActionTests(unittest.TestCase):
    def setUp(self):
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8, ())
        self.engine = Engine(Catalog("v2025_04", {}, {}, {"fall_blau": scenario}))

    def test_s1_starts_in_axis_initial_phase(self):
        state = self.engine.new_game("fall_blau")
        self.assertEqual((state.turn, state.phase, state.active_side, state.weather),
                         (1, Phase.INITIAL, Side.AXIS, "clear_weather"))
        with self.assertRaises(UnsupportedRuleError):
            self.engine.get_legal_actions(state)

    def test_unknown_scenario_is_rejected(self):
        with self.assertRaises(CatalogError):
            self.engine.new_game("unknown")

    def test_clear_weather_phase_can_advance_without_mutating_input(self):
        state = replace(self.engine.new_game("fall_blau"), phase=Phase.WEATHER, active_side=Side.NONE)
        self.assertEqual(self.engine.get_legal_actions(state), [EndPhaseAction(Side.NONE)])
        next_state = self.engine.apply_action(state, EndPhaseAction(Side.NONE))
        self.assertEqual((next_state.phase, next_state.active_side), (Phase.INITIAL, Side.AXIS))
        self.assertEqual((state.phase, state.active_side), (Phase.WEATHER, Side.NONE))
        self.assertEqual(next_state.events[-1].kind, "phase_ended")

    def test_wrong_side_is_rejected_before_rule_gate(self):
        state = self.engine.new_game("fall_blau")
        with self.assertRaises(InvalidActionError):
            self.engine.apply_action(state, EndPhaseAction(Side.SOVIET))

    def test_pending_decision_cannot_be_skipped(self):
        state = replace(self.engine.new_game("fall_blau"), phase=Phase.WEATHER,
                        active_side=Side.NONE, pending_decision="choose")
        with self.assertRaises(InvalidActionError):
            self.engine.apply_action(state, EndPhaseAction(Side.NONE))
