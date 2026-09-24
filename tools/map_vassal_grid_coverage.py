"""List Map A grid centers inside VASSAL's zone that lack a checked printed ID."""

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from engine.catalog import _expected_neighbor
from tools.map_edge_candidates import FORWARD_DIRECTIONS
from tools.map_image_evidence import center_of


def point_in_polygon(x: int, y: int, polygon: list[tuple[int, int]]) -> bool:
    if len(polygon) < 3:
        raise ValueError("polygon needs at least three points")
    inside = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        cross = (x - ax) * (by - ay) - (y - ay) * (bx - ax)
        if cross == 0 and min(ax, bx) <= x <= max(ax, bx) and min(ay, by) <= y <= max(ay, by):
            return True
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            inside = not inside
    return inside


def candidate_centers(
    polygon: list[tuple[int, int]], columns: range = range(100), rows: range = range(100),
) -> list[tuple[str, int, int]]:
    result = []
    for column in columns:
        for row in rows:
            hex_id = f"{column:02d}{row:02d}"
            x, y = center_of(hex_id)
            if 0 <= x < 3300 and 0 <= y < 5100 and point_in_polygon(x, y, polygon):
                result.append((hex_id, x, y))
    return result


def load_map_a_zone(build_file: Path) -> list[tuple[int, int]]:
    root = ET.parse(build_file).getroot()
    board = next((node for node in root.iter()
                  if node.tag.endswith(".Board") and node.get("name") == "Map A"), None)
    if board is None:
        raise ValueError("Map A board missing from VASSAL build file")
    zone = next((node for node in board.iter()
                 if node.tag.endswith(".Zone") and node.get("name") == "Hexgrid"), None)
    if zone is None or not zone.get("path"):
        raise ValueError("Map A Hexgrid zone missing from VASSAL build file")
    return [tuple(int(value) for value in point.split(","))
            for point in zone.get("path").split(";")]


def read_printed_ids(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != ("hex_id", "source_region", "review_scope"):
            raise ValueError(f"invalid printed ID columns: {path}")
        rows = list(reader)
    ids = [row["hex_id"] for row in rows]
    if len(ids) != len(set(ids)) or any(len(h) != 4 or not h.isascii() or not h.isdigit()
                                       for h in ids):
        raise ValueError("printed IDs must be unique four-digit numbers")
    return set(ids)


def zone_candidate_edges(
    zone_ids: set[str], checked_ids: set[str],
) -> list[tuple[str, str, str]]:
    if not checked_ids <= zone_ids:
        raise ValueError("checked printed ID outside Map A zone")
    result = []
    for hex_id in sorted(zone_ids):
        for direction in FORWARD_DIRECTIONS:
            neighbor = _expected_neighbor(hex_id, direction)
            if neighbor in zone_ids and (hex_id not in checked_ids or neighbor not in checked_ids):
                result.append((hex_id, direction, neighbor))
    return result


def write_review_queue(rows: list[tuple[str, int, int]], stream) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("hex_id", "center_x", "center_y", "review_status"))
    for hex_id, x, y in rows:
        writer.writerow((hex_id, x, y, "unconfirmed_zone_center"))


def write_edge_queue(rows: list[tuple[str, str, str]], stream) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("hex_id", "direction", "neighbor_id", "review_status"))
    for hex_id, direction, neighbor_id in rows:
        writer.writerow((hex_id, direction, neighbor_id, "zone_unconfirmed"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_file", type=Path)
    parser.add_argument("--printed-csv", type=Path,
                        default=Path("docs/map_a_printed_id_checks.csv"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edge-output", type=Path)
    args = parser.parse_args()

    centers = candidate_centers(load_map_a_zone(args.build_file))
    checked = read_printed_ids(args.printed_csv)
    candidates = [row for row in centers if row[0] not in checked]
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        write_review_queue(candidates, stream)
    if args.edge_output:
        edges = zone_candidate_edges({row[0] for row in centers}, checked)
        with args.edge_output.open("w", newline="", encoding="utf-8") as stream:
            write_edge_queue(edges, stream)
        print(f"zone-only geometric edges={len(edges)}")
    print(f"zone centers={len(centers)}, checked_inside={len(centers)-len(candidates)}, "
          f"unconfirmed={len(candidates)}, checked_outside={sorted(checked - {r[0] for r in centers})}")
