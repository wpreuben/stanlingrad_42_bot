import unittest

from tools.map_edge_candidates import EdgeCandidate
from tools.map_image_evidence import center_of, score_blue_edges, select_river_review


class FakeImage:
    size = (3300, 5100)

    def getpixel(self, point):
        return (80, 150, 215) if point == (420, 195) else (240, 233, 210)


class MapImageEvidenceTests(unittest.TestCase):
    def test_center_uses_printed_map_grid(self):
        self.assertEqual(center_of("1300"), (420, 138))
        self.assertEqual(center_of("1301"), (420, 252))
        self.assertEqual(center_of("3200"), (2301, 195))

    def test_blue_pixel_probe_prioritizes_without_changing_review_status(self):
        edges = [EdgeCandidate("1300", "s", "1301", "unreviewed", "", "")]
        evidence = score_blue_edges(edges, FakeImage())
        self.assertEqual(evidence[0].blue_pixels, 1)
        self.assertEqual(evidence[0].review_status, "unreviewed")
        self.assertEqual(evidence[0].crossing_features, "")
        self.assertEqual(select_river_review(evidence, minimum_blue=1), evidence)
        self.assertEqual(select_river_review(evidence, minimum_blue=2), [])


if __name__ == "__main__":
    unittest.main()
