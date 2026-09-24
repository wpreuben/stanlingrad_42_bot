import json
import tempfile
import unittest
from pathlib import Path

from engine.catalog import Catalog, HexDef, Placement, ScenarioDef, UnitDef, UnitFace, load_catalog, validate_catalog
from engine.errors import CatalogError
from engine.engine import Engine
from engine.types import Phase, Side


def hex_def(hex_id, neighbors=None, source_ref="fixture:hex"):
    return HexDef(hex_id, "clear", neighbors or {}, (), {}, source_ref)


class CatalogTests(unittest.TestCase):
    def test_loader_rejects_missing_map_instead_of_returning_empty_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sources.json").write_text(
                '{"schema_version":1,"ruleset_id":"v2025_04","sources":[]}', encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_catalog(root)

    def test_loader_rejects_empty_data_sets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for filename, key in (("map_a.json", "hexes"),
                                  ("units_s1.json", "units"),
                                  ("fall_blau.json", "scenarios")):
                (root / filename).write_text(json.dumps({"schema_version": 1,
                    "ruleset_id": "v2025_04", key: []}), encoding="utf-8")
            (root / "sources.json").write_text(json.dumps({"schema_version": 1,
                "ruleset_id": "v2025_04", "sources": []}), encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_catalog(root)

    def test_loader_preserves_hq_start_face_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            common = {"schema_version": 1, "ruleset_id": "v2025_04"}
            records = {
                "sources.json": {**common, "sources": []},
                "map_a.json": {**common, "hexes": [{"id": "1300", "terrain": "clear",
                    "neighbors": {}, "features": [], "edge_features": {}, "source_ref": "fixture:map"}]},
                "units_s1.json": {**common, "units": [{"id": "hq", "side": "axis",
                    "term_id": "army_hq", "printed_label": "2A HQ", "source_ref": "fixture:counter",
                    "faces": [{"steps": 1, "attack": None, "defense": 1, "movement": 5,
                               "abilities": [], "state": "ready"},
                              {"steps": 1, "attack": 0, "defense": 1, "movement": 5,
                               "abilities": [], "state": "used"}]}]},
                "fall_blau.json": {**common, "scenarios": [{"id": "fall_blau",
                    "map_ids": ["map_a"], "start_turn": 1, "start_phase": "initial_phase",
                    "start_side": "axis", "end_turn": 8, "placements": [{"unit_id": "hq",
                        "location": "1300", "steps": 1, "source_ref": "fixture:card",
                        "face_state": "ready"}]}]},
            }
            for filename, value in records.items():
                (root / filename).write_text(json.dumps(value), encoding="utf-8")
            catalog = load_catalog(root)
            self.assertEqual(Engine(catalog).new_game("fall_blau").units["hq"].face_state,
                             "ready")

    def test_nonreciprocal_neighbor_rejected(self):
        catalog = Catalog("v2025_04", {
            "a": hex_def("a", {"s": "b"}),
            "b": hex_def("b"),
        }, {}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_map_a_vertical_neighbors_use_north_and_south_edges(self):
        catalog = Catalog("v2025_04", {
            "1300": hex_def("1300", {"s": "1301"}),
            "1301": hex_def("1301", {"n": "1300"}),
        }, {}, {})
        validate_catalog(catalog)

    def test_reciprocal_but_geometrically_wrong_hex_edge_is_rejected(self):
        catalog = Catalog("v2025_04", {
            "1300": hex_def("1300", {"s": "1400"}),
            "1400": hex_def("1400", {"n": "1300"}),
        }, {}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_northwest_map_edges_follow_alternating_column_offsets(self):
        catalog = Catalog("v2025_04", {
            "1200": hex_def("1200", {"ne": "1300", "se": "1301"}),
            "1300": hex_def("1300", {"sw": "1200", "s": "1301", "se": "1400"}),
            "1301": hex_def("1301", {"nw": "1200", "n": "1300", "ne": "1400"}),
            "1400": hex_def("1400", {"nw": "1300", "sw": "1301"}),
        }, {}, {})
        validate_catalog(catalog)

    def test_unknown_hexside_feature_is_rejected(self):
        catalog = Catalog("v2025_04", {
            "1300": HexDef("1300", "clear", {"s": "1301"}, (),
                           {"s": ("railraod",)}, "fixture:hex"),
            "1301": HexDef("1301", "clear", {"n": "1300"}, (),
                           {"n": ("railraod",)}, "fixture:hex"),
        }, {}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_printed_town_and_landmark_can_be_recorded(self):
        catalog = Catalog("v2025_04", {
            "1300": HexDef("1300", "clear", {}, ("town",), {}, "fixture:map"),
            "1301": HexDef("1301", "clear", {}, ("landmark",), {}, "fixture:map"),
        }, {}, {})
        validate_catalog(catalog)

    def test_distinct_road_and_impassable_hexside_types(self):
        for feature in ("primary_road", "secondary_road", "lake_hexside", "alpine_hexside"):
            with self.subTest(feature=feature):
                catalog = Catalog("v2025_04", {
                    "1300": HexDef("1300", "clear", {"s": "1301"}, (),
                                   {"s": (feature,)}, "fixture:map"),
                    "1301": HexDef("1301", "clear", {"n": "1300"}, (),
                                   {"n": (feature,)}, "fixture:map"),
                }, {}, {})
                validate_catalog(catalog)

    def test_ambiguous_road_feature_is_rejected(self):
        catalog = Catalog("v2025_04", {
            "1300": HexDef("1300", "clear", {"s": "1301"}, (),
                           {"s": ("road",)}, "fixture:map"),
            "1301": HexDef("1301", "clear", {"n": "1300"}, (),
                           {"n": ("road",)}, "fixture:map"),
        }, {}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_printed_victory_value_is_stored_and_validated(self):
        hex_def_with_vp = HexDef("1300", "clear", {}, (), {}, "fixture:hex", victory_points=2)
        self.assertEqual(hex_def_with_vp.victory_points, 2)
        validate_catalog(Catalog("v2025_04", {"1300": hex_def_with_vp}, {}, {}))
        invalid = HexDef("1300", "clear", {}, (), {}, "fixture:hex", victory_points=-1)
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {"1300": invalid}, {}, {}))

    def test_unknown_hex_feature_is_rejected(self):
        typo = HexDef("1300", "clear", {}, ("porrt",), {}, "fixture:hex")
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {"1300": typo}, {}, {}))

    def test_unknown_neighbor_rejected(self):
        catalog = Catalog("v2025_04", {"a": hex_def("a", {"s": "missing"})}, {}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_missing_source_rejected(self):
        catalog = Catalog("v2025_04", {"a": hex_def("a", source_ref="")}, {}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_missing_placement_unit_rejected(self):
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8,
                               (Placement("missing", "a", 1, "fixture:placement"),))
        catalog = Catalog("v2025_04", {"a": hex_def("a")}, {}, {"fall_blau": scenario})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)

    def test_unit_face_step_count_must_match_rules(self):
        for steps in (0, 4):
            with self.subTest(steps=steps):
                unit = UnitDef("u", Side.AXIS, "infantry", "U",
                               (UnitFace(steps, 1, 1, 3, ()),), "fixture:unit")
                with self.assertRaises(CatalogError):
                    validate_catalog(Catalog("v2025_04", {}, {"u": unit}, {}))

    def test_duplicate_unit_face_step_count_is_rejected(self):
        unit = UnitDef("u", Side.AXIS, "infantry", "U",
                       (UnitFace(2, 3, 4, 3, ()), UnitFace(2, 1, 2, 3, ())),
                       "fixture:unit")
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {}, {"u": unit}, {}))

    def test_one_step_hq_can_have_ready_and_used_faces(self):
        unit = UnitDef("hq", Side.AXIS, "army_hq", "2A HQ",
                       (UnitFace(1, None, 1, 5, (), "ready"),
                        UnitFace(1, 0, 1, 5, (), "used")), "fixture:unit")
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8,
                               (Placement("hq", "zone:setup", 1, "fixture:card", "ready"),))
        catalog = Catalog("v2025_04", {}, {"hq": unit}, {"fall_blau": scenario})
        validate_catalog(catalog)
        self.assertEqual(tuple(face.state for face in unit.faces), ("ready", "used"))
        self.assertEqual(Engine(catalog).new_game("fall_blau").units["hq"].face_state, "ready")

    def test_placement_must_select_existing_face(self):
        unit = UnitDef("hq", Side.AXIS, "army_hq", "2A HQ",
                       (UnitFace(1, None, 1, 5, (), "ready"),), "fixture:unit")
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8,
                               (Placement("hq", "zone:setup", 1, "fixture:card", "used"),))
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {}, {"hq": unit}, {"fall_blau": scenario}))

    def test_supply_point_starts_on_full_movement_face(self):
        unit = UnitDef("sp", Side.AXIS, "supply_point", "Supply",
                       (UnitFace(1, 0, 0, 5, (), "full_movement"),
                        UnitFace(1, None, 0, None, (), "ready")), "fixture:counter")
        scenario = ScenarioDef("fall_blau", ("map_a",), 1, Phase.INITIAL, Side.AXIS, 8,
                               (Placement("sp", "zone:setup", 1, "fixture:card",
                                          "full_movement"),))
        catalog = Catalog("v2025_04", {}, {"sp": unit}, {"fall_blau": scenario})
        self.assertEqual(Engine(catalog).new_game("fall_blau").units["sp"].face_state,
                         "full_movement")

    def test_unknown_face_state_is_rejected(self):
        unit = UnitDef("u", Side.AXIS, "infantry", "U",
                       (UnitFace(1, 1, 1, 3, (), "mystery"),), "fixture:unit")
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {}, {"u": unit}, {}))

    def test_unknown_unit_ability_is_rejected(self):
        unit = UnitDef("u", Side.AXIS, "infantry", "U",
                       (UnitFace(1, 1, 1, 3, ("unverified_counter_symbol",)),),
                       "fixture:unit")
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {}, {"u": unit}, {}))

    def test_terrain_glossary_term_cannot_be_unit_type(self):
        unit = UnitDef("u", Side.AXIS, "road", "U",
                       (UnitFace(1, 1, 1, 3, ()),), "fixture:unit")
        with self.assertRaises(CatalogError):
            validate_catalog(Catalog("v2025_04", {}, {"u": unit}, {}))

    def test_catalog_copies_input_mappings(self):
        hexes = {"a": hex_def("a")}
        catalog = Catalog("v2025_04", hexes, {}, {})
        hexes.clear()
        self.assertIn("a", catalog.hexes)
        with self.assertRaises(TypeError):
            catalog.hexes["b"] = hex_def("b")

    def test_nested_definition_lists_are_copied(self):
        abilities = ["elite"]
        faces = [UnitFace(1, 1, 1, 1, abilities)]
        unit = UnitDef("u", Side.AXIS, "infantry", "U", faces, "fixture:unit")
        maps = ["map_a"]
        scenario = ScenarioDef("s", maps, 1, Phase.INITIAL, Side.AXIS, 8, [])
        abilities.append("motorized")
        faces.clear()
        maps.clear()
        self.assertEqual(unit.faces[0].abilities, ("elite",))
        self.assertEqual(scenario.map_ids, ("map_a",))

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sources.json").write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_catalog(root)

    def test_unknown_term_id_rejected(self):
        unit = UnitDef("u", Side.AXIS, "invented_unit", "U",
                       (UnitFace(1, 1, 1, 1, ()),), "fixture:unit")
        catalog = Catalog("v2025_04", {}, {"u": unit}, {})
        with self.assertRaises(CatalogError):
            validate_catalog(catalog)
