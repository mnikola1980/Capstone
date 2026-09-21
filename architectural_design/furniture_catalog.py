"""Furniture templates keyed by room type.

All dimensions are stored in **metres** and converted to the building's
unit on lookup, so the metric heritage plans and the imperial generated
plans share one source of truth.

Each entry carries a name, footprint, colour, a `kind` used by the
renderers to pick a glyph, and a priority controlling placement order
(larger/more important pieces are placed first so smaller pieces fit
around them). `min_room_area` (in square metres) skips an item in a room
too small to plausibly hold it.
"""

from __future__ import annotations

from typing import Dict, List, NamedTuple

from .models import FT_PER_M, RoomType


class FurnitureTemplate(NamedTuple):
    name: str
    width: float           # metres
    depth: float           # metres
    color: str
    kind: str
    priority: int          # lower = placed first
    min_room_area: float = 0.0   # square metres


def _scaled(t: FurnitureTemplate, units: str) -> FurnitureTemplate:
    if units != "ft":
        return t
    f = FT_PER_M
    return t._replace(
        width=t.width * f,
        depth=t.depth * f,
        min_room_area=t.min_room_area * f * f,
    )


# Dimensions in metres (the imperial sizes these were derived from are
# recovered exactly by the ft conversion on lookup).
CATALOG: Dict[RoomType, List[FurnitureTemplate]] = {
    RoomType.BEDROOM: [
        FurnitureTemplate("Bed", 1.52, 1.98, "#8fb0d8", "bed", 1),
        FurnitureTemplate("Wardrobe", 1.22, 0.61, "#9c7b4f", "wardrobe", 2),
        FurnitureTemplate("Nightstand", 0.46, 0.46, "#b89a72", "table", 3),
        FurnitureTemplate("Desk", 1.07, 0.55, "#b89a72", "desk", 4, min_room_area=8.36),
    ],
    RoomType.MASTER_BEDROOM: [
        FurnitureTemplate("Bed (Queen)", 1.98, 2.06, "#8fb0d8", "bed", 1),
        FurnitureTemplate("Wardrobe", 1.52, 0.61, "#9c7b4f", "wardrobe", 2),
        FurnitureTemplate("Nightstand", 0.46, 0.46, "#b89a72", "table", 3),
        FurnitureTemplate("Nightstand", 0.46, 0.46, "#b89a72", "table", 3),
        FurnitureTemplate("Bench", 1.22, 0.46, "#c2a97e", "bench", 5, min_room_area=13.01),
    ],
    RoomType.LIVING_ROOM: [
        FurnitureTemplate("Sofa", 2.13, 0.91, "#a8785a", "sofa", 1),
        FurnitureTemplate("Coffee Table", 1.07, 0.61, "#8a6a45", "table", 2),
        FurnitureTemplate("TV Console", 1.52, 0.40, "#4a4a4a", "console", 3),
        FurnitureTemplate("Armchair", 0.82, 0.82, "#a8785a", "chair", 4, min_room_area=13.01),
        FurnitureTemplate("Bookshelf", 0.91, 0.30, "#9c7b4f", "shelf", 5, min_room_area=14.86),
    ],
    RoomType.SALON: [
        FurnitureTemplate("Sofa", 1.95, 0.85, "#a8785a", "sofa", 1),
        FurnitureTemplate("Coffee Table", 1.00, 0.60, "#8a6a45", "table", 2),
        FurnitureTemplate("Bookshelf", 1.20, 0.35, "#9c7b4f", "shelf", 3),
    ],
    RoomType.KITCHEN: [
        FurnitureTemplate("Counter Run", 2.44, 0.61, "#c7c7c7", "counter", 1),
        FurnitureTemplate("Island", 1.52, 0.91, "#d8d0c0", "island", 2, min_room_area=13.01),
        FurnitureTemplate("Fridge", 0.91, 0.76, "#dedede", "appliance", 3),
        FurnitureTemplate("Dining Table", 1.37, 0.91, "#8a6a45", "table", 4, min_room_area=11.15),
    ],
    RoomType.DINING_ROOM: [
        FurnitureTemplate("Dining Table", 1.83, 1.07, "#8a6a45", "table", 1),
        FurnitureTemplate("Sideboard", 1.22, 0.46, "#9c7b4f", "console", 2, min_room_area=9.29),
    ],
    RoomType.BATHROOM: [
        FurnitureTemplate("Bathtub", 1.68, 0.76, "#d3e8ee", "tub", 1, min_room_area=5.11),
        FurnitureTemplate("Shower", 0.91, 0.91, "#d3e8ee", "shower", 1, min_room_area=3.72),
        FurnitureTemplate("Vanity/Sink", 0.91, 0.55, "#e6e6e6", "sink", 2),
        FurnitureTemplate("Toilet", 0.46, 0.70, "#f2f2f2", "toilet", 3),
    ],
    RoomType.TOILET: [
        FurnitureTemplate("Toilet", 0.40, 0.65, "#f2f2f2", "toilet", 1),
        FurnitureTemplate("Basin", 0.35, 0.28, "#e6e6e6", "sink", 2, min_room_area=1.6),
    ],
    RoomType.OFFICE: [
        FurnitureTemplate("Desk", 1.37, 0.70, "#b89a72", "desk", 1),
        FurnitureTemplate("Bookshelf", 0.91, 0.30, "#9c7b4f", "shelf", 2),
        FurnitureTemplate("Chair", 0.61, 0.61, "#6f6f6f", "chair", 3),
    ],
    RoomType.ENTRY: [
        FurnitureTemplate("Console Table", 1.07, 0.40, "#9c7b4f", "console", 1, min_room_area=2.32),
        FurnitureTemplate("Bench", 0.91, 0.40, "#c2a97e", "bench", 2, min_room_area=2.79),
    ],
    RoomType.LAUNDRY: [
        FurnitureTemplate("Washer", 0.76, 0.76, "#dedede", "appliance", 1),
        FurnitureTemplate("Dryer", 0.76, 0.76, "#dedede", "appliance", 2),
    ],
    RoomType.GARAGE: [
        FurnitureTemplate("Car Bay", 2.74, 5.49, "#cfcfcf", "car", 1),
    ],
    RoomType.HALLWAY: [],
    RoomType.LANDING: [],
    RoomType.CLOSET: [],
    RoomType.STORAGE: [],
    RoomType.ATTIC: [],
    RoomType.BALCONY: [],
    RoomType.BAY: [],
    RoomType.GENERIC: [
        FurnitureTemplate("Table", 0.91, 0.61, "#8a6a45", "table", 1, min_room_area=5.57),
    ],
}


def catalog_for(room_type: RoomType, units: str = "ft", style: str = "modern") -> List[FurnitureTemplate]:
    """Furniture templates for a room type, in the requested unit.

    With `style="heritage"` the 1931 Dutch period catalogue is used
    instead (its dimensions are also metric and scaled the same way).
    """
    if str(style).lower().startswith("herit"):
        from .heritage import heritage_catalog  # imported lazily to avoid a cycle

        items = heritage_catalog(room_type)
    else:
        items = CATALOG.get(room_type, CATALOG[RoomType.GENERIC])
    return [_scaled(t, units) for t in sorted(items, key=lambda t: t.priority)]
