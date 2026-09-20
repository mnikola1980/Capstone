"""Core geometric and domain data models used throughout the package."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class RoomType(str, Enum):
    BEDROOM = "bedroom"
    MASTER_BEDROOM = "master_bedroom"
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    DINING_ROOM = "dining_room"
    BATHROOM = "bathroom"
    OFFICE = "office"
    HALLWAY = "hallway"
    CLOSET = "closet"
    LAUNDRY = "laundry"
    GARAGE = "garage"
    ENTRY = "entry"
    GENERIC = "generic"

    @classmethod
    def from_str(cls, value: str) -> "RoomType":
        try:
            return cls(value.lower())
        except ValueError:
            return cls.GENERIC


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Rect:
    """Axis-aligned rectangle, origin at bottom-left, in project units (feet)."""

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
        # Vertical adjacency (this.E touches other.W, or this.W touches other.E)
        if abs(self.x2 - other.x) < eps:
            lo, hi = max(self.y, other.y), min(self.y2, other.y2)
            if hi - lo > eps:
                return ("E", lo, hi)
        if abs(self.x - other.x2) < eps:
            lo, hi = max(self.y, other.y), min(self.y2, other.y2)
            if hi - lo > eps:
                return ("W", lo, hi)
        # Horizontal adjacency
        if abs(self.y2 - other.y) < eps:
            lo, hi = max(self.x, other.x), min(self.x2, other.x2)
            if hi - lo > eps:
                return ("N", lo, hi)
        if abs(self.y - other.y2) < eps:
            lo, hi = max(self.x, other.x), min(self.x2, other.x2)
            if hi - lo > eps:
                return ("S", lo, hi)
        return None


@dataclass
class Door:
    side: str          # "N","S","E","W" - which wall of the room it's on
    position: float     # distance along that wall (from the wall's start corner) to the door center
    width: float = 3.0  # feet
    connects_to: Optional[str] = None  # room id on the other side, or None if exterior


@dataclass
class Window:
    side: str
    position: float
    width: float = 3.0


@dataclass
class FurnitureItem:
    name: str
    rect: Rect
    rotation: int = 0  # degrees, 0/90/180/270 - already baked into rect w/h at placement time
    color: str = "#c9b79c"
    kind: str = "generic"


@dataclass
class RoomSpec:
    """User-facing request for a room, before layout has assigned geometry."""

    name: str
    room_type: str
    weight: float = 1.0        # relative floor-area share within the building
    min_dim: float = 6.0       # minimum edge length (feet) the layout should try to respect
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

    @property
    def area(self) -> float:
        return self.rect.area


@dataclass
class Building:
    name: str
    width: float
    height: float
    rooms: List[Room] = field(default_factory=list)
    units: str = "ft"

    def room_by_id(self, room_id: str) -> Optional[Room]:
        for r in self.rooms:
            if r.id == room_id:
                return r
        return None

    def total_room_area(self) -> float:
        return sum(r.area for r in self.rooms)

    def footprint_area(self) -> float:
        return self.width * self.height
