"""Command-line interface.

    # generated plan from a weighted room list
    python -m architectural_design.cli generate --spec examples/studio_apartment.json --out output/

    # surveyed plan: the 1931 house, all three storeys, heritage drawing style
    python -m architectural_design.cli generate --spec examples/rhijngeesterstraatweg_143.json --out output/

    # daylight & orientation report only
    python -m architectural_design.cli daylight --spec examples/rhijngeesterstraatweg_143.json

Outputs written to the output directory:
    <name>_<level>_<storey>.png / .svg   - 2D floor plan per storey
    <name>_3d.png                         - pseudo-3D massing view
    <name>_summary.json                   - rooms, areas, daylight, orientation
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import daylight as daylight_mod
from .furniture_placer import furnish
from .layout import building_from_spec
from .renderer import render_daylight_plan, render_floorplan_2d
from .renderer3d import render_isometric
from .spec import load_spec


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_") or "building"


def _build(args) -> tuple:
    spec = load_spec(args.spec)
    building = building_from_spec(spec)
    style = getattr(args, "style", None) or building.style
    building.style = style
    unplaced = furnish(building, style=style)
    return spec, building, style, unplaced


def cmd_generate(args: argparse.Namespace) -> int:
    spec, building, style, unplaced_report = _build(args)
    os.makedirs(args.out, exist_ok=True)
    slug = _slug(spec.name)

    plan_paths, daylight_paths = [], []
    storeys = building.storeys
    for storey in storeys:
        sslug = _slug(storey.name)
        base = f"{slug}_{storey.level}_{sslug}" if len(storeys) > 1 else f"{slug}_floorplan"
        png = os.path.join(args.out, base + ".png")
        svg = os.path.join(args.out, base + ".svg")
        render_floorplan_2d(building, png, storey=storey, style=style)
        render_floorplan_2d(building, svg, storey=storey, style=style)
        plan_paths += [png, svg]
        if not args.no_daylight_plan:
            dpath = os.path.join(args.out, base + "_daylight.png")
            render_daylight_plan(building, dpath, storey=storey)
            daylight_paths.append(dpath)

    iso_path = None
    if not args.no_3d:
        iso_path = os.path.join(args.out, f"{slug}_3d.png")
        render_isometric(building, iso_path, storey=storeys[0], style=style)

    report = daylight_mod.analyse_building(building)
    day_summary = daylight_mod.summarise(building, report)

    summary = {
        "name": building.name,
        "address": building.address,
        "year_built": building.year_built,
        "architect": building.architect,
        "style": style,
        "units": building.units,
        "width": building.width,
        "depth": building.height,
        "footprint_area": round(building.footprint_area(), 2),
        "gross_floor_area": round(building.total_floor_area(), 2),
        "north_angle_deg": building.north_angle_deg,
        "orientation": {s: building.side_compass(s) for s in ("N", "E", "S", "W")},
        "blind_sides": building.blind_sides,
        "provenance": getattr(spec, "provenance", {}),
        "storeys": [
            {
                "name": s.name,
                "level": s.level,
                "ceiling_height": s.ceiling_height,
                "area": round(s.area, 2),
                "rooms": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "type": r.room_type.value,
                        "x": r.rect.x, "y": r.rect.y,
                        "width": r.rect.w, "height": r.rect.h,
                        "area": round(r.area, 2),
                        "doors": len(r.doors),
                        "windows": len(r.windows),
                        "glazed_area": round(r.glazed_area, 2),
                        "furniture": [f.name for f in r.furniture],
                        "note": r.note,
                    }
                    for r in s.rooms
                ],
            }
            for s in storeys
        ],
        "daylight": {
            "summary": day_summary,
            "rooms": [
                {
                    "room": d.name, "storey": d.storey,
                    "floor_area": round(d.floor_area, 2),
                    "glazed_area": round(d.glazed_area, 2),
                    "ratio": round(d.ratio, 4),
                    "facing": d.orientations, "sun": d.sun, "rating": d.rating,
                }
                for d in report
            ],
        },
        "unplaced_furniture": unplaced_report,
        "outputs": {"plans": plan_paths, "daylight_plans": daylight_paths,
                    "isometric_png": iso_path},
    }
    summary_path = os.path.join(args.out, f"{slug}_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    n_rooms = len(building.all_rooms())
    print(f"Generated '{building.name}' - {len(storeys)} storey(s), {n_rooms} rooms, style={style}")
    if building.address:
        print(f"  {building.address}" + (f" ({building.year_built})" if building.year_built else ""))
    facing = ", ".join(f"{s}->{building.side_compass(s)}" for s in ("N", "E", "S", "W"))
    print(f"  Orientation: {facing}")
    for p in plan_paths:
        print(f"  Plan       : {p}")
    for p in daylight_paths:
        print(f"  Daylight   : {p}")
    if iso_path:
        print(f"  3D view    : {iso_path}")
    print(f"  Summary    : {summary_path}")
    if args.daylight:
        print()
        print(daylight_mod.format_report(building, report))
    if unplaced_report:
        print("  Note: some furniture did not fit and was skipped:")
        for room_id, items in unplaced_report.items():
            print(f"    - {room_id}: {', '.join(items)}")
    return 0


def cmd_daylight(args: argparse.Namespace) -> int:
    _, building, _, _ = _build(args)
    print(daylight_mod.format_report(building))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="architectural_design",
        description="Generate architectural interior floor-plan layouts and visuals from a JSON spec.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate floor plans + visuals from a spec file")
    gen.add_argument("--spec", required=True, help="Path to a building spec JSON file")
    gen.add_argument("--out", default="output", help="Output directory (default: output/)")
    gen.add_argument("--no-3d", action="store_true", help="Skip the pseudo-3D isometric render")
    gen.add_argument("--style", choices=["modern", "heritage"], default=None,
                     help="Drawing style (default: the spec's own style)")
    gen.add_argument("--daylight", action="store_true",
                     help="Also print the daylight & orientation report")
    gen.add_argument("--no-daylight-plan", action="store_true",
                     help="Skip rendering the daylight & orientation plan per storey")
    gen.set_defaults(func=cmd_generate)

    day = sub.add_parser("daylight", help="Print the daylight & orientation report for a spec")
    day.add_argument("--spec", required=True)
    day.add_argument("--style", choices=["modern", "heritage"], default=None)
    day.set_defaults(func=cmd_daylight)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
