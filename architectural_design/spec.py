"""Loading building specifications from JSON.

Expected JSON shape:

{
  "name": "Studio Apartment",
  "width": 30,
  "height": 24,
  "units": "ft",
  "rooms": [
    {"name": "Living Room", "type": "living_room", "weight": 3.0},
    {"name": "Bedroom",     "type": "bedroom",      "weight": 2.0},
    {"name": "Kitchen",     "type": "kitchen",       "weight": 1.5},
    {"name": "Bathroom",    "type": "bathroom",      "weight": 0.8, "needs_window": false}
  ]
}

`weight` is a relative area share (not an absolute size) - the layout
engine allocates floor area proportionally to weight within the given
building footprint.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from .models import RoomSpec


@dataclass
class BuildingSpec:
    name: str
    width: float
    height: float
    units: str
    rooms: List[RoomSpec]


def load_spec(path: str) -> BuildingSpec:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return spec_from_dict(data)


def spec_from_dict(data: dict) -> BuildingSpec:
    required = ("name", "width", "height", "rooms")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Spec is missing required field(s): {missing}")
    if not isinstance(data["rooms"], list) or not data["rooms"]:
        raise ValueError("Spec must include a non-empty 'rooms' list")

    rooms = []
    for i, r in enumerate(data["rooms"]):
        if "name" not in r or "type" not in r:
            raise ValueError(f"rooms[{i}] must have 'name' and 'type'")
        rooms.append(
            RoomSpec(
                name=r["name"],
                room_type=r["type"],
                weight=float(r.get("weight", 1.0)),
                min_dim=float(r.get("min_dim", 6.0)),
                needs_window=bool(r.get("needs_window", True)),
            )
        )

    return BuildingSpec(
        name=data["name"],
        width=float(data["width"]),
        height=float(data["height"]),
        units=data.get("units", "ft"),
        rooms=rooms,
    )
