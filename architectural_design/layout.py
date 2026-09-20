"""
Floor-plan layout generation.

Uses a recursive "slicing" (guillotine) partition of the building footprint,
similar in spirit to a squarified treemap: at each step the current
rectangle is split once, perpendicular to its longer side, into two groups
of rooms whose combined weight matches the split ratio. This guarantees:

  * every room is an axis-aligned rectangle
  * rooms never overlap
  * the union of all rooms exactly tiles the building footprint
  * room areas are proportional to their requested `weight`

After the rectangles are assigned, adjacency between rooms is computed from
shared wall segments, a minimum-spanning "circulation" tree over that
adjacency graph decides where interior doors go (so every room is reachable
from the entry), and windows are placed on any wall segment that lies on the
building's exterior boundary.
"""

from __future__ import annotations

import itertools
import math
from typing import List, Optional, Sequence, Tuple

from .models import Building, Door, Rect, Room, RoomSpec, RoomType, Window

_EPS = 1e-6


def _split_group(specs: Sequence[RoomSpec]) -> Tuple[List[RoomSpec], List[RoomSpec]]:
    """Split a list of specs into two contiguous groups whose weight sums are as
    close as possible to half the total (keeps original order, which keeps
    the recursion deterministic and gives more compact resulting shapes)."""
    total = sum(s.weight for s in specs)
    target = total / 2.0
    best_i, best_diff = 1, float("inf")
    running = 0.0
    for i, s in enumerate(specs):
        running += s.weight
        diff = abs(running - target)
        if diff < best_diff and 0 < i + 1 < len(specs) + 1 and running < total - _EPS:
            best_diff = diff
            best_i = i + 1
    if best_i <= 0 or best_i >= len(specs):
        best_i = max(1, len(specs) // 2)
    return list(specs[:best_i]), list(specs[best_i:])


def _partition(rect: Rect, specs: Sequence[RoomSpec]) -> List[Tuple[RoomSpec, Rect]]:
    if len(specs) == 1:
        return [(specs[0], rect)]

    group_a, group_b = _split_group(specs)
    weight_a = sum(s.weight for s in group_a)
    weight_b = sum(s.weight for s in group_b)
    ratio = weight_a / (weight_a + weight_b)

    # Cut perpendicular to the longer side, so rooms stay closer to square.
    if rect.w >= rect.h:
        split_w = rect.w * ratio
        rect_a = Rect(rect.x, rect.y, split_w, rect.h)
        rect_b = Rect(rect.x + split_w, rect.y, rect.w - split_w, rect.h)
    else:
        split_h = rect.h * ratio
        rect_a = Rect(rect.x, rect.y, rect.w, split_h)
        rect_b = Rect(rect.x, rect.y + split_h, rect.w, rect.h - split_h)

    return _partition(rect_a, group_a) + _partition(rect_b, group_b)


def _make_room_id(name: str, used: set) -> str:
    base = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_") or "room"
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def _build_adjacency(rooms: List[Room]) -> List[Tuple[int, int, float, str, float, float]]:
    """Return list of (i, j, shared_length, side_of_i, lo, hi) for every pair of
    rooms that share a wall segment, sorted by shared length descending."""
    edges = []
    for i, j in itertools.combinations(range(len(rooms)), 2):
        shared = rooms[i].rect.shared_edge(rooms[j].rect)
        if shared:
            side, lo, hi = shared
            edges.append((i, j, hi - lo, side, lo, hi))
    edges.sort(key=lambda e: -e[2])
    return edges


def _union_find(n: int):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
        return True

    return find, union


def _opposite(side: str) -> str:
    return {"N": "S", "S": "N", "E": "W", "W": "E"}[side]


# Private rooms should generally open onto a hallway/living space through a
# single door, not become a thoroughfare with a door to every neighbor.
# Public/circulation rooms are left effectively uncapped.
_PRIVATE_ROOM_TYPES = {
    RoomType.BEDROOM,
    RoomType.MASTER_BEDROOM,
    RoomType.BATHROOM,
    RoomType.OFFICE,
    RoomType.CLOSET,
    RoomType.LAUNDRY,
}
_MAX_DOORS_PRIVATE = 1
_MAX_DOORS_PUBLIC = 99


def _max_doors(room: Room) -> int:
    return _MAX_DOORS_PRIVATE if room.room_type in _PRIVATE_ROOM_TYPES else _MAX_DOORS_PUBLIC


def _add_door_between(rooms: List[Room], i: int, j: int, side: str, lo: float, hi: float, length: float) -> None:
    mid = (lo + hi) / 2.0
    door_width = min(3.0, length * 0.6)
    room_i, room_j = rooms[i], rooms[j]
    pos_i = mid - room_i.rect.y if side in ("E", "W") else mid - room_i.rect.x
    pos_j = mid - room_j.rect.y if side in ("E", "W") else mid - room_j.rect.x
    room_i.doors.append(Door(side=side, position=pos_i, width=door_width, connects_to=room_j.id))
    room_j.doors.append(
        Door(side=_opposite(side), position=pos_j, width=door_width, connects_to=room_i.id)
    )


def _add_interior_doors(rooms: List[Room], min_shared: float = 3.5) -> None:
    """Connect rooms into a single reachable graph by adding a door across the
    widest shared wall on a minimum-spanning tree of the adjacency graph.

    Runs in two passes: first a "polite" pass that respects a one-door cap
    on private rooms (bedrooms, bathrooms, offices, ...) so they don't end
    up as a hallway-substitute with doors on three walls; then a fallback
    pass, ignoring that cap, for any room the first pass left unreachable
    (connectivity always wins over the cap).
    """
    edges = _build_adjacency(rooms)
    edges = [e for e in edges if e[2] >= min_shared]
    find, union = _union_find(len(rooms))
    door_count = [0] * len(rooms)

    def connect(i, j, length, side, lo, hi):
        union(i, j)
        _add_door_between(rooms, i, j, side, lo, hi, length)
        door_count[i] += 1
        door_count[j] += 1

    deferred = []
    for i, j, length, side, lo, hi in edges:
        if find(i) == find(j):
            continue
        if door_count[i] >= _max_doors(rooms[i]) or door_count[j] >= _max_doors(rooms[j]):
            deferred.append((i, j, length, side, lo, hi))
            continue
        connect(i, j, length, side, lo, hi)

    # Fallback: force-connect any still-isolated components, ignoring caps.
    for i, j, length, side, lo, hi in deferred:
        if find(i) == find(j):
            continue
        connect(i, j, length, side, lo, hi)


# Rooms most plausible to hold the front door, most-preferred first. Any
# room type not listed falls into the lowest-preference tier so the entry
# only lands somewhere unexpected (e.g. a bedroom) if nothing better touches
# the front wall.
_ENTRY_PREFERENCE = {
    RoomType.ENTRY: 0,
    RoomType.HALLWAY: 1,
    RoomType.LIVING_ROOM: 2,
    RoomType.DINING_ROOM: 3,
    RoomType.KITCHEN: 4,
    RoomType.OFFICE: 4,
}


def _add_exterior_features(building: Building, front_side: str = "S") -> None:
    """Give every room with `needs_window` a window on any exterior wall it
    touches, and ensure exactly one exterior door exists (on the front side)
    so the building has an entrance from outside. Prefers placing that door
    in an entry/hallway/living-type room over e.g. a bedroom or bathroom,
    breaking ties by whichever candidate has the longest front-facing wall."""
    best_entry: Optional[Tuple[Room, str, float, float]] = None
    best_key: Optional[Tuple[int, float]] = None
    for room in building.rooms:
        r = room.rect
        # Exterior boundary checks per side.
        sides = {
            "S": (r.y <= _EPS, r.x, r.x2),
            "N": (abs(r.y2 - building.height) <= _EPS, r.x, r.x2),
            "W": (r.x <= _EPS, r.y, r.y2),
            "E": (abs(r.x2 - building.width) <= _EPS, r.y, r.y2),
        }
        for side, (is_exterior, lo, hi) in sides.items():
            if not is_exterior:
                continue
            length = hi - lo
            if side != front_side:
                continue
            preference = _ENTRY_PREFERENCE.get(room.room_type, 9)
            key = (preference, -length)  # lower preference tier wins, then longer wall
            if best_key is None or key < best_key:
                best_key = key
                best_entry = (room, side, lo, hi)

    for room in building.rooms:
        spec_needs_window = getattr(room, "_needs_window", True)
        if not spec_needs_window:
            continue
        r = room.rect
        sides = {
            "S": r.y <= _EPS,
            "N": abs(r.y2 - building.height) <= _EPS,
            "W": r.x <= _EPS,
            "E": abs(r.x2 - building.width) <= _EPS,
        }
        for side, is_exterior in sides.items():
            if not is_exterior:
                continue
            length = r.w if side in ("N", "S") else r.h
            if length < 3.5:
                continue
            width = min(4.0, length * 0.5)
            pos = length / 2.0
            room.windows.append(Window(side=side, position=pos, width=width))

    if best_entry is not None:
        room, side, lo, hi = best_entry
        length = hi - lo
        origin = room.rect.x if side in ("N", "S") else room.rect.y
        pos = (lo + hi) / 2.0 - origin
        room.doors.append(Door(side=side, position=pos, width=min(3.5, length * 0.5), connects_to=None))


def generate_layout(name: str, width: float, height: float, specs: Sequence[RoomSpec]) -> Building:
    """Generate a non-overlapping rectangular floor plan for `specs` inside a
    `width` x `height` building envelope, with interior doors connecting all
    rooms and windows/entry door on exterior walls."""
    if not specs:
        raise ValueError("At least one RoomSpec is required")
    if width <= 0 or height <= 0:
        raise ValueError("Building width/height must be positive")

    envelope = Rect(0.0, 0.0, float(width), float(height))
    placements = _partition(envelope, list(specs))

    used_ids: set = set()
    rooms: List[Room] = []
    for spec, rect in placements:
        rid = _make_room_id(spec.name, used_ids)
        room = Room(
            id=rid,
            name=spec.name,
            room_type=RoomType.from_str(spec.room_type),
            rect=rect,
        )
        room._needs_window = spec.needs_window  # type: ignore[attr-defined]
        rooms.append(room)

    building = Building(name=name, width=float(width), height=float(height), rooms=rooms)
    _add_interior_doors(rooms)
    _add_exterior_features(building)
    return building
