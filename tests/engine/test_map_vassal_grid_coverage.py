import unittest

from tools.map_vassal_grid_coverage import candidate_centers, point_in_polygon, zone_candidate_edges


class MapVassalGridCoverageTests(unittest.TestCase):
    def test_polygon_includes_only_grid_centers_inside(self):
        polygon = [(400, 100), (700, 100), (700, 300), (400, 300)]
        result = candidate_centers(polygon, columns=range(13, 17), rows=range(0, 2))
        self.assertIn(("1300", 420, 138), result)
        self.assertIn(("1501", 618, 252), result)
        self.assertNotIn(("1601", 717, 309), result)

    def test_boundary_is_included_and_outside_is_excluded(self):
        polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertTrue(point_in_polygon(5, 0, polygon))
        self.assertTrue(point_in_polygon(5, 5, polygon))
        self.assertFalse(point_in_polygon(11, 5, polygon))

    def test_new_zone_edges_are_separate_from_checked_id_edges(self):
        result = zone_candidate_edges({"1300", "1301", "1400"}, {"1300", "1301"})
        self.assertEqual(result, [("1300", "se", "1400"),
                                  ("1301", "ne", "1400")])


if __name__ == "__main__":
    unittest.main()
