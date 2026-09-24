import unittest

from tools.map_vassal_grid_coverage import candidate_centers, point_in_polygon


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


if __name__ == "__main__":
    unittest.main()
