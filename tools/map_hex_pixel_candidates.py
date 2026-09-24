"""Score confirmed Map A hex IDs from raster color; never certify terrain."""

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from tools.map_fragment_audit import HEX_FIELDS, _read_rows, audit_fragments
from tools.map_image_evidence import PixelImage, center_of


@dataclass(frozen=True)
class HexPixelCandidate:
    hex_id: str
    candidate: str
    median_red: int
    median_green: int
    median_blue: int
    green_fraction: float
    dark_fraction: float
    blue_fraction: float
    reviewed_terrain: str


def read_zone_center_queue(path: Path) -> list[str]:
    """Read geometric zone centers as candidate IDs, not confirmed map hexes."""
    expected = ("hex_id", "center_x", "center_y", "review_status")
    result = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != expected:
            raise ValueError(f"zone center queue columns must be {expected}")
        for row in reader:
            hex_id = row["hex_id"]
            if (row["review_status"] != "unconfirmed_zone_center"
                    or len(hex_id) != 4 or not hex_id.isascii() or not hex_id.isdigit()
                    or (int(row["center_x"]), int(row["center_y"])) != center_of(hex_id)):
                raise ValueError(f"invalid zone center: {row}")
            result.append(hex_id)
    if len(result) != len(set(result)):
        raise ValueError("duplicate zone center ID")
    return result


def classify_hex_pixels(
    median_rgb: tuple[int, int, int], green_fraction: float,
    dark_fraction: float, blue_fraction: float,
) -> str:
    """Return a deliberately coarse candidate or unresolved for other colors."""
    red, green, blue = median_rgb
    if red >= 230 and green >= 225 and blue >= 210:
        return "clear_candidate"
    if green_fraction >= 0.55 and red < 210:
        return "vegetation_candidate"
    if 180 <= red < 205 and green > red and blue_fraction >= 0.08 and dark_fraction < 0.1:
        return "marsh_candidate"
    if red < 205 and dark_fraction >= 0.18:
        return "major_city_candidate"
    return "unresolved"


def score_hex_pixels(
    hex_ids: list[str], image: PixelImage, reviewed: dict[str, str],
) -> list[HexPixelCandidate]:
    """Sample the central area of each known printed hex ID."""
    if image.size != (3300, 5100):
        raise ValueError(f"Map A image must be 3300x5100 pixels; got {image.size}")
    result = []
    for hex_id in hex_ids:
        x, y = center_of(hex_id)
        points = [(i, j) for i in range(x - 30, x + 31, 3)
                  for j in range(y - 35, y + 36, 3)
                  if 0 <= i < image.size[0] and 0 <= j < image.size[1]]
        if not points:
            raise ValueError(f"hex center outside Map A image: {hex_id}")
        pixels = [image.getpixel(point) for point in points]
        median_rgb = tuple(int(median(channel)) for channel in zip(*pixels))
        count = len(pixels)
        green_fraction = sum(g > r + 12 and g > b + 5 for r, g, b in pixels) / count
        dark_fraction = sum(max(r, g, b) < 130 for r, g, b in pixels) / count
        blue_fraction = sum(b > r + 20 and b > g + 5 and b > 120 for r, g, b in pixels) / count
        result.append(HexPixelCandidate(
            hex_id, classify_hex_pixels(median_rgb, green_fraction, dark_fraction, blue_fraction),
            *median_rgb, round(green_fraction, 4), round(dark_fraction, 4),
            round(blue_fraction, 4), reviewed.get(hex_id, ""),
        ))
    return result


def write_candidates(candidates: list[HexPixelCandidate], stream) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("hex_id", "candidate", "median_red", "median_green", "median_blue",
                     "green_fraction", "dark_fraction", "blue_fraction", "reviewed_terrain"))
    for row in candidates:
        writer.writerow((row.hex_id, row.candidate, row.median_red, row.median_green,
                         row.median_blue, row.green_fraction, row.dark_fraction,
                         row.blue_fraction, row.reviewed_terrain))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_image", type=Path)
    parser.add_argument("--printed-csv", type=Path,
                        default=Path("docs/map_a_printed_id_checks.csv"))
    parser.add_argument("--fragments-root", type=Path, default=Path("docs"))
    parser.add_argument("--zone-center-csv", type=Path,
                        help="score an unconfirmed VASSAL zone center queue instead")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from PIL import Image

    if args.zone_center_csv:
        hex_ids = read_zone_center_queue(args.zone_center_csv)
        reviewed = {}
    else:
        audit_fragments(args.fragments_root)
        with args.printed_csv.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != ("hex_id", "source_region", "review_scope"):
                raise ValueError(f"invalid printed ID columns: {args.printed_csv}")
            hex_ids = [row["hex_id"] for row in reader]
        if len(hex_ids) != len(set(hex_ids)) or any(len(h) != 4 or not h.isascii() or not h.isdigit()
                                                   for h in hex_ids):
            raise ValueError("printed IDs must be unique four-digit numbers")
        reviewed = {row["hex_id"]: row["terrain"]
                    for path in args.fragments_root.glob("map_a_*_hexes.csv")
                    for row in _read_rows(path, HEX_FIELDS, optional_last=True)}
        if reviewed.keys() - set(hex_ids):
            raise ValueError("reviewed hex missing from printed ID list")
    with Image.open(args.map_image) as source:
        candidates = score_hex_pixels(hex_ids, source.convert("RGB"), reviewed)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        write_candidates(candidates, stream)
    print("candidates", dict(Counter(row.candidate for row in candidates)))
    print("reviewed", dict(Counter((row.reviewed_terrain, row.candidate) for row in candidates
                                   if row.reviewed_terrain)))
    print(f"wrote {len(candidates)} hex candidates to {args.output}")
