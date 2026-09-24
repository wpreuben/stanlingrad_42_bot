import unittest
from pathlib import Path

from engine.catalog import load_catalog


DATA = Path(__file__).resolve().parents[2] / "data" / "engine" / "v2025_04"


class MapATests(unittest.TestCase):
    @unittest.skip("Map A 전체 전사 및 원본 대조 대기: docs/rule_issues.md")
    def test_s1_reference_hexes_exist_in_complete_map_a(self):
        catalog = load_catalog(DATA)
        for hex_id in ("1300", "1600", "3806", "4100", "4111"):
            with self.subTest(hex_id=hex_id):
                self.assertIn(hex_id, catalog.hexes)
