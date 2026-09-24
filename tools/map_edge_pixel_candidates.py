"""Score known Map A edge candidates from pixels; scores are review hints only."""

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

from tools.map_edge_candidates import EdgeCandidate, build_edge_candidates
from tools.map_image_evidence import PixelImage, center_of


@dataclass(frozen=True)
class EdgePixelCandidate:
    hex_id: str
    direction: str
    neighbor_id: str
    review_status: str
    crossing_features: str
    blue_pixels: int
    pink_pixels: int
    dark_pixels: int
    wide_signal_pixels: int
    border_signal_pixels: int
    route_crossing_score: int
    signals: tuple[str, ...]


def score_edge_pixels(
    candidates: list[EdgeCandidate], image: PixelImage, threshold: int = 25,
) -> list[EdgePixelCandidate]:
    """Count color signals near each edge midpoint and in a wider quiet check."""
    if image.size != (3300, 5100):
        raise ValueError(f"Map A image must be 3300x5100 pixels; got {image.size}")
    if threshold < 1:
        raise ValueError("threshold must be positive")

    result = []
    for edge in candidates:
        x1, y1 = center_of(edge.hex_id)
        x2, y2 = center_of(edge.neighbor_id)
        mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
        blue = pink = dark = wide_signal = 0
        for x in range(max(0, mid_x - 25), min(image.size[0], mid_x + 26)):
            for y in range(max(0, mid_y - 25), min(image.size[1], mid_y + 26)):
                red, green, blue_channel = image.getpixel((x, y))
                is_blue = blue_channel > red + 20 and blue_channel > green + 5 and blue_channel > 120
                is_pink = red - green > 8 and red - blue_channel > 10 and red > 180 and green > 140
                is_dark = max(red, green, blue_channel) < 100
                wide_signal += is_blue + is_pink + is_dark
                if abs(x - mid_x) <= 14 and abs(y - mid_y) <= 14:
                    blue += is_blue
                    pink += is_pink
                    dark += is_dark
        dx, dy = x2 - x1, y2 - y1
        distance = math.hypot(dx, dy)
        along_x, along_y = -dy / distance, dx / distance
        across_x, across_y = dx / distance, dy / distance
        center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
        border_signal = 0
        for along in range(-53, 54, 2):
            for across in range(-6, 7, 2):
                x = round(center_x + along_x * along + across_x * across)
                y = round(center_y + along_y * along + across_y * across)
                if not (0 <= x < image.size[0] and 0 <= y < image.size[1]):
                    continue
                red, green, blue_channel = image.getpixel((x, y))
                border_signal += (
                    (blue_channel > red + 20 and blue_channel > green + 5 and blue_channel > 120)
                    + (red - green > 8 and red - blue_channel > 10 and red > 180 and green > 140)
                    + (max(red, green, blue_channel) < 100)
                )
        route_score = 0
        for along in range(-30, 31, 2):
            side_counts = []
            for sign in (-1, 1):
                side_count = 0
                for distance_from_border in range(10, 34, 3):
                    for offset in (-2, 0, 2):
                        x = round(center_x + along_x * (along + offset)
                                  + across_x * sign * distance_from_border)
                        y = round(center_y + along_y * (along + offset)
                                  + across_y * sign * distance_from_border)
                        if 0 <= x < image.size[0] and 0 <= y < image.size[1]:
                            side_count += max(image.getpixel((x, y))) < 200
                side_counts.append(side_count)
            route_score = max(route_score, min(side_counts))
        signals = []
        if blue >= threshold:
            signals.append("river_candidate")
        if pink >= 5:
            signals.append("road_candidate")
        if dark >= 10:
            signals.append("rail_or_primary_candidate")
        if route_score >= 4:
            signals.append("route_crossing_candidate")
        if wide_signal <= 10 and route_score < 4:
            signals.append("no_feature_candidate")
            if border_signal <= 5:
                signals.append("strong_no_feature_candidate")
        result.append(EdgePixelCandidate(
            edge.hex_id, edge.direction, edge.neighbor_id,
            edge.review_status, edge.crossing_features, blue, pink, dark,
            wide_signal, border_signal, route_score, tuple(signals),
        ))
    return result


def evaluate_reviewed(candidates: list[EdgePixelCandidate]) -> dict[str, dict[str, int]]:
    """Count in-sample detections against manually reviewed edges."""
    truth = {
        "river_candidate": lambda features: "river" in features,
        "road_candidate": lambda features: "secondary_road" in features,
        "rail_or_primary_candidate": lambda features: (
            "railroad" in features or "primary_road" in features
        ),
        "no_feature_candidate": lambda features: features == "none",
        "strong_no_feature_candidate": lambda features: features == "none",
        "route_crossing_candidate": lambda features: (
            "secondary_road" in features or "primary_road" in features
            or "railroad" in features
        ),
    }
    metrics = {name: {"true_positive": 0, "false_positive": 0, "false_negative": 0}
               for name in truth}
    for edge in candidates:
        if edge.review_status != "reviewed":
            continue
        for name, matches in truth.items():
            detected = name in edge.signals
            actual = matches(edge.crossing_features)
            if detected and actual:
                metrics[name]["true_positive"] += 1
            elif detected:
                metrics[name]["false_positive"] += 1
            elif actual:
                metrics[name]["false_negative"] += 1
    return metrics


def write_candidates(candidates: list[EdgePixelCandidate], stream) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("hex_id", "direction", "neighbor_id", "review_status",
                     "crossing_features", "blue_pixels_29x29", "pink_pixels_29x29",
                     "dark_pixels_29x29", "color_pixels_51x51", "border_signal_pixels",
                     "route_crossing_score", "signals"))
    for edge in candidates:
        writer.writerow((edge.hex_id, edge.direction, edge.neighbor_id,
                         edge.review_status, edge.crossing_features,
                         edge.blue_pixels, edge.pink_pixels, edge.dark_pixels,
                         edge.wide_signal_pixels, edge.border_signal_pixels,
                         edge.route_crossing_score,
                         ";".join(edge.signals)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_image", type=Path)
    parser.add_argument("--printed-csv", type=Path,
                        default=Path("docs/map_a_printed_id_checks.csv"))
    parser.add_argument("--fragments-root", type=Path, default=Path("docs"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from PIL import Image

    edges = build_edge_candidates(args.printed_csv, args.fragments_root)
    with Image.open(args.map_image) as source:
        scores = score_edge_pixels(edges, source.convert("RGB"))
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        write_candidates(scores, stream)
    for name, counts in evaluate_reviewed(scores).items():
        print(name, counts)
    print(f"wrote {len(scores)} edge candidates to {args.output}")
