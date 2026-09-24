import csv
import tempfile
import unittest
from pathlib import Path

from tools.map_fragment_audit import audit_fragments


HEX_FIELDS = ("hex_id", "terrain", "source_ref", "other_features", "victory_points")
EDGE_FIELDS = ("hex_id", "direction", "neighbor_id", "source_ref", "crossing_features")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


class MapFragmentAuditTests(unittest.TestCase):
    def test_checked_fragment_has_all_internal_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_csv(root / "map_a_sample_hexes.csv", HEX_FIELDS, (
                ("1300", "clear", "map:crop", "none", "1"),
                ("1301", "clear", "map:crop", "landmark", "0")))
            write_csv(root / "map_a_sample_edges.csv", EDGE_FIELDS, (
                ("1300", "s", "1301", "map:crop", "secondary_road|minor_river"),))
            result = audit_fragments(root)
            self.assertEqual((result.hexes, result.edges), (2, 1))
            self.assertEqual(result.features["minor_river"], 1)
            self.assertEqual(result.victory_points, 1)

    def test_missing_internal_edge_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_csv(root / "map_a_sample_hexes.csv", HEX_FIELDS, (
                ("1300", "clear", "map:crop", "none", "0"),
                ("1301", "clear", "map:crop", "none", "0")))
            write_csv(root / "map_a_sample_edges.csv", EDGE_FIELDS, ())
            with self.assertRaisesRegex(ValueError, "missing internal edge"):
                audit_fragments(root)

    def test_missing_edge_between_fragments_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, hex_id in (("west", "1300"), ("east", "1400")):
                write_csv(root / f"map_a_{name}_hexes.csv", HEX_FIELDS, (
                    (hex_id, "clear", "map:crop", "none", "0"),))
                write_csv(root / f"map_a_{name}_edges.csv", EDGE_FIELDS, ())
            with self.assertRaisesRegex(ValueError, "missing internal edge"):
                audit_fragments(root)

    def test_wrong_geometry_and_duplicate_edge_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_csv(root / "map_a_sample_hexes.csv", HEX_FIELDS, (
                ("1300", "clear", "map:crop", "none", "0"),
                ("1301", "clear", "map:crop", "none", "0")))
            edge_path = root / "map_a_sample_edges.csv"
            write_csv(edge_path, EDGE_FIELDS, (
                ("1300", "ne", "1301", "map:crop", "none"),))
            with self.assertRaisesRegex(ValueError, "geometry"):
                audit_fragments(root)
            write_csv(edge_path, EDGE_FIELDS, (
                ("1300", "s", "1301", "map:crop", "none"),
                ("1301", "n", "1300", "map:crop", "none")))
            with self.assertRaisesRegex(ValueError, "duplicate edge"):
                audit_fragments(root)

    def test_negative_victory_points_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_csv(root / "map_a_sample_hexes.csv", HEX_FIELDS, (
                ("1300", "clear", "map:crop", "none", "-1"),))
            write_csv(root / "map_a_sample_edges.csv", EDGE_FIELDS, ())
            with self.assertRaisesRegex(ValueError, "victory_points"):
                audit_fragments(root)

    def test_current_verified_fragments(self):
        root = Path(__file__).resolve().parents[2] / "docs"
        result = audit_fragments(root)
        self.assertEqual((result.hexes, result.edges), (80, 178))
        self.assertEqual(result.features["minor_river"], 23)
        self.assertEqual(result.features["major_river"], 5)
        self.assertEqual(result.features["railroad"], 11)
        self.assertEqual(result.features["secondary_road"], 24)
        self.assertEqual(result.victory_points, 1)


if __name__ == "__main__":
    unittest.main()
