"""Make a visual sheet for manual review of unverified Map A hexsides."""

import argparse
from pathlib import Path

from tools.map_edge_candidates import EdgeCandidate, build_edge_candidates
from tools.map_image_evidence import center_of


def select_review_edges(candidates: list[EdgeCandidate], columns: tuple[int, int],
                        rows: tuple[int, int]) -> list[EdgeCandidate]:
    """Return unreviewed edges touching the inclusive column/row rectangle."""
    if columns[0] > columns[1] or rows[0] > rows[1]:
        raise ValueError("region bounds must be ascending")

    def inside(hex_id: str) -> bool:
        column, row = int(hex_id[:2]), int(hex_id[2:])
        return columns[0] <= column <= columns[1] and rows[0] <= row <= rows[1]

    return [edge for edge in candidates if edge.review_status == "unreviewed"
            and (inside(edge.hex_id) or inside(edge.neighbor_id))]


def crop_box(edge: EdgeCandidate) -> tuple[int, int, int, int]:
    """Include both hex centers and the full shared side around its midpoint."""
    source_x, source_y = center_of(edge.hex_id)
    target_x, target_y = center_of(edge.neighbor_id)
    mid_x, mid_y = (source_x + target_x) // 2, (source_y + target_y) // 2
    return mid_x - 90, mid_y - 75, mid_x + 90, mid_y + 75


def render_sheet(candidates: list[EdgeCandidate], image_path: Path, output_path: Path) -> None:
    """Render source image crops with an open ring at each geometric midpoint."""
    if not candidates:
        raise ValueError("no unreviewed edges in selected region")

    from PIL import Image, ImageDraw

    with Image.open(image_path) as source:
        if source.size != (3300, 5100):
            raise ValueError(f"Map A image must be 3300x5100 pixels; got {source.size}")
        source = source.convert("RGB")
        columns = min(3, len(candidates))
        sheet = Image.new("RGB", (columns * 380, ((len(candidates) + columns - 1) // columns) * 350),
                          "white")
        draw = ImageDraw.Draw(sheet)
        for index, edge in enumerate(candidates):
            left = (index % columns) * 380 + 10
            top = (index // columns) * 350 + 40
            crop = source.crop(crop_box(edge)).resize((360, 300))
            sheet.paste(crop, (left, top))
            draw.text((left, top - 25), f"{edge.hex_id} {edge.direction} {edge.neighbor_id}",
                      fill="black")
            draw.ellipse((left + 173, top + 143, left + 187, top + 157),
                         outline=(225, 0, 0), width=2)
        sheet.save(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_image", type=Path)
    parser.add_argument("--columns", nargs=2, type=int, required=True, metavar=("MIN", "MAX"))
    parser.add_argument("--rows", nargs=2, type=int, required=True, metavar=("MIN", "MAX"))
    parser.add_argument("--printed-csv", type=Path, default=Path("docs/map_a_printed_id_checks.csv"))
    parser.add_argument("--fragments-root", type=Path, default=Path("docs"))
    parser.add_argument("--max-edges", type=int, default=36)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidates = build_edge_candidates(args.printed_csv, args.fragments_root)
    selected = select_review_edges(candidates, tuple(args.columns), tuple(args.rows))
    if len(selected) > args.max_edges:
        parser.error(f"selected {len(selected)} edges; narrow the region or raise --max-edges")
    render_sheet(selected, args.map_image, args.output)
    print(f"review sheet: {len(selected)} unreviewed edges -> {args.output}")
