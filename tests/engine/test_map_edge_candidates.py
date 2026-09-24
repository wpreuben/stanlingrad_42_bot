import csv
import tempfile
import unittest
from pathlib import Path

from tools.map_edge_candidates import build_edge_candidates


def write_rows(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


class MapEdgeCandidateTests(unittest.TestCase):
    def test_geometry_is_generated_but_only_checked_edges_have_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            printed = root / "map_a_printed_id_checks.csv"
            write_rows(printed, ("hex_id", "source_region", "review_scope"), (
                ("1300", "crop", "printed_id_only"),
                ("1301", "crop", "printed_id_only"),
                ("1400", "crop", "printed_id_only"),
            ))
            write_rows(root / "map_a_sample_hexes.csv",
                       ("hex_id", "terrain", "source_ref", "other_features"), (
                           ("1300", "clear", "map:crop", "none"),
                           ("1301", "clear", "map:crop", "none"),
                       ))
            write_rows(root / "map_a_sample_edges.csv",
                       ("hex_id", "direction", "neighbor_id", "source_ref", "crossing_features"), (
                           ("1300", "s", "1301", "map:crop", "none"),
                       ))

            candidates = build_edge_candidates(printed, root)

            self.assertEqual([
                (edge.hex_id, edge.direction, edge.neighbor_id,
                 edge.review_status, edge.crossing_features)
                for edge in candidates
            ], [
                ("1300", "s", "1301", "reviewed", "none"),
                ("1300", "se", "1400", "unreviewed", ""),
                ("1301", "ne", "1400", "unreviewed", ""),
            ])
            self.assertEqual(candidates[0].source_ref, "map:crop")
            self.assertEqual(candidates[1].source_ref, "")

    def test_duplicate_printed_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            printed = root / "map_a_printed_id_checks.csv"
            write_rows(printed, ("hex_id", "source_region", "review_scope"), (
                ("1300", "crop", "printed_id_only"),
                ("1300", "crop", "printed_id_only"),
            ))
            write_rows(root / "map_a_sample_hexes.csv",
                       ("hex_id", "terrain", "source_ref", "other_features"), (
                           ("1300", "clear", "map:crop", "none"),
                       ))
            write_rows(root / "map_a_sample_edges.csv",
                       ("hex_id", "direction", "neighbor_id", "source_ref", "crossing_features"), ())

            with self.assertRaisesRegex(ValueError, "duplicate printed ID"):
                build_edge_candidates(printed, root)

    def test_current_reviewed_edges_are_preserved(self):
        root = Path(__file__).resolve().parents[2] / "docs"
        candidates = build_edge_candidates(root / "map_a_printed_id_checks.csv", root)
        reviewed = [edge for edge in candidates if edge.review_status == "reviewed"]
        self.assertEqual(len(reviewed), 144)
        self.assertTrue(all(edge.crossing_features and edge.source_ref for edge in reviewed))
        self.assertGreater(len(candidates), len(reviewed))


if __name__ == "__main__":
    unittest.main()
