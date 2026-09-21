"""Loading building specifications from JSON.

Two kinds of spec are supported.

**Generated** - a room list with relative area `weight`s; the layout
engine partitions the footprint (see `layout.generate_layout`):

```json
{
  "name": "Studio Apartment", "width": 28, "height": 22, "units": "ft",
  "rooms": [{"name": "Living Area", "type": "living_room", "weight": 3.2}]
}
```

**Surveyed** - explicit room rectangles, optionally over several storeys,
used to reproduce a real building such as the 1931 house on the
Rhijngeesterstraatweg. Rooms carry their own `x`/`y`/`width`/`height`
plus any doors and windows, and nothing is invented by the layout engine:

```json
{
  "name": "...", "units": "m", "width": 7.15, "height": 9.90,
  "north_angle_deg": 270, "style": "heritage", "blind_sides": ["E"],
  "storeys": [
    {"name": "Begane grond", "level": 0, "ceiling_height": 3.05,
     "rooms": [
       {"name": "Hal", "type": "hal", "x": 0, "y": 1.6, "width": 2.8, "height": 3.4,
        "windows": [{"side": "W", "position": 1.7, "role": "stair"}],
        "doors":   [{"side": "S", "position": 1.4, "width": 1.1, "kind": "front_door"}]}
     ]}
  ]
}
```

`north_angle_deg` is the compass bearing of the plan's +Y axis, i.e. of
"up" on the drawing; 0 means the plan is drawn north-up.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .heritage import window_kwargs
from .models import Door, FurnitureItem, Rect, Room, RoomSpec, RoomType, Storey, Window


@dataclass
class BuildingSpec:
    name: str
    width: float
    height: float
    units: str
    rooms: List[RoomSpec] = field(default_factory=list)
    storeys: List[Storey] = field(default_factory=list)   # explicit geometry only
    explicit: bool = False
    north_angle_deg: float = 0.0
    address: str = ""
    year_built: Optional[int] = None
    architect: str = ""
    style: str = "modern"
    scale_note: str = ""
    blind_sides: List[str] = field(default_factory=list)
    provenance: Dict = field(default_factory=dict)


def load_spec(path: str) -> BuildingSpec:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return spec_from_dict(data)


def _make_id(name: str, used: set) -> str:
    base = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_") or "room"
    candidate, n = base, 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def _window_from_dict(w: dict) -> Window:
    """Build a Window, expanding a heritage `role` (e.g. "bedroom",
    "stair") into the period's opening size and number of lights."""
    kwargs = dict(window_kwargs(w["role"])) if "role" in w else {}
    for key in ("width", "height", "sill", "lights", "transom", "kind"):
        if key in w:
            kwargs[key] = w[key]
    kwargs.setdefault("width", 1.2)
    return Window(side=w["side"], position=float(w["position"]), **kwargs)


def _door_from_dict(d: dict) -> Door:
    return Door(
        side=d["side"],
        position=float(d["position"]),
        width=float(d.get("width", 0.9)),
        connects_to=d.get("connects_to"),
        kind=d.get("kind", "interior"),
        swing=int(d.get("swing", 1)),
    )


def _furniture_from_dict(f: dict, rect: Rect) -> FurnitureItem:
    """A fixture pinned by the survey rather than placed by the heuristic.

    `x`/`y` are offsets from the room's bottom-left corner, which makes a
    surveyed room easy to author by hand.
    """
    return FurnitureItem(
        name=f["name"],
        rect=Rect(rect.x + float(f.get("x", 0.0)), rect.y + float(f.get("y", 0.0)),
                  float(f["width"]), float(f["height"])),
        color=f.get("color", "#b09a76"),
        kind=f.get("kind", "generic"),
    )


def _room_from_dict(r: dict, used_ids: set) -> Room:
    for key in ("x", "y", "width", "height"):
        if key not in r:
            raise ValueError(f"Explicit room '{r.get('name', '?')}' is missing '{key}'")
    room = Room(
        id=r.get("id") or _make_id(r["name"], used_ids),
        name=r["name"],
        room_type=RoomType.from_str(r["type"]),
        rect=Rect(float(r["x"]), float(r["y"]), float(r["width"]), float(r["height"])),
        doors=[_door_from_dict(d) for d in r.get("doors", [])],
        windows=[_window_from_dict(w) for w in r.get("windows", [])],
        note=r.get("note", ""),
        features=list(r.get("features", [])),
    )
    # Surveyed fixtures are placed first so the heuristic placer works around them.
    room.furniture = [_furniture_from_dict(f, room.rect) for f in r.get("furniture", [])]
    return room


def spec_from_dict(data: dict) -> BuildingSpec:
    for key in ("name", "width", "height"):
        if key not in data:
            raise ValueError(f"Spec is missing required field '{key}'")

    common = dict(
        name=data["name"],
        width=float(data["width"]),
        height=float(data["height"]),
        units=data.get("units", "ft"),
        north_angle_deg=float(data.get("north_angle_deg", 0.0)),
        address=data.get("address", ""),
        year_built=data.get("year_built"),
        architect=data.get("architect", ""),
        style=data.get("style", "modern"),
        scale_note=data.get("scale_note", ""),
        blind_sides=list(data.get("blind_sides", [])),
        provenance=dict(data.get("provenance", {})),
    )

    if "storeys" in data:
        used_ids: set = set()
        storeys = []
        for i, s in enumerate(data["storeys"]):
            if "rooms" not in s or not s["rooms"]:
                raise ValueError(f"storeys[{i}] must contain a non-empty 'rooms' list")
            storeys.append(
                Storey(
                    name=s.get("name", f"Level {i}"),
                    level=int(s.get("level", i)),
                    ceiling_height=float(s.get("ceiling_height", 2.9)),
                    note=s.get("note", ""),
                    rooms=[_room_from_dict(r, used_ids) for r in s["rooms"]],
                )
            )
        return BuildingSpec(storeys=storeys, explicit=True, **common)

    if "rooms" not in data or not isinstance(data["rooms"], list) or not data["rooms"]:
        raise ValueError("Spec must include a non-empty 'rooms' list (or 'storeys')")

    first = data["rooms"][0]
    if all(k in first for k in ("x", "y", "width", "height")):
        used_ids = set()
        rooms = [_room_from_dict(r, used_ids) for r in data["rooms"]]
        storey = Storey(name=data.get("storey_name", "Ground floor"), level=0, rooms=rooms)
        return BuildingSpec(storeys=[storey], explicit=True, **common)

    specs = []
    for i, r in enumerate(data["rooms"]):
        if "name" not in r or "type" not in r:
            raise ValueError(f"rooms[{i}] must have 'name' and 'type'")
        specs.append(
            RoomSpec(
                name=r["name"],
                room_type=r["type"],
                weight=float(r.get("weight", 1.0)),
                min_dim=float(r.get("min_dim", 6.0)),
                needs_window=bool(r.get("needs_window", True)),
            )
        )
    return BuildingSpec(rooms=specs, explicit=False, **common)
