import unittest

from tools.map_edge_candidates import EdgeCandidate
from tools.map_edge_review_sheet import crop_box, select_review_edges


class MapEdgeReviewSheetTests(unittest.TestCase):
    def test_selects_only_unreviewed_edges_touching_region(self):
        edges = [
            EdgeCandidate("1300", "s", "1301", "reviewed", "none", "map"),
            EdgeCandidate("1301", "ne", "1400", "unreviewed", "", ""),
            EdgeCandidate("1400", "s", "1401", "unreviewed", "", ""),
            EdgeCandidate("1500", "s", "1501", "unreviewed", "", ""),
        ]
        self.assertEqual(select_review_edges(edges, (13, 13), (0, 1)), [edges[1]])

    def test_crop_contains_both_hex_centers_and_midpoint(self):
        edge = EdgeCandidate("1300", "s", "1301", "unreviewed", "", "")
        left, top, right, bottom = crop_box(edge)
        self.assertLessEqual(left, 420)
        self.assertGreaterEqual(right, 420)
        self.assertLessEqual(top, 138)
        self.assertGreaterEqual(bottom, 252)
        self.assertEqual((left, top, right, bottom), (330, 120, 510, 270))

    def test_eastern_crop_tracks_narrower_printed_column_pitch(self):
        edge = EdgeCandidate("3403", "ne", "3503", "unreviewed", "", "")
        self.assertEqual(crop_box(edge), (2458, 433, 2638, 583))


if __name__ == "__main__":
    unittest.main()
