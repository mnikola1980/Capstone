"""Static catalog of furniture templates keyed by room type.

Each entry is (name, width_ft, depth_ft, color, kind, priority). Priority
controls placement order (larger/most important pieces placed first, so
smaller pieces are asked to fit around them). Items are only attempted if
the room is big enough to plausibly hold them (checked by the placer).
"""

from __future__ import annotations

from typing import Dict, List, NamedTuple

from .models import RoomType


class FurnitureTemplate(NamedTuple):
    name: str
    width: float
    depth: float
    color: str
    kind: str
    priority: int  # lower = placed first
    min_room_area: float = 0.0  # skip this item if room smaller than this


CATALOG: Dict[RoomType, List[FurnitureTemplate]] = {
    RoomType.BEDROOM: [
        FurnitureTemplate("Bed", 5.0, 6.5, "#8fb0d8", "bed", 1),
        FurnitureTemplate("Wardrobe", 4.0, 2.0, "#9c7b4f", "wardrobe", 2),
        FurnitureTemplate("Nightstand", 1.5, 1.5, "#b89a72", "table", 3),
        FurnitureTemplate("Desk", 3.5, 1.8, "#b89a72", "desk", 4, min_room_area=90),
    ],
    RoomType.MASTER_BEDROOM: [
        FurnitureTemplate("Bed (Queen)", 6.5, 6.75, "#8fb0d8", "bed", 1),
        FurnitureTemplate("Wardrobe", 5.0, 2.0, "#9c7b4f", "wardrobe", 2),
        FurnitureTemplate("Nightstand", 1.5, 1.5, "#b89a72", "table", 3),
        FurnitureTemplate("Nightstand", 1.5, 1.5, "#b89a72", "table", 3),
        FurnitureTemplate("Bench", 4.0, 1.5, "#c2a97e", "bench", 5, min_room_area=140),
    ],
    RoomType.LIVING_ROOM: [
        FurnitureTemplate("Sofa", 7.0, 3.0, "#a8785a", "sofa", 1),
        FurnitureTemplate("Coffee Table", 3.5, 2.0, "#8a6a45", "table", 2),
        FurnitureTemplate("TV Console", 5.0, 1.3, "#4a4a4a", "console", 3),
        FurnitureTemplate("Armchair", 2.7, 2.7, "#a8785a", "chair", 4, min_room_area=140),
        FurnitureTemplate("Bookshelf", 3.0, 1.0, "#9c7b4f", "shelf", 5, min_room_area=160),
    ],
    RoomType.KITCHEN: [
        FurnitureTemplate("Counter Run", 8.0, 2.0, "#c7c7c7", "counter", 1),
        FurnitureTemplate("Island", 5.0, 3.0, "#d8d0c0", "island", 2, min_room_area=140),
        FurnitureTemplate("Fridge", 3.0, 2.5, "#dedede", "appliance", 3),
        FurnitureTemplate("Dining Table", 4.5, 3.0, "#8a6a45", "table", 4, min_room_area=120),
    ],
    RoomType.DINING_ROOM: [
        FurnitureTemplate("Dining Table", 6.0, 3.5, "#8a6a45", "table", 1),
        FurnitureTemplate("Sideboard", 4.0, 1.5, "#9c7b4f", "console", 2, min_room_area=100),
    ],
    RoomType.BATHROOM: [
        FurnitureTemplate("Bathtub", 5.5, 2.5, "#d3e8ee", "tub", 1, min_room_area=55),
        FurnitureTemplate("Shower", 3.0, 3.0, "#d3e8ee", "shower", 1, min_room_area=40),
        FurnitureTemplate("Vanity/Sink", 3.0, 1.8, "#e6e6e6", "sink", 2),
        FurnitureTemplate("Toilet", 1.5, 2.3, "#f2f2f2", "toilet", 3),
    ],
    RoomType.OFFICE: [
        FurnitureTemplate("Desk", 4.5, 2.3, "#b89a72", "desk", 1),
        FurnitureTemplate("Bookshelf", 3.0, 1.0, "#9c7b4f", "shelf", 2),
        FurnitureTemplate("Chair", 2.0, 2.0, "#6f6f6f", "chair", 3),
    ],
    RoomType.ENTRY: [
        FurnitureTemplate("Console Table", 3.5, 1.3, "#9c7b4f", "console", 1, min_room_area=25),
        FurnitureTemplate("Bench", 3.0, 1.3, "#c2a97e", "bench", 2, min_room_area=30),
    ],
    RoomType.LAUNDRY: [
        FurnitureTemplate("Washer", 2.5, 2.5, "#dedede", "appliance", 1),
        FurnitureTemplate("Dryer", 2.5, 2.5, "#dedede", "appliance", 2),
    ],
    RoomType.GARAGE: [
        FurnitureTemplate("Car Bay", 9.0, 18.0, "#cfcfcf", "car", 1),
    ],
    RoomType.CLOSET: [],
    RoomType.HALLWAY: [],
    RoomType.GENERIC: [
        FurnitureTemplate("Table", 3.0, 2.0, "#8a6a45", "table", 1, min_room_area=60),
    ],
}


def catalog_for(room_type: RoomType) -> List[FurnitureTemplate]:
    return sorted(CATALOG.get(room_type, CATALOG[RoomType.GENERIC]), key=lambda t: t.priority)
