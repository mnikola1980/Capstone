"""Command-line interface.

Usage:
    python -m architectural_design.cli generate --spec examples/studio_apartment.json --out output/

Produces, in the output directory:
    <name>_floorplan.png / .svg   - 2D floor plan
    <name>_3d.png                  - pseudo-3D massing view
    <name>_summary.json            - room list, areas, unplaced furniture report
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .furniture_placer import furnish
from .layout import generate_layout
from .renderer import render_floorplan_2d
from .renderer3d import render_isometric
from .spec import load_spec


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_") or "building"


def cmd_generate(args: argparse.Namespace) -> int:
    spec = load_spec(args.spec)
    building = generate_layout(spec.name, spec.width, spec.height, spec.rooms)
    building.units = spec.units
    unplaced_report = furnish(building)

    os.makedirs(args.out, exist_ok=True)
    slug = _slug(spec.name)

    png_path = os.path.join(args.out, f"{slug}_floorplan.png")
    svg_path = os.path.join(args.out, f"{slug}_floorplan.svg")
    render_floorplan_2d(building, png_path)
    render_floorplan_2d(building, svg_path)

    iso_path = None
    if not args.no_3d:
        iso_path = os.path.join(args.out, f"{slug}_3d.png")
        render_isometric(building, iso_path)

    summary = {
        "name": building.name,
        "width": building.width,
        "height": building.height,
        "units": building.units,
        "footprint_area": building.footprint_area(),
        "total_room_area": building.total_room_area(),
        "rooms": [
            {
                "id": r.id,
                "name": r.name,
                "type": r.room_type.value,
                "x": r.rect.x,
                "y": r.rect.y,
                "width": r.rect.w,
                "height": r.rect.h,
                "area": r.area,
                "doors": len(r.doors),
                "windows": len(r.windows),
                "furniture": [f.name for f in r.furniture],
            }
            for r in building.rooms
        ],
        "unplaced_furniture": unplaced_report,
        "outputs": {
            "floorplan_png": png_path,
            "floorplan_svg": svg_path,
            "isometric_png": iso_path,
        },
    }
    summary_path = os.path.join(args.out, f"{slug}_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Generated layout for '{building.name}' ({len(building.rooms)} rooms)")
    print(f"  Floor plan : {png_path}")
    print(f"  Floor plan : {svg_path}")
    if iso_path:
        print(f"  3D view    : {iso_path}")
    print(f"  Summary    : {summary_path}")
    if unplaced_report:
        print("  Note: some furniture did not fit and was skipped:")
        for room_id, items in unplaced_report.items():
            print(f"    - {room_id}: {', '.join(items)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="architectural_design",
        description="Generate architectural interior floor-plan layouts and visuals from a JSON spec.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a floor plan + visuals from a spec file")
    gen.add_argument("--spec", required=True, help="Path to a building spec JSON file")
    gen.add_argument("--out", default="output", help="Output directory (default: output/)")
    gen.add_argument("--no-3d", action="store_true", help="Skip the pseudo-3D isometric render")
    gen.set_defaults(func=cmd_generate)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
