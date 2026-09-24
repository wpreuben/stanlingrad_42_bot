import unittest

from tools.map_edge_candidates import EdgeCandidate
from tools.map_edge_pixel_candidates import EdgePixelCandidate, evaluate_reviewed, score_edge_pixels


class FakeImage:
    size = (3300, 5100)

    def getpixel(self, point):
        x, y = point
        if y == 195 and x == 420:
            return (80, 150, 215)
        if y == 195 and 421 <= x <= 425:
            return (215, 180, 170)
        if y == 194 and 420 <= x <= 429:
            return (50, 50, 50)
        return (240, 233, 210)


class MapEdgePixelCandidateTests(unittest.TestCase):
    def test_scores_independent_signals_without_verifying_an_edge(self):
        edge = EdgeCandidate("1300", "s", "1301", "unreviewed", "", "")
        result = score_edge_pixels([edge], FakeImage(), threshold=1)
        self.assertEqual((result[0].blue_pixels, result[0].pink_pixels,
                          result[0].dark_pixels), (1, 5, 10))
        self.assertEqual(result[0].signals,
                         ("river_candidate", "road_candidate", "rail_or_primary_candidate"))
        self.assertEqual(result[0].review_status, "unreviewed")

    def test_quiet_wider_area_marks_only_a_candidate(self):
        edges = [
            EdgeCandidate("1300", "s", "1301", "unreviewed", "", ""),
            EdgeCandidate("1301", "s", "1302", "unreviewed", "", ""),
        ]
        result = score_edge_pixels(edges, FakeImage(), threshold=1)
        self.assertNotIn("no_feature_candidate", result[0].signals)
        self.assertIn("no_feature_candidate", result[1].signals)
        self.assertEqual(result[1].review_status, "unreviewed")

    def test_evaluation_counts_misses_and_false_positives_on_reviewed_edges(self):
        edges = [
            EdgePixelCandidate("1300", "s", "1301", "reviewed", "minor_river",
                               25, 0, 0, 25, ("river_candidate",)),
            EdgePixelCandidate("1301", "s", "1302", "reviewed", "none",
                               25, 0, 0, 25, ("river_candidate",)),
            EdgePixelCandidate("1302", "s", "1303", "reviewed", "major_river",
                               0, 0, 0, 0, ()),
        ]
        self.assertEqual(evaluate_reviewed(edges)["river_candidate"],
                         {"true_positive": 1, "false_positive": 1, "false_negative": 1})


if __name__ == "__main__":
    unittest.main()
