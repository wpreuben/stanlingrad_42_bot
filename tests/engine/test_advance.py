import unittest

from engine.advance import advance_allowance, advance_rate
from engine.catalog import UnitDef, UnitFace
from engine.errors import CatalogError, InvalidActionError, UnsupportedRuleError
from engine.types import Side


def unit(term_id, side=Side.AXIS, movement=5):
    face = UnitFace(1, 2, 2, movement, ())
    return UnitDef("fixture", side, term_id, "fixture", (face,), "fixture:counter"), face


class AdvanceRateTests(unittest.TestCase):
    def test_mechanized_cavalry_and_other_rates(self):
        cases = (("tank_unit", 4), ("motorized_infantry", 4),
                 ("artillery_support_unit", 4), ("sturmgeschutz", 4),
                 ("supply_point", 4), ("cavalry", 3),
                 ("infantry", 2), ("bicycle_infantry", 2),
                 ("nkvd_infantry", 2))
        for term_id, expected in cases:
            with self.subTest(term_id=term_id):
                counter, face = unit(term_id)
                self.assertEqual(advance_rate(counter, face), expected)

    def test_soviet_army_hq_with_three_movement_points_is_exception(self):
        hq, face = unit("army_hq", Side.SOVIET, 3)
        self.assertEqual(advance_rate(hq, face), 2)
        faster_hq, faster_face = unit("army_hq", Side.SOVIET, 5)
        self.assertEqual(advance_rate(faster_hq, faster_face), 4)
        axis_hq, axis_face = unit("army_hq", Side.AXIS, 3)
        self.assertEqual(advance_rate(axis_hq, axis_face), 4)

    def test_current_face_controls_hq_exception(self):
        fast = UnitFace(1, 0, 1, 5, ())
        slow = UnitFace(1, 0, 1, 3, (), "used")
        hq = UnitDef("hq", Side.SOVIET, "army_hq", "HQ", (fast, slow), "fixture:counter")
        self.assertEqual(advance_rate(hq, fast), 4)
        self.assertEqual(advance_rate(hq, slow), 2)

    def test_crt_result_caps_individual_advance(self):
        mech, face = unit("tank_unit")
        self.assertEqual(advance_allowance(mech, face, 3), 3)
        self.assertEqual(advance_allowance(mech, face, 5), 4)
        self.assertEqual(advance_allowance(mech, face, 0), 0)

    def test_invalid_result_or_unclassified_unit_is_rejected(self):
        counter, face = unit("tank_unit")
        for result in (-1, True, 2.0):
            with self.subTest(result=result), self.assertRaises(InvalidActionError):
                advance_allowance(counter, face, result)
        unknown, unknown_face = unit("leader_unit")
        with self.assertRaises(UnsupportedRuleError):
            advance_rate(unknown, unknown_face)
        with self.assertRaises(CatalogError):
            advance_rate(counter, UnitFace(1, 2, 2, 6, ()))


if __name__ == "__main__":
    unittest.main()
