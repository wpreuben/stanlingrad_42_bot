"""Load and validate versioned, immutable game reference data."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .errors import CatalogError
from .types import Phase, Side


RULESET_ID = "v2025_04"
SCHEMA_VERSION = 1
OPPOSITE = {"n": "s", "ne": "sw", "se": "nw",
            "s": "n", "sw": "ne", "nw": "se"}
TERRAINS = frozenset({"clear", "desert", "rough", "woods", "wooded_rough",
                      "mountain", "minor_city", "major_city", "marsh", "seasonal_marsh"})
EDGE_FEATURES = frozenset({"primary_road", "secondary_road", "railroad", "minor_river", "major_river",
                           "volga_river", "bridge", "road_bridge", "railroad_bridge",
                           "ferry", "lake_hexside", "alpine_hexside", "impassable_hexside"})
HEX_FEATURES = frozenset({"town", "landmark", "port", "fortification", "entry_area", "supply_source"})
DEFAULT_GLOSSARY = Path(__file__).resolve().parents[2] / "data" / "glossary.csv"


@dataclass(frozen=True)
class HexDef:
    id: str
    terrain: str
    neighbors: Mapping[str, str]
    features: tuple[str, ...]
    edge_features: Mapping[str, tuple[str, ...]]
    source_ref: str
    victory_points: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "neighbors", MappingProxyType(dict(self.neighbors)))
        object.__setattr__(self, "features", tuple(self.features))
        object.__setattr__(self, "edge_features", MappingProxyType(
            {direction: tuple(features) for direction, features in self.edge_features.items()}))


@dataclass(frozen=True)
class UnitFace:
    steps: int
    attack: int | None
    defense: int | None
    movement: int | None
    abilities: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "abilities", tuple(self.abilities))


@dataclass(frozen=True)
class UnitDef:
    id: str
    side: Side
    term_id: str
    printed_label: str
    faces: tuple[UnitFace, ...]
    source_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "faces", tuple(self.faces))


@dataclass(frozen=True)
class Placement:
    unit_id: str
    location: str
    steps: int
    source_ref: str


@dataclass(frozen=True)
class ScenarioDef:
    id: str
    map_ids: tuple[str, ...]
    start_turn: int
    start_phase: Phase
    start_side: Side
    end_turn: int
    placements: tuple[Placement, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "map_ids", tuple(self.map_ids))
        object.__setattr__(self, "placements", tuple(self.placements))


@dataclass(frozen=True)
class Catalog:
    ruleset_id: str
    hexes: Mapping[str, HexDef]
    units: Mapping[str, UnitDef]
    scenarios: Mapping[str, ScenarioDef]

    def __post_init__(self) -> None:
        for name in ("hexes", "units", "scenarios"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


def _term_ids() -> frozenset[str]:
    try:
        with DEFAULT_GLOSSARY.open(encoding="utf-8-sig", newline="") as stream:
            return frozenset(row["term_id"] for row in csv.DictReader(stream))
    except (OSError, KeyError) as exc:
        raise CatalogError(f"cannot read glossary: {DEFAULT_GLOSSARY}") from exc


def _required_source(value: str, context: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"missing source_ref: {context}")


def _int(value: object, context: str, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise CatalogError(f"invalid integer: {context}")


def validate_catalog(catalog: Catalog) -> None:
    """Reject any reference or graph defect before a catalog is used."""
    if catalog.ruleset_id != RULESET_ID:
        raise CatalogError(f"unsupported ruleset: {catalog.ruleset_id}")
    terms = _term_ids()
    for key, hex_def in catalog.hexes.items():
        if key != hex_def.id or not key or hex_def.terrain not in TERRAINS:
            raise CatalogError(f"invalid hex: {key}")
        _required_source(hex_def.source_ref, f"hex {key}")
        _int(hex_def.victory_points, f"hex {key} victory_points")
        if set(hex_def.features) - HEX_FEATURES or set(hex_def.features) - terms:
            raise CatalogError(f"unknown hex feature at {key}")
        if set(hex_def.neighbors) - OPPOSITE.keys() or set(hex_def.edge_features) - OPPOSITE.keys():
            raise CatalogError(f"invalid direction at hex {key}")
        for direction, neighbor_id in hex_def.neighbors.items():
            other = catalog.hexes.get(neighbor_id)
            opposite = OPPOSITE[direction]
            if other is None or other.neighbors.get(opposite) != key:
                raise CatalogError(f"nonreciprocal edge {key}:{direction}->{neighbor_id}")
            if hex_def.edge_features.get(direction, ()) != other.edge_features.get(opposite, ()):
                raise CatalogError(f"mismatched edge features {key}:{direction}")
        for direction, features in hex_def.edge_features.items():
            if features and direction not in hex_def.neighbors:
                raise CatalogError(f"edge feature without neighbor {key}:{direction}")
            if set(features) - EDGE_FEATURES or set(features) - terms:
                raise CatalogError(f"unknown edge feature at {key}:{direction}")
    for key, unit in catalog.units.items():
        if key != unit.id or not key or not isinstance(unit.side, Side):
            raise CatalogError(f"invalid unit: {key}")
        _required_source(unit.source_ref, f"unit {key}")
        if unit.term_id not in terms:
            raise CatalogError(f"unknown term_id: {unit.term_id}")
        if not unit.faces:
            raise CatalogError(f"unit has no faces: {key}")
        for face in unit.faces:
            _int(face.steps, f"unit {key} steps", 1)
            for field in ("attack", "defense", "movement"):
                value = getattr(face, field)
                if value is not None:
                    _int(value, f"unit {key} {field}")
    for key, scenario in catalog.scenarios.items():
        if key != scenario.id or not key or not scenario.map_ids:
            raise CatalogError(f"invalid scenario: {key}")
        _int(scenario.start_turn, f"scenario {key} start_turn", 1)
        _int(scenario.end_turn, f"scenario {key} end_turn", scenario.start_turn)
        if not isinstance(scenario.start_phase, Phase) or not isinstance(scenario.start_side, Side):
            raise CatalogError(f"invalid scenario phase/side: {key}")
        seen: set[str] = set()
        for placement in scenario.placements:
            _required_source(placement.source_ref, f"placement {placement.unit_id}")
            if placement.unit_id in seen or placement.unit_id not in catalog.units:
                raise CatalogError(f"duplicate or unknown placement unit: {placement.unit_id}")
            seen.add(placement.unit_id)
            if placement.location not in catalog.hexes and not placement.location.startswith("zone:"):
                raise CatalogError(f"unknown placement location: {placement.location}")
            _int(placement.steps, f"placement {placement.unit_id} steps", 1)
            if placement.steps not in {face.steps for face in catalog.units[placement.unit_id].faces}:
                raise CatalogError(f"invalid placement steps: {placement.unit_id}")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_unique_pairs)
    except (OSError, ValueError, UnicodeError) as exc:
        raise CatalogError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION or value.get("ruleset_id") != RULESET_ID:
        raise CatalogError(f"invalid schema/ruleset in {path}")
    return value


def _unique_by_id(records: list[dict], factory, label: str) -> dict:
    result = {}
    for record in records:
        item = factory(record)
        if item.id in result:
            raise CatalogError(f"duplicate {label} ID: {item.id}")
        result[item.id] = item
    return result


def load_catalog(root: Path) -> Catalog:
    """Read a complete versioned catalog from a data directory."""
    root = Path(root)
    _read_json(root / "sources.json")
    for filename in ("map_a.json", "units_s1.json", "fall_blau.json"):
        if not (root / filename).is_file():
            raise CatalogError(f"missing catalog file: {filename}")
    try:
        hexes = {}
        if (root / "map_a.json").exists():
            data = _read_json(root / "map_a.json")
            hexes = _unique_by_id(data["hexes"], lambda h: HexDef(
                h["id"], h["terrain"], h["neighbors"], tuple(h["features"]),
                {k: tuple(v) for k, v in h["edge_features"].items()}, h["source_ref"],
                h.get("victory_points", 0)), "hex")
        units = {}
        if (root / "units_s1.json").exists():
            data = _read_json(root / "units_s1.json")
            units = _unique_by_id(data["units"], lambda u: UnitDef(
                u["id"], Side(u["side"]), u["term_id"], u["printed_label"],
                tuple(UnitFace(f["steps"], f["attack"], f["defense"], f["movement"],
                               tuple(f["abilities"])) for f in u["faces"]), u["source_ref"]), "unit")
        scenarios = {}
        if (root / "fall_blau.json").exists():
            data = _read_json(root / "fall_blau.json")
            scenarios = _unique_by_id(data["scenarios"], lambda s: ScenarioDef(
                s["id"], tuple(s["map_ids"]), s["start_turn"], Phase(s["start_phase"]),
                Side(s["start_side"]), s["end_turn"],
                tuple(Placement(p["unit_id"], p["location"], p["steps"], p["source_ref"])
                      for p in s["placements"])), "scenario")
        if not hexes or not units or not scenarios:
            raise CatalogError("catalog map, unit, and scenario data must be nonempty")
        catalog = Catalog(RULESET_ID, hexes, units, scenarios)
        validate_catalog(catalog)
        return catalog
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        if isinstance(exc, CatalogError):
            raise
        raise CatalogError(f"invalid catalog data: {exc}") from exc
