"""Advance After Combat distance cap (2025 English rules §§2.3.3, 14.2.1–2).

This module calculates distance only; combat eligibility and legal paths are
resolved separately by the combat and movement rules.
"""

from .catalog import UnitDef, UnitFace
from .errors import CatalogError, InvalidActionError, UnsupportedRuleError
from .types import Side


MECHANIZED = frozenset({
    "tank_unit", "mechanized_unit", "panzergrenadier", "tank_destroyer",
    "motorized_infantry", "artillery_support_unit", "army_hq",
    "sturmgeschutz", "supply_point",
})
NON_MECHANIZED = frozenset({
    "non_mechanized_unit", "infantry", "security", "jager_infantry",
    "naval_infantry", "mountain_infantry", "bicycle_infantry",
    "nkvd_infantry", "engineer", "ski",
})


def advance_rate(unit: UnitDef, face: UnitFace) -> int:
    """Return the unit's maximum advance in hexes under §14.2.2.

    A Soviet Army HQ with printed MA 3 uses the two-hex exception. Abstract
    glossary terms without a known movement class are intentionally rejected.
    """
    if face not in unit.faces:
        raise CatalogError(f"face does not belong to unit: {unit.id}")
    if unit.term_id == "cavalry":
        return 3
    if unit.term_id in NON_MECHANIZED:
        return 2
    if unit.term_id in MECHANIZED:
        if (unit.term_id == "army_hq" and unit.side is Side.SOVIET
                and face.movement == 3):
            return 2
        return 4
    raise UnsupportedRuleError(f"unclassified advance rate: {unit.term_id}")


def advance_allowance(unit: UnitDef, face: UnitFace, crt_result: int) -> int:
    """Cap a nonnegative CRT advance result at the unit's rate (§14.2.1)."""
    if type(crt_result) is not int or crt_result < 0:
        raise InvalidActionError(f"invalid CRT advance result: {crt_result!r}")
    return min(crt_result, advance_rate(unit, face))
