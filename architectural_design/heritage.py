"""The 1931 Dutch (Oegstgeest) heritage profile.

Everything in this module describes the *interbellum* Dutch villa idiom
that the houses on the Rhijngeesterstraatweg belong to: a block of six
"landhuizen" built in 1931 to plan no. 590 by the Leiden architect
M.C. van Straten. It carries three things:

1. `HERITAGE_STYLE` - the drawing style of the original sheets: warm linen
   paper, sepia ink, solid poché walls, sparse hand-lettered labels.
2. `HERITAGE_ROOM_COLORS` - a muted period palette for the room fills,
   keyed by room type, so a heritage plan does not read like a modern
   estate-agent floor plan.
3. `HERITAGE_FURNITURE` - period-appropriate furniture (in metres) for the
   Dutch room names found on the drawings: a *huiskamer* gets a dining
   table and a fireplace seat rather than a sectional and a TV console.

The window conventions of the period are captured in `WINDOW_LIGHTS`: the
tall openings carry a divided upper light (*bovenlicht*) over a single
large pane, which is what the renderer draws as mullion ticks.
"""

from __future__ import annotations

from typing import Dict, List

from .furniture_catalog import FurnitureTemplate
from .models import RoomType

# ---------------------------------------------------------------------------
# Drawing style
# ---------------------------------------------------------------------------

HERITAGE_STYLE = {
    "paper": "#d9c7a0",          # linen drawing paper, aged
    "paper_edge": "#c9b487",
    "ink": "#4a2c1a",            # sepia drawing ink
    "ink_light": "#6d4a32",
    "wall": "#432616",           # poché fill for cut walls
    "glass": "#7d5a3c",
    "text": "#3c2312",
    "furniture_edge": "#6d4a32",
    "wall_lw": 0.0,              # walls are drawn as filled poché, not lines
    "line_lw": 1.0,
    "title_font": "serif",
}

MODERN_STYLE = {
    "paper": "#ffffff",
    "paper_edge": "#ffffff",
    "ink": "#000000",
    "ink_light": "#5a5a5a",
    "wall": "#000000",
    "glass": "#4a90d9",
    "text": "#222222",
    "furniture_edge": "#3a3a3a",
    "wall_lw": 2.2,
    "line_lw": 1.0,
    "title_font": "sans-serif",
}


def style_for(name: str) -> Dict:
    return HERITAGE_STYLE if str(name).lower().startswith("herit") else MODERN_STYLE


#: Muted period fills, in the spirit of a tinted 1930s presentation drawing.
HERITAGE_ROOM_COLORS = {
    RoomType.LIVING_ROOM: "#cdb98e",
    RoomType.SALON: "#d2c096",
    RoomType.DINING_ROOM: "#cbb78c",
    RoomType.KITCHEN: "#c2bda0",
    RoomType.BEDROOM: "#cfc4a4",
    RoomType.MASTER_BEDROOM: "#cec099",
    RoomType.BATHROOM: "#bdc3ae",
    RoomType.TOILET: "#b9bfa9",
    RoomType.OFFICE: "#cdbd98",
    RoomType.HALLWAY: "#c6b795",
    RoomType.LANDING: "#c6b795",
    RoomType.ENTRY: "#c9ba98",
    RoomType.STORAGE: "#bbb195",
    RoomType.CLOSET: "#bbb195",
    RoomType.LAUNDRY: "#bfbc9f",
    RoomType.ATTIC: "#c8bb9a",
    RoomType.BALCONY: "#b6ae91",
    RoomType.BAY: "#d2c096",
    RoomType.GARAGE: "#b4ab8e",
    RoomType.GENERIC: "#c8ba97",
}

# ---------------------------------------------------------------------------
# Window conventions of the period
# ---------------------------------------------------------------------------

#: Typical opening sizes (metres) on the 1931 elevations, by window role.
#: (width, height, sill, lights, transom)
WINDOW_LIGHTS = {
    "living_front": (2.40, 1.95, 0.55, 3, True),   # wide voorkamer window band
    "living_rear": (2.20, 1.95, 0.55, 3, True),    # garden side, onto the terrace
    "kitchen": (1.20, 1.30, 1.00, 2, True),
    "bedroom": (1.60, 1.50, 0.80, 3, True),
    "small": (0.80, 1.00, 1.10, 2, False),
    "toilet": (0.50, 0.60, 1.60, 1, False),
    "stair": (1.20, 2.40, 1.10, 4, True),          # the tall bordestrap window
    "dormer": (1.60, 1.05, 0.85, 3, True),         # attic dormer (dakkapel)
}


def window_kwargs(role: str) -> Dict:
    """Keyword arguments for `Window` describing a period opening."""
    w, h, sill, lights, transom = WINDOW_LIGHTS.get(role, WINDOW_LIGHTS["small"])
    kind = {"stair": "stair", "dormer": "dormer"}.get(role, "casement")
    return {
        "width": w,
        "height": h,
        "sill": sill,
        "lights": lights,
        "transom": transom,
        "kind": kind,
    }


# ---------------------------------------------------------------------------
# Period furniture (metres)
# ---------------------------------------------------------------------------

HERITAGE_FURNITURE: Dict[RoomType, List[FurnitureTemplate]] = {
    RoomType.LIVING_ROOM: [
        FurnitureTemplate("Eettafel", 1.60, 1.00, "#8a6a45", "table", 1),
        FurnitureTemplate("Buffetkast", 1.60, 0.55, "#7d5a36", "console", 2),
        FurnitureTemplate("Fauteuil", 0.75, 0.80, "#9c6f52", "chair", 3),
        FurnitureTemplate("Fauteuil", 0.75, 0.80, "#9c6f52", "chair", 4),
    ],
    RoomType.SALON: [
        FurnitureTemplate("Canapé", 1.95, 0.85, "#9c6f52", "sofa", 1),
        FurnitureTemplate("Salontafel", 1.00, 0.60, "#8a6a45", "table", 2),
        FurnitureTemplate("Boekenkast", 1.20, 0.35, "#7d5a36", "shelf", 3),
        FurnitureTemplate("Fauteuil", 0.75, 0.80, "#9c6f52", "chair", 4),
    ],
    RoomType.KITCHEN: [
        FurnitureTemplate("Aanrecht", 2.40, 0.60, "#b3ab93", "counter", 1),
        FurnitureTemplate("Fornuis", 0.70, 0.60, "#8c8778", "appliance", 2),
        FurnitureTemplate("Koelkast", 0.70, 0.65, "#c3bda9", "appliance", 3),
        FurnitureTemplate("Keukentafel", 1.20, 0.80, "#8a6a45", "table", 4, min_room_area=9.0),
    ],
    RoomType.DINING_ROOM: [
        FurnitureTemplate("Eettafel", 1.80, 1.00, "#8a6a45", "table", 1),
        FurnitureTemplate("Dressoir", 1.40, 0.50, "#7d5a36", "console", 2),
    ],
    RoomType.BEDROOM: [
        FurnitureTemplate("Ledikant", 1.40, 2.00, "#a08a6a", "bed", 1),
        FurnitureTemplate("Linnenkast", 1.20, 0.60, "#7d5a36", "wardrobe", 2),
        FurnitureTemplate("Nachtkastje", 0.45, 0.40, "#8a6a45", "table", 3),
        FurnitureTemplate("Waschtafel", 0.80, 0.50, "#c3bda9", "sink", 4, min_room_area=9.0),
    ],
    RoomType.MASTER_BEDROOM: [
        FurnitureTemplate("Ledikant", 1.60, 2.00, "#a08a6a", "bed", 1),
        FurnitureTemplate("Linnenkast", 1.60, 0.60, "#7d5a36", "wardrobe", 2),
        FurnitureTemplate("Nachtkastje", 0.45, 0.40, "#8a6a45", "table", 3),
        FurnitureTemplate("Nachtkastje", 0.45, 0.40, "#8a6a45", "table", 4),
        FurnitureTemplate("Toilettafel", 1.00, 0.45, "#8a6a45", "console", 5, min_room_area=14.0),
    ],
    RoomType.OFFICE: [
        FurnitureTemplate("Schrijfbureau", 1.35, 0.70, "#8a6a45", "desk", 1),
        FurnitureTemplate("Boekenkast", 1.20, 0.35, "#7d5a36", "shelf", 2),
        FurnitureTemplate("Stoel", 0.50, 0.50, "#6f6252", "chair", 3),
    ],
    RoomType.BATHROOM: [
        FurnitureTemplate("Ligbad", 1.70, 0.75, "#c9d2cb", "tub", 1, min_room_area=6.0),
        FurnitureTemplate("Douche", 0.90, 0.90, "#c9d2cb", "shower", 1, min_room_area=3.5),
        FurnitureTemplate("Wastafel", 0.70, 0.45, "#d7d9d0", "sink", 2),
        FurnitureTemplate("Closet", 0.40, 0.65, "#d7d9d0", "toilet", 3),
    ],
    RoomType.TOILET: [
        FurnitureTemplate("Closet", 0.40, 0.65, "#d7d9d0", "toilet", 1),
        FurnitureTemplate("Fonteintje", 0.35, 0.28, "#d7d9d0", "sink", 2, min_room_area=1.6),
    ],
    # Stairs are fixed building fabric: they are pinned by the survey
    # (a room's "furniture" list in the spec), not placed heuristically.
    RoomType.HALLWAY: [
        FurnitureTemplate("Kapstok", 1.00, 0.30, "#7d5a36", "console", 2),
    ],
    RoomType.LANDING: [
        FurnitureTemplate("Linnenkast", 1.00, 0.55, "#7d5a36", "wardrobe", 2, min_room_area=7.0),
    ],
    RoomType.ENTRY: [
        FurnitureTemplate("Kapstok", 1.00, 0.30, "#7d5a36", "console", 1),
        FurnitureTemplate("Bankje", 0.90, 0.40, "#9c6f52", "bench", 2, min_room_area=3.5),
    ],
    RoomType.STORAGE: [
        FurnitureTemplate("Kast", 0.90, 0.55, "#8d8470", "wardrobe", 1, min_room_area=1.5),
    ],
    RoomType.LAUNDRY: [
        FurnitureTemplate("Wasmachine", 0.60, 0.60, "#c3bda9", "appliance", 1),
        FurnitureTemplate("Wastafel", 0.60, 0.50, "#d7d9d0", "sink", 2),
    ],
    RoomType.ATTIC: [
        FurnitureTemplate("Ledikant", 1.40, 2.00, "#a08a6a", "bed", 1, min_room_area=9.0),
        FurnitureTemplate("Kast", 1.00, 0.55, "#7d5a36", "wardrobe", 2),
    ],
    RoomType.BALCONY: [],
    RoomType.BAY: [
        FurnitureTemplate("Zitbank", 1.40, 0.55, "#9c6f52", "bench", 1, min_room_area=2.5),
    ],
    RoomType.CLOSET: [],
    RoomType.GARAGE: [
        FurnitureTemplate("Auto", 1.80, 4.20, "#b0a893", "car", 1, min_room_area=14.0),
    ],
    RoomType.GENERIC: [
        FurnitureTemplate("Tafel", 1.20, 0.80, "#8a6a45", "table", 1, min_room_area=6.0),
    ],
}


def heritage_catalog(room_type: RoomType) -> List[FurnitureTemplate]:
    """Period furniture templates (metres) for a room type."""
    items = HERITAGE_FURNITURE.get(room_type, HERITAGE_FURNITURE[RoomType.GENERIC])
    return sorted(items, key=lambda t: t.priority)


#: Provenance of the heritage data, printed in the title block.
PROVENANCE = {
    "estate": "Terrein v/h landhuis 'Enna'",
    "plan_no": "Plan no. 590",
    "architect": "M.C. van Straten, arch., Leiden",
    "date": "maart 1931",
    "project": "Zes landhuizen a/d Rijksstraatweg te Oegstgeest",
    "scale": "schaal 1:100",
    "approval": "Goedgekeurd B&W Oegstgeest, 1 juli 1931",
    "note": "As built 0.90 m dieper dan bouwteekening (aanvraag 15-6-1931)",
}
