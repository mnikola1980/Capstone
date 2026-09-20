"""
Heuristic furniture placement.

For each room, candidate furniture items (from `furniture_catalog`) are
tried against the room's walls in priority order using a simple
"perimeter skyline" strategy: walk each wall, keep a cursor of how much of
it is already used, and place the next item's long edge flush against the
wall wherever it fits without overlapping previously placed furniture,
doors (plus swing clearance) or windows. Items that cannot be placed
anywhere are silently skipped (tracked on `Room.unplaced` for callers who
care), which is normal for small rooms.

This is intentionally simple (no true bin-packing/ILP) but is fast,
deterministic, and produces plausible, non-overlapping layouts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .furniture_catalog import FurnitureTemplate, catalog_for
from .models import Building, Door, FurnitureItem, Rect, Room

INSET = 0.35          # gap kept between furniture and the wall face (feet)
DOOR_CLEARANCE = 2.5   # keep this much clear space in front of a door swing


def _wall_length(room: Room, side: str) -> float:
    return room.rect.w if side in ("N", "S") else room.rect.h


def _blocked_intervals(room: Room, side: str) -> List[Tuple[float, float]]:
    """Return [start,end] intervals (along the wall, local coords) blocked by
    doors/windows on this wall, expanded by clearance for doors."""
    blocked = []
    for d in room.doors:
        if d.side != side:
            continue
        half = d.width / 2 + DOOR_CLEARANCE
        blocked.append((d.position - half, d.position + half))
    for w in room.windows:
        if w.side != side:
            continue
        half = w.width / 2 + 0.2
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


def _place_on_wall(room: Room, side: str, item_w: float, item_d: float) -> Rect | None:
    """Try to place a rectangle of footprint (item_w along wall) x (item_d away
    from wall) flush against `side`, scanning left-to-right for the first
    gap where it fits without hitting doors/windows or existing furniture."""
    wall_len = _wall_length(room, side)
    if item_w > wall_len - 2 * INSET:
        return None
    blocked = _blocked_intervals(room, side)

    r = room.rect
    step = 0.5
    pos = INSET
    while pos + item_w <= wall_len - INSET + 1e-6:
        if _fits((pos, pos + item_w), blocked, wall_len):
            candidate = _build_rect(r, side, pos, item_w, item_d)
            if not any(candidate.overlaps(f.rect) for f in room.furniture):
                return candidate
        pos += step
    return None


def _build_rect(room_rect: Rect, side: str, pos_along: float, item_w: float, item_d: float) -> Rect:
    r = room_rect
    if side == "S":
        return Rect(r.x + pos_along, r.y + INSET, item_w, item_d)
    if side == "N":
        return Rect(r.x + pos_along, r.y2 - INSET - item_d, item_w, item_d)
    if side == "W":
        return Rect(r.x + INSET, r.y + pos_along, item_d, item_w)
    if side == "E":
        return Rect(r.x2 - INSET - item_d, r.y + pos_along, item_d, item_w)
    raise ValueError(f"unknown side {side}")


def _try_place_item(room: Room, tmpl: FurnitureTemplate) -> bool:
    sides_by_length = sorted(["S", "N", "W", "E"], key=lambda s: -_wall_length(room, s))
    for side in sides_by_length:
        for w, d in ((tmpl.width, tmpl.depth), (tmpl.depth, tmpl.width)):
            rect = _place_on_wall(room, side, w, d)
            if rect is not None:
                room.furniture.append(
                    FurnitureItem(name=tmpl.name, rect=rect, color=tmpl.color, kind=tmpl.kind)
                )
                return True
    return False


def furnish_room(room: Room) -> List[str]:
    """Populate room.furniture in place. Returns names of items that didn't fit."""
    unplaced = []
    for tmpl in catalog_for(room.room_type):
        if room.area < tmpl.min_room_area:
            unplaced.append(tmpl.name)
            continue
        if not _try_place_item(room, tmpl):
            unplaced.append(tmpl.name)
    return unplaced


def furnish(building: Building) -> dict:
    """Furnish every room in the building. Returns {room_id: [unplaced item names]}."""
    report = {}
    for room in building.rooms:
        unplaced = furnish_room(room)
        if unplaced:
            report[room.id] = unplaced
    return report
