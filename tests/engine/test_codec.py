import json
import unittest
from dataclasses import replace

from engine.actions import EndPhaseAction
from engine.catalog import Catalog, HexDef, ScenarioDef, UnitDef, UnitFace
from engine.codec import deserialize_state, hash_state, serialize_state
from engine.errors import InvalidActionError, StateFormatError
from engine.actions import deserialize_action, serialize_action
from engine.rng import roll_d6
from engine.types import Event, GameState, Phase, RngState, Side, UnitState


class CodecTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog("v2025_04", {
            "a": HexDef("a", "clear", {}, (), {}, "fixture:hex"),
            "b": HexDef("b", "clear", {}, (), {}, "fixture:hex"),
        }, {
            "u": UnitDef("u", Side.AXIS, "infantry", "U", (UnitFace(1, 2, 3, 4, ()),), "fixture:unit")
        }, {
            "fall_blau": ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8, ())
        })
        self.state = GameState("v2025_04", "fall_blau", 1, Phase.INITIAL,
                               Side.AXIS, "clear_weather", {"u": UnitState("u", "a", 1, ())},
                               {"marker": "a"}, RngState(428193, 2), None,
                               (Event("die_roll", (("reason", "test"), ("value", "3"))),),
                               control={"a": "axis"}, supply={"u": "supplied"},
                               resources={"axis": 2}, reinforcements={"axis": ("u",)},
                               victory_points={"axis": 1}, private_state={"secret": "box-a"})

    def test_state_json_round_trip_preserves_all_dynamic_fields(self):
        data = serialize_state(self.state)
        restored = deserialize_state(json.loads(json.dumps(data)), self.catalog)
        self.assertEqual(restored, self.state)
        self.assertEqual(data["schema_version"], 1)

    def test_hash_excludes_events_but_includes_rng_and_locations(self):
        original = hash_state(self.state)
        self.assertEqual(original, hash_state(replace(self.state, events=())))
        self.assertNotEqual(original, hash_state(replace(self.state, rng=RngState(428193, 3))))
        moved = replace(self.state, units={"u": UnitState("u", "b", 1, ())})
        self.assertNotEqual(original, hash_state(moved))

    def test_future_schema_unknown_unit_and_bad_rng_are_rejected(self):
        for field, value in (("schema_version", 2), ("rng", {"seed": 1, "draw_count": -1})):
            with self.subTest(field=field):
                data = serialize_state(self.state)
                data[field] = value
                with self.assertRaises(StateFormatError):
                    deserialize_state(data, self.catalog)
        data = serialize_state(self.state)
        data["units"]["missing"] = data["units"].pop("u")
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)

    def test_missing_field_and_boolean_integer_are_rejected(self):
        data = serialize_state(self.state)
        del data["ruleset_id"]
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)
        data = serialize_state(self.state)
        data["turn"] = True
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)

    def test_action_round_trip_and_unknown_tag(self):
        action = EndPhaseAction(Side.AXIS)
        self.assertEqual(deserialize_action(serialize_action(action)), action)
        with self.assertRaises(InvalidActionError):
            deserialize_action({"schema_version": 1, "type": "move", "side": "axis"})

    def test_rng_continues_identically_after_save_and_restore(self):
        _, first_rng, first_event = roll_d6(RngState(428193, 0), "weather")
        progressed = replace(self.state, rng=first_rng, events=(first_event,))
        restored = deserialize_state(json.loads(json.dumps(serialize_state(progressed))), self.catalog)
        self.assertEqual(roll_d6(progressed.rng, "combat"),
                         roll_d6(restored.rng, "combat"))

    def test_unknown_fields_and_mismatched_ruleset_are_rejected(self):
        data = serialize_state(self.state)
        data["surprise"] = 1
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)

    def test_unknown_reinforcement_and_control_hex_are_rejected(self):
        data = serialize_state(self.state)
        data["reinforcements"]["axis"] = ["missing"]
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)
        data = serialize_state(self.state)
        data["control"]["missing"] = "axis"
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)
        data = serialize_state(self.state)
        data["ruleset_id"] = "future"
        with self.assertRaises(StateFormatError):
            deserialize_state(data, self.catalog)
