import unittest
from dataclasses import replace

from engine import get_result, is_terminal, new_game
from engine.actions import EndPhaseAction
from engine.catalog import Catalog, ScenarioDef
from engine.engine import Engine
from engine.errors import CatalogError, UnsupportedRuleError
from engine.types import GameResult, Phase, Side


class FoundationAcceptanceTests(unittest.TestCase):
    def test_public_api_refuses_s1_until_reference_data_exist(self):
        with self.assertRaises(CatalogError):
            new_game("fall_blau")

    def test_fixture_s1_initial_phase_cannot_be_skipped(self):
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8, ())
        engine = Engine(Catalog("v2025_04", {}, {}, {"fall_blau": scenario}))
        state = engine.new_game("fall_blau")
        with self.assertRaises(UnsupportedRuleError):
            engine.apply_action(state, EndPhaseAction(Side.AXIS))
        self.assertFalse(is_terminal(state))
        self.assertEqual(get_result(state), GameResult.ONGOING)

    def test_fixture_weather_phase_advances_without_mutation(self):
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8, ())
        engine = Engine(Catalog("v2025_04", {}, {}, {"fall_blau": scenario}))
        state = replace(engine.new_game("fall_blau"), phase=Phase.WEATHER, active_side=Side.NONE)
        next_state = engine.apply_action(state, EndPhaseAction(Side.NONE))
        self.assertEqual((state.phase, next_state.phase), (Phase.WEATHER, Phase.INITIAL))
