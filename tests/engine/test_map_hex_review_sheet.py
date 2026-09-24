import unittest

from tools.map_hex_pixel_candidates import HexPixelCandidate
from tools.map_hex_review_sheet import select_hexes


class MapHexReviewSheetTests(unittest.TestCase):
    def test_selects_only_requested_candidate_and_orders_by_blue_fraction(self):
        rows = [
            HexPixelCandidate("1001", "unresolved", 0, 155, 209, 0, 0, 0.75, ""),
            HexPixelCandidate("1002", "clear_candidate", 239, 235, 224, 0, 0, 0, ""),
            HexPixelCandidate("1003", "unresolved", 223, 220, 200, 0, 0, 0, ""),
        ]
        self.assertEqual([row.hex_id for row in select_hexes(rows, "unresolved")],
                         ["1001", "1003"])


if __name__ == "__main__":
    unittest.main()
