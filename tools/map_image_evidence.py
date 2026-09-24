"""Rank Map A river-edge candidates from blue pixels; never verify edges."""

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tools.map_edge_candidates import EdgeCandidate, build_edge_candidates


class PixelImage(Protocol):
    size: tuple[int, int]

    def getpixel(self, point: tuple[int, int]) -> tuple[int, int, int]: ...


@dataclass(frozen=True)
class EdgeImageEvidence:
    hex_id: str
    direction: str
    neighbor_id: str
    review_status: str
    crossing_features: str
    blue_pixels: int


def center_of(hex_id: str) -> tuple[int, int]:
    """Printed ID center on the 3300×5100 Map A source image."""
    column, row = int(hex_id[:2]), int(hex_id[2:])
    return 420 + (column - 13) * 99, 138 + row * 114 + (57 if column % 2 == 0 else 0)


def score_blue_edges(candidates: list[EdgeCandidate], image: PixelImage) -> list[EdgeImageEvidence]:
    if image.size != (3300, 5100):
        raise ValueError(f"Map A image must be 3300x5100 pixels; got {image.size}")
    scored = []
    for edge in candidates:
        x1, y1 = center_of(edge.hex_id)
        x2, y2 = center_of(edge.neighbor_id)
        mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
        blue_pixels = 0
        for x in range(max(0, mid_x - 14), min(image.size[0], mid_x + 15)):
            for y in range(max(0, mid_y - 14), min(image.size[1], mid_y + 15)):
                red, green, blue = image.getpixel((x, y))
                blue_pixels += blue > red + 20 and blue > green + 5 and blue > 120
        scored.append(EdgeImageEvidence(edge.hex_id, edge.direction, edge.neighbor_id,
                                        edge.review_status, edge.crossing_features,
                                        blue_pixels))
    return scored


def select_river_review(evidence: list[EdgeImageEvidence], minimum_blue: int = 25) -> list[EdgeImageEvidence]:
    if minimum_blue < 1:
        raise ValueError("minimum_blue must be positive")
    return sorted((edge for edge in evidence if edge.review_status == "unreviewed"
                   and edge.blue_pixels >= minimum_blue),
                  key=lambda edge: (-edge.blue_pixels, edge.hex_id, edge.direction))


def write_river_review(evidence: list[EdgeImageEvidence], stream, source_image: str) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("hex_id", "direction", "neighbor_id", "blue_pixels_29x29",
                     "review_status", "source_image"))
    for edge in evidence:
        writer.writerow((edge.hex_id, edge.direction, edge.neighbor_id,
                         edge.blue_pixels, edge.review_status, source_image))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_image", type=Path)
    parser.add_argument("--printed-csv", type=Path, default=Path("docs/map_a_printed_id_checks.csv"))
    parser.add_argument("--fragments-root", type=Path, default=Path("docs"))
    parser.add_argument("--minimum-blue", type=int, default=25)
    parser.add_argument("--output", type=Path, help="write review queue CSV here instead of stdout")
    args = parser.parse_args()

    from PIL import Image

    candidates = build_edge_candidates(args.printed_csv, args.fragments_root)
    with Image.open(args.map_image) as source:
        evidence = score_blue_edges(candidates, source.convert("RGB"))
    queue = select_river_review(evidence, args.minimum_blue)
    if args.output:
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            write_river_review(queue, stream, args.map_image.name)
    else:
        write_river_review(queue, sys.stdout, args.map_image.name)
