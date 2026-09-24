"""Check reviewed Map A CSV fragments without treating them as a complete map."""

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from engine.catalog import EDGE_FEATURES, HEX_FEATURES, OPPOSITE, TERRAINS, _expected_neighbor


HEX_FIELDS = ("hex_id", "terrain", "source_ref", "other_features")
EDGE_FIELDS = ("hex_id", "direction", "neighbor_id", "source_ref", "crossing_features")


@dataclass(frozen=True)
class AuditResult:
    hexes: int
    edges: int
    features: Counter[str]


def _read_rows(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"invalid columns: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"incomplete row: {path}")
    return rows


def _features(value: str, allowed: frozenset[str], context: str) -> tuple[str, ...]:
    if value == "none":
        return ()
    parts = tuple(value.split("|"))
    if not parts or len(set(parts)) != len(parts) or set(parts) - allowed:
        raise ValueError(f"invalid feature at {context}: {value}")
    return parts


def audit_fragments(root: Path) -> AuditResult:
    """Validate all reviewed fragments and each fragment's internal adjacency."""
    paths = sorted(root.glob("map_a_*_hexes.csv"))
    if not paths:
        raise ValueError(f"no Map A fragments: {root}")

    ids: set[str] = set()
    members: list[set[str]] = []
    edge_files: list[Path] = []
    for hex_path in paths:
        edge_path = hex_path.with_name(hex_path.name.replace("_hexes.csv", "_edges.csv"))
        if not edge_path.is_file():
            raise ValueError(f"missing edge file: {edge_path}")
        local: set[str] = set()
        for row in _read_rows(hex_path, HEX_FIELDS):
            hex_id = row["hex_id"]
            if len(hex_id) != 4 or not hex_id.isascii() or not hex_id.isdigit():
                raise ValueError(f"invalid hex ID: {hex_id}")
            if hex_id in ids or row["terrain"] not in TERRAINS or not row["source_ref"].strip():
                raise ValueError(f"invalid or duplicate hex: {hex_id}")
            _features(row["other_features"], HEX_FEATURES, hex_id)
            ids.add(hex_id)
            local.add(hex_id)
        if not local:
            raise ValueError(f"empty fragment: {hex_path}")
        members.append(local)
        edge_files.append(edge_path)

    edges: set[tuple[str, str]] = set()
    features: Counter[str] = Counter()
    for edge_path in edge_files:
        for row in _read_rows(edge_path, EDGE_FIELDS):
            source, target, direction = row["hex_id"], row["neighbor_id"], row["direction"]
            if source not in ids or target not in ids or not row["source_ref"].strip():
                raise ValueError(f"unknown edge endpoint or source: {source}->{target}")
            if direction not in OPPOSITE or _expected_neighbor(source, direction) != target:
                raise ValueError(f"invalid edge geometry: {source}:{direction}->{target}")
            pair = tuple(sorted((source, target)))
            if pair in edges:
                raise ValueError(f"duplicate edge: {source}->{target}")
            edges.add(pair)
            features.update(_features(row["crossing_features"], EDGE_FEATURES, str(pair)))

    for local in members:
        for hex_id in local:
            for direction in OPPOSITE:
                neighbor = _expected_neighbor(hex_id, direction)
                if neighbor in local and tuple(sorted((hex_id, neighbor))) not in edges:
                    raise ValueError(f"missing internal edge: {hex_id}->{neighbor}")
    return AuditResult(len(ids), len(edges), features)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("docs"))
    args = parser.parse_args()
    result = audit_fragments(args.root)
    print(f"reviewed hexes={result.hexes}, edges={result.edges}, features={dict(result.features)}")
