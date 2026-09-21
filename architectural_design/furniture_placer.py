"""
Heuristic furniture placement.

For each room, candidate furniture items (from `furniture_catalog`) are
tried against the room's walls in priority order using a simple
"perimeter skyline" strategy: walk each wall, keep a cursor of how much of
it is already used, and place the next item's long edge flush against the
wall wherever it fits without overlapping previously placed furniture,
doors (plus swing clearance) or windows. Items that cannot be placed
anywhere are skipped and reported, which is normal for small rooms.

This is intentionally simple (no true bin-packing/ILP) but is fast,
deterministic, and produces plausible, non-overlapping layouts.

All clearances are defined in metres and scaled to the building's unit.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .furniture_catalog import FurnitureTemplate, catalog_for
from .models import FT_PER_M, Building, FurnitureItem, Rect, Room

INSET_M = 0.107           # gap kept between furniture and the wall face
DOOR_CLEARANCE_M = 0.762   # clear space kept in front of a door swing


def _scale(units: str) -> float:
    return FT_PER_M if units == "ft" else 1.0


def _wall_length(room: Room, side: str) -> float:
    return room.rect.w if side in ("N", "S") else room.rect.h


def _blocked_intervals(room: Room, side: str, door_clearance: float) -> List[Tuple[float, float]]:
    """Intervals along the wall (local coords) blocked by doors/windows on
    this wall, doors expanded by swing clearance."""
    blocked = []
    for d in room.doors:
        if d.side != side:
            continue
        half = d.width / 2 + door_clearance
        blocked.append((d.position - half, d.position + half))
    for w in room.windows:
        if w.side != side:
            continue
        # A window only blocks furniture that would rise above its sill.
        half = w.width / 2 + 0.06 * (door_clearance / DOOR_CLEARANCE_M or 1.0)
        blocked.append((w.position - half, w.position + half))
    return blocked


def _fits(interval: Tuple[float, float], blocked: List[Tuple[float, float]], wall_len: float) -> bool:
    s, e = interval
    if s < -1e-6 or e > wall_len + 1e-6:
        return False
    for bs, be in blocked:
        if s < be and bs < e:
            return False
    return True


def _build_rect(room_rect: Rect, side: str, pos_along: float, item_w: float, item_d: float, inset: float) -> Rect:
    r = room_rect
    if side == "S":
        return Rect(r.x + pos_along, r.y + inset, item_w, item_d)
    if side == "N":
        return Rect(r.x + pos_along, r.y2 - inset - item_d, item_w, item_d)
    if side == "W":
        return Rect(r.x + inset, r.y + pos_along, item_d, item_w)
    if side == "E":
        return Rect(r.x2 - inset - item_d, r.y + pos_along, item_d, item_w)
    raise ValueError(f"unknown side {side}")


def _place_on_wall(
    room: Room, side: str, item_w: float, item_d: float, inset: float, door_clearance: float
) -> Optional[Rect]:
    """Try to place a footprint (item_w along the wall, item_d away from it)
    flush against `side`, scanning for the first gap where it fits without
    hitting doors, windows or existing furniture."""
    wall_len = _wall_length(room, side)
    if item_w > wall_len - 2 * inset:
        return None
    if item_d > (room.rect.h if side in ("N", "S") else room.rect.w) - inset:
        return None
    blocked = _blocked_intervals(room, side, door_clearance)

    step = max(0.05, inset)
    pos = inset
    while pos + item_w <= wall_len - inset + 1e-6:
        if _fits((pos, pos + item_w), blocked, wall_len):
            candidate = _build_rect(room.rect, side, pos, item_w, item_d, inset)
            if not any(candidate.overlaps(f.rect) for f in room.furniture):
                return candidate
        pos += step
    return None


def _try_place_item(room: Room, tmpl: FurnitureTemplate, inset: float, door_clearance: float) -> bool:
    sides_by_length = sorted(["S", "N", "W", "E"], key=lambda s: -_wall_length(room, s))
    for side in sides_by_length:
        for w, d in ((tmpl.width, tmpl.depth), (tmpl.depth, tmpl.width)):
            rect = _place_on_wall(room, side, w, d, inset, door_clearance)
            if rect is not None:
                room.furniture.append(
                    FurnitureItem(name=tmpl.name, rect=rect, color=tmpl.color, kind=tmpl.kind)
                )
                return True
    return False


def furnish_room(room: Room, units: str = "ft", style: str = "modern") -> List[str]:
    """Populate room.furniture in place. Returns names of items that didn't fit."""
    scale = _scale(units)
    inset = INSET_M * scale
    door_clearance = DOOR_CLEARANCE_M * scale
    unplaced = []
    for tmpl in catalog_for(room.room_type, units=units, style=style):
        if room.area < tmpl.min_room_area:
            unplaced.append(tmpl.name)
            continue
        if not _try_place_item(room, tmpl, inset, door_clearance):
            unplaced.append(tmpl.name)
    return unplaced


def furnish(building: Building, style: Optional[str] = None) -> dict:
    """Furnish every room on every storey. Returns {room_id: [unplaced names]}."""
    style = style if style is not None else getattr(building, "style", "modern")
    units = building.units
    report = {}
    for room in building.all_rooms():
        unplaced = furnish_room(room, units=units, style=style)
        if unplaced:
            report[room.id] = unplaced
    return report
