"""Generate coordinate-adjacent Map A edge candidates from confirmed printed IDs.

An unreviewed candidate is only a geometric possibility: its hexside may be
sea, impassable, or absent from the eventual playable map.
"""

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from engine.catalog import _expected_neighbor
from tools.map_fragment_audit import EDGE_FIELDS, HEX_FIELDS, _read_rows, audit_fragments


PRINTED_FIELDS = ("hex_id", "source_region", "review_scope")
CANDIDATE_FIELDS = ("hex_id", "direction", "neighbor_id", "review_status",
                    "crossing_features", "source_ref")
FORWARD_DIRECTIONS = ("s", "ne", "se")


@dataclass(frozen=True)
class EdgeCandidate:
    hex_id: str
    direction: str
    neighbor_id: str
    review_status: str
    crossing_features: str
    source_ref: str


def build_edge_candidates(printed_csv: Path, fragments_root: Path) -> list[EdgeCandidate]:
    """Preserve checked edges; leave all other geometric candidates undecided."""
    printed_ids: set[str] = set()
    for row in _read_rows(printed_csv, PRINTED_FIELDS):
        hex_id = row["hex_id"]
        if len(hex_id) != 4 or not hex_id.isascii() or not hex_id.isdigit():
            raise ValueError(f"invalid printed ID: {hex_id}")
        if hex_id in printed_ids:
            raise ValueError(f"duplicate printed ID: {hex_id}")
        printed_ids.add(hex_id)

    audit_fragments(fragments_root)
    reviewed_ids: set[str] = set()
    reviewed_edges: dict[tuple[str, str], dict[str, str]] = {}
    for path in sorted(fragments_root.glob("map_a_*_hexes.csv")):
        reviewed_ids.update(row["hex_id"] for row in _read_rows(path, HEX_FIELDS, optional_last=True))
        edge_path = path.with_name(path.name.replace("_hexes.csv", "_edges.csv"))
        for row in _read_rows(edge_path, EDGE_FIELDS):
            pair = tuple(sorted((row["hex_id"], row["neighbor_id"])))
            reviewed_edges[pair] = row
    if reviewed_ids - printed_ids:
        raise ValueError(f"reviewed IDs missing from printed IDs: {sorted(reviewed_ids - printed_ids)}")

    candidates: list[EdgeCandidate] = []
    for hex_id in sorted(printed_ids):
        for direction in FORWARD_DIRECTIONS:
            neighbor = _expected_neighbor(hex_id, direction)
            if neighbor not in printed_ids:
                continue
            row = reviewed_edges.get(tuple(sorted((hex_id, neighbor))))
            candidates.append(EdgeCandidate(
                hex_id, direction, neighbor, "reviewed" if row else "unreviewed",
                row["crossing_features"] if row else "",
                row["source_ref"] if row else "",
            ))
    if sum(edge.review_status == "reviewed" for edge in candidates) != len(reviewed_edges):
        raise ValueError("reviewed edge missing from printed ID candidates")
    return candidates


def write_candidates(candidates: list[EdgeCandidate], stream) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(CANDIDATE_FIELDS)
    for edge in candidates:
        writer.writerow((edge.hex_id, edge.direction, edge.neighbor_id,
                         edge.review_status, edge.crossing_features, edge.source_ref))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("printed_csv", nargs="?", type=Path,
                        default=Path("docs/map_a_printed_id_checks.csv"))
    parser.add_argument("fragments_root", nargs="?", type=Path, default=Path("docs"))
    parser.add_argument("--output", type=Path, help="write candidate CSV here instead of stdout")
    args = parser.parse_args()
    result = build_edge_candidates(args.printed_csv, args.fragments_root)
    if args.output:
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            write_candidates(result, stream)
    else:
        write_candidates(result, sys.stdout)
