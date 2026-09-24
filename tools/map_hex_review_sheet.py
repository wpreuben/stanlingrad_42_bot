"""Render Map A pixel candidates as a contact sheet for manual map review."""

import argparse
import csv
from pathlib import Path

from tools.map_hex_pixel_candidates import HexPixelCandidate
from tools.map_image_evidence import center_of


def read_candidates(path: Path) -> list[HexPixelCandidate]:
    result = []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            result.append(HexPixelCandidate(
                row["hex_id"], row["candidate"],
                int(row["median_red"]), int(row["median_green"]),
                int(row["median_blue"]), float(row["green_fraction"]),
                float(row["dark_fraction"]), float(row["blue_fraction"]),
                row["reviewed_terrain"],
            ))
    return result


def select_hexes(rows: list[HexPixelCandidate], candidate: str) -> list[HexPixelCandidate]:
    """Show highest blue coverage first when reviewing coast and water."""
    return sorted((row for row in rows if row.candidate == candidate),
                  key=lambda row: (-row.blue_fraction, row.hex_id))


def render_sheet(rows: list[HexPixelCandidate], image_path: Path, output_path: Path) -> None:
    if not rows:
        raise ValueError("no hex candidates selected")
    from PIL import Image, ImageDraw

    with Image.open(image_path) as source:
        if source.size != (3300, 5100):
            raise ValueError(f"Map A image must be 3300x5100 pixels; got {source.size}")
        source = source.convert("RGB")
        columns = min(3, len(rows))
        sheet = Image.new("RGB", (columns * 380, ((len(rows) + columns - 1) // columns) * 370),
                          "white")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(rows):
            center_x, center_y = center_of(row.hex_id)
            left = (index % columns) * 380 + 10
            top = (index // columns) * 370 + 40
            crop = source.crop((center_x - 90, center_y - 80,
                                center_x + 90, center_y + 80)).resize((360, 320))
            sheet.paste(crop, (left, top))
            draw.text((left, top - 25),
                      f"{row.hex_id} | {row.candidate} | blue {row.blue_fraction:.2f}",
                      fill="black")
            draw.ellipse((left + 172, top + 152, left + 188, top + 168),
                         outline=(225, 0, 0), width=2)
        sheet.save(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_image", type=Path)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--candidate", default="unresolved")
    parser.add_argument("--max-hexes", type=int, default=36)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected = select_hexes(read_candidates(args.candidates), args.candidate)
    if len(selected) > args.max_hexes:
        parser.error(f"selected {len(selected)} hexes; narrow the filter or raise --max-hexes")
    render_sheet(selected, args.map_image, args.output)
    print(f"review sheet: {len(selected)} hexes -> {args.output}")
