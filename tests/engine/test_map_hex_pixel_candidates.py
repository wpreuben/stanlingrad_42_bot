import unittest

from tools.map_hex_pixel_candidates import classify_hex_pixels, score_hex_pixels


class FakeImage:
    size = (3300, 5100)

    def getpixel(self, point):
        x, y = point
        if 600 <= x <= 660 and 100 <= y <= 180:
            return (160, 195, 130)
        return (239, 235, 224)


class MapHexPixelCandidateTests(unittest.TestCase):
    def test_scores_distinct_hex_colors_as_candidates(self):
        result = score_hex_pixels(["1300", "1500"], FakeImage(), {"1300": "clear"})
        self.assertEqual(result[0].candidate, "clear_candidate")
        self.assertEqual(result[0].reviewed_terrain, "clear")
        self.assertEqual(result[1].candidate, "vegetation_candidate")
        self.assertEqual(result[1].reviewed_terrain, "")

    def test_classification_keeps_ambiguous_city_and_marsh_separate(self):
        self.assertEqual(classify_hex_pixels((170, 165, 145), 0.02, 0.24, 0.13),
                         "major_city_candidate")
        self.assertEqual(classify_hex_pixels((192, 198, 189), 0.09, 0.0, 0.20),
                         "marsh_candidate")
        self.assertEqual(classify_hex_pixels((195, 189, 178), 0.0, 0.15, 0.11),
                         "unresolved")


if __name__ == "__main__":
    unittest.main()
