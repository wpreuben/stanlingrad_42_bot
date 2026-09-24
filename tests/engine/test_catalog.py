import json
import tempfile
import unittest
from pathlib import Path

from engine.catalog import Catalog, HexDef, Placement, ScenarioDef, UnitDef, UnitFace, load_catalog, validate_catalog
from engine.errors import CatalogError
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
