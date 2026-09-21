"""Core geometric and domain data models used throughout the package.

Lengths are expressed in the building's own unit (`Building.units`), which
is either "ft" (imperial, the default for the generated example plans) or
"m" (metric, used by the 1931 Dutch heritage plans).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

FT_PER_M = 3.280839895013123


def to_units(value_m: float, units: str) -> float:
    """Convert a length given in metres into the target unit."""
    return value_m * FT_PER_M if units == "ft" else value_m


def area_label(units: str) -> str:
    return "sq ft" if units == "ft" else "m²"


# ---------------------------------------------------------------------------
# Room types
# ---------------------------------------------------------------------------


class RoomType(str, Enum):
    BEDROOM = "bedroom"
    MASTER_BEDROOM = "master_bedroom"
    LIVING_ROOM = "living_room"
    SALON = "salon"
    KITCHEN = "kitchen"
    DINING_ROOM = "dining_room"
    BATHROOM = "bathroom"
    TOILET = "toilet"
    OFFICE = "office"
    HALLWAY = "hallway"
    LANDING = "landing"
    CLOSET = "closet"
    STORAGE = "storage"
    LAUNDRY = "laundry"
    GARAGE = "garage"
    ENTRY = "entry"
    ATTIC = "attic"
    BALCONY = "balcony"
    BAY = "bay"
    GENERIC = "generic"

    @classmethod
    def from_str(cls, value: str) -> "RoomType":
        key = (value or "").strip().lower().replace(" ", "_")
        if key in _ROOM_TYPE_ALIASES:
            return _ROOM_TYPE_ALIASES[key]
        try:
            return cls(key)
        except ValueError:
            return cls.GENERIC


# Dutch (and a few English) names used on the 1931 drawings and in the
# estate-agent brochure, mapped onto the canonical room types.
_ROOM_TYPE_ALIASES: Dict[str, RoomType] = {
    # circulation
    "hal": RoomType.HALLWAY,
    "gang": RoomType.HALLWAY,
    "portaal": RoomType.LANDING,
    "overloop": RoomType.LANDING,
    "vestibule": RoomType.ENTRY,
    "entree": RoomType.ENTRY,
    "hall": RoomType.HALLWAY,
    # living
    "huiskamer": RoomType.LIVING_ROOM,
    "woonkamer": RoomType.LIVING_ROOM,
    "achterkamer": RoomType.LIVING_ROOM,
    "voorkamer": RoomType.SALON,
    "zitkamer": RoomType.SALON,
    "spreekkamer": RoomType.OFFICE,
    "studeerkamer": RoomType.OFFICE,
    "werkkamer": RoomType.OFFICE,
    "eetkamer": RoomType.DINING_ROOM,
    "zitje": RoomType.BAY,
    "erker": RoomType.BAY,
    # service
    "keuken": RoomType.KITCHEN,
    "bijkeuken": RoomType.LAUNDRY,
    "wc": RoomType.TOILET,
    "badkamer": RoomType.BATHROOM,
    "badk": RoomType.BATHROOM,
    "berging": RoomType.STORAGE,
    "bergruimte": RoomType.STORAGE,
    "trapkast": RoomType.STORAGE,
    "kelder": RoomType.STORAGE,
    # sleeping
    "slaapkamer": RoomType.BEDROOM,
    "slaapk": RoomType.BEDROOM,
    "ouderslaapkamer": RoomType.MASTER_BEDROOM,
    # upper / outdoor
    "zolder": RoomType.ATTIC,
    "vliering": RoomType.ATTIC,
    "balkon": RoomType.BALCONY,
    "balcon": RoomType.BALCONY,
    "serre": RoomType.BAY,
    "veranda": RoomType.BAY,
}

# Rooms that are circulation/serving space rather than habitable rooms.
NON_HABITABLE_TYPES = {
    RoomType.HALLWAY,
    RoomType.LANDING,
    RoomType.ENTRY,
    RoomType.TOILET,
    RoomType.CLOSET,
    RoomType.STORAGE,
    RoomType.GARAGE,
    RoomType.BALCONY,
}


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Rect:
    """Axis-aligned rectangle, origin at bottom-left, in project units."""

    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def area(self) -> float:
        return self.w * self.h

    @property
    def center(self) -> Point:
        return Point(self.x + self.w / 2, self.y + self.h / 2)

    def contains_point(self, p: Point, eps: float = 1e-6) -> bool:
        return (self.x - eps <= p.x <= self.x2 + eps) and (self.y - eps <= p.y <= self.y2 + eps)

    def overlaps(self, other: "Rect", eps: float = 1e-6) -> bool:
        """True if the two rectangles overlap with positive area (touching edges is OK)."""
        return not (
            self.x2 <= other.x + eps
            or other.x2 <= self.x + eps
            or self.y2 <= other.y + eps
            or other.y2 <= self.y + eps
        )

    def shared_edge(self, other: "Rect", eps: float = 1e-3) -> Optional[Tuple[str, float, float]]:
        """
        If this rect shares a wall segment with `other`, return
        (side, overlap_start, overlap_end) where `side` is the side of *this*
        rect ("N","S","E","W") the shared wall lies on, and the overlap range
        is along the perpendicular axis. Returns None if not adjacent.
        """
        if abs(self.x2 - other.x) < eps:
            lo, hi = max(self.y, other.y), min(self.y2, other.y2)
            if hi - lo > eps:
                return ("E", lo, hi)
        if abs(self.x - other.x2) < eps:
            lo, hi = max(self.y, other.y), min(self.y2, other.y2)
            if hi - lo > eps:
                return ("W", lo, hi)
        if abs(self.y2 - other.y) < eps:
            lo, hi = max(self.x, other.x), min(self.x2, other.x2)
            if hi - lo > eps:
                return ("N", lo, hi)
        if abs(self.y - other.y2) < eps:
            lo, hi = max(self.x, other.x), min(self.x2, other.x2)
            if hi - lo > eps:
                return ("S", lo, hi)
        return None


# ---------------------------------------------------------------------------
# Openings
# ---------------------------------------------------------------------------


@dataclass
class Door:
    side: str           # "N","S","E","W" - which wall of the room it's on
    position: float     # distance along that wall (from the wall's start corner) to the door centre
    width: float = 3.0
    connects_to: Optional[str] = None  # room id on the other side, or None if exterior
    kind: str = "interior"  # interior | front_door | garden | sliding | opening
    swing: int = 1          # 1 or -1, which way the leaf is drawn


@dataclass
class Window:
    """A window opening.

    `lights` is the number of glazed panes across the opening - on the 1931
    houses the tall windows carry a divided upper light (*bovenlicht*) over
    a single large pane, which is what gives the facades their period
    character. `height` and `sill` are used for the daylight calculation.
    """

    side: str
    position: float
    width: float = 3.0
    height: float = 1.5
    sill: float = 0.9
    lights: int = 1
    transom: bool = False   # has a divided bovenlicht above the main pane
    kind: str = "casement"  # casement | bay | french | dormer | stair | roof

    @property
    def glazed_area(self) -> float:
        return self.width * self.height


@dataclass
class FurnitureItem:
    name: str
    rect: Rect
    rotation: int = 0
    color: str = "#c9b79c"
    kind: str = "generic"


@dataclass
class RoomSpec:
    """User-facing request for a room, before layout has assigned geometry."""

    name: str
    room_type: str
    weight: float = 1.0
    min_dim: float = 6.0
    needs_window: bool = True


@dataclass
class Room:
    id: str
    name: str
    room_type: RoomType
    rect: Rect
    doors: List[Door] = field(default_factory=list)
    windows: List[Window] = field(default_factory=list)
    furniture: List[FurnitureItem] = field(default_factory=list)
    note: str = ""          # e.g. "open haard", "schuifdeuren", "onder de kap"
    features: List[str] = field(default_factory=list)

    @property
    def area(self) -> float:
        return self.rect.area

    @property
    def is_habitable(self) -> bool:
        return self.room_type not in NON_HABITABLE_TYPES

    @property
    def glazed_area(self) -> float:
        return sum(w.glazed_area for w in self.windows)


@dataclass
class Storey:
    """One floor of a building."""

    name: str
    rooms: List[Room] = field(default_factory=list)
    level: int = 0
    ceiling_height: float = 2.9
    note: str = ""

    @property
    def area(self) -> float:
        return sum(r.area for r in self.rooms)

    @property
    def habitable_area(self) -> float:
        return sum(r.area for r in self.rooms if r.is_habitable)


# ---------------------------------------------------------------------------
# Compass / orientation
# ---------------------------------------------------------------------------

#: Bearing, in degrees clockwise from north, of each plan side when the plan's
#: +Y ("up" on the sheet) points due north.
_SIDE_BEARING_WHEN_NORTH_UP = {"N": 0.0, "E": 90.0, "S": 180.0, "W": 270.0}

_COMPASS_16 = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def compass_bearing(side: str, north_angle_deg: float) -> float:
    """Real-world bearing of a wall's outward normal.

    `north_angle_deg` is the compass bearing of the plan's +Y axis, i.e. of
    "up" on the drawing. With north_angle_deg = 0 the plan is drawn north-up
    and the top wall faces north; with 270 the top of the sheet faces west.
    """
    base = _SIDE_BEARING_WHEN_NORTH_UP[side]
    return (base + north_angle_deg) % 360.0


def compass_name(bearing_deg: float) -> str:
    """Nearest 16-point compass name for a bearing in degrees."""
    idx = int((bearing_deg % 360.0) / 22.5 + 0.5) % 16
    return _COMPASS_16[idx]


def bearing_to_vector(bearing_deg: float) -> Tuple[float, float]:
    """Unit vector, in plan coordinates, pointing along a compass bearing,
    assuming the plan is drawn north-up. Used to draw the north arrow."""
    rad = math.radians(bearing_deg)
    return (math.sin(rad), math.cos(rad))


@dataclass
class Building:
    name: str
    width: float
    height: float
    rooms: List[Room] = field(default_factory=list)
    units: str = "ft"
    storeys: List[Storey] = field(default_factory=list)
    north_angle_deg: float = 0.0   # compass bearing of the plan's +Y axis
    address: str = ""
    year_built: Optional[int] = None
    architect: str = ""
    style: str = "modern"          # modern | heritage
    scale_note: str = ""
    blind_sides: List[str] = field(default_factory=list)  # party walls: no openings

    def __post_init__(self):
        # Backwards compatibility: a Building built from a flat room list
        # behaves as a single-storey building.
        if not self.storeys and self.rooms:
            self.storeys = [Storey(name="Ground floor", rooms=self.rooms, level=0)]
        elif self.storeys and not self.rooms:
            self.rooms = self.storeys[0].rooms

    def all_rooms(self) -> List[Room]:
        if self.storeys:
            return [r for s in self.storeys for r in s.rooms]
        return list(self.rooms)

    def room_by_id(self, room_id: str) -> Optional[Room]:
        for r in self.all_rooms():
            if r.id == room_id:
                return r
        return None

    def total_room_area(self) -> float:
        return sum(r.area for r in self.rooms)

    def total_floor_area(self) -> float:
        return sum(s.area for s in self.storeys) if self.storeys else self.total_room_area()

    def footprint_area(self) -> float:
        return self.width * self.height

    def side_bearing(self, side: str) -> float:
        return compass_bearing(side, self.north_angle_deg)

    def side_compass(self, side: str) -> str:
        return compass_name(self.side_bearing(side))
