"""Daylight and orientation analysis ("lights").

Two things are computed per room:

*Daylight*  - the glazed area of the room's windows as a fraction of its
floor area. Dutch practice (and the Bouwbesluit's daylight requirement for
a *verblijfsruimte*) works out at roughly 10% of the floor area of
equivalent daylight opening, so that is used as the pass mark, with a
generous band above it. The 1931 houses were designed well before that
rule but their tall windows with divided upper lights (*bovenlichten*)
comfortably clear it in the principal rooms, which is exactly the
"prettige lichtinval" the sale brochure describes.

*Orientation* - each window's wall is converted from a plan side
("N"/"E"/"S"/"W") into a real-world compass bearing using the building's
`north_angle_deg`, and from there into the part of the day that facade
receives direct sun. A room's sun periods are the union over its windows.

Nothing here is a substitute for a real climate-based daylight simulation;
it is the quick orientation check an architect does on a sketch plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import Building, Room, Storey, compass_bearing, compass_name

#: Fraction of floor area of glazing at which a habitable room is considered
#: adequately daylit (Dutch rule of thumb / Bouwbesluit order of magnitude).
DAYLIGHT_TARGET = 0.10
DAYLIGHT_GENEROUS = 0.18

#: Which part of the day a facade of a given bearing gets direct sun.
#: Bearings are the outward normal of the wall, degrees clockwise from north.
_SUN_BANDS = [
    (45.0, 112.5, "morning sun"),
    (112.5, 247.5, "midday sun"),
    (247.5, 315.0, "afternoon sun"),
]


def sun_periods(bearing_deg: float) -> List[str]:
    """Parts of the day a wall with this outward bearing sees direct sun."""
    b = bearing_deg % 360.0
    periods = [label for lo, hi, label in _SUN_BANDS if lo <= b < hi]
    return periods or ["no direct sun"]


@dataclass
class RoomDaylight:
    room_id: str
    name: str
    storey: str
    floor_area: float
    glazed_area: float
    ratio: float
    habitable: bool
    orientations: List[str] = field(default_factory=list)   # compass names, e.g. ["W", "S"]
    sun: List[str] = field(default_factory=list)            # e.g. ["afternoon sun"]
    rating: str = "none"
    window_count: int = 0

    @property
    def meets_target(self) -> bool:
        return self.ratio >= DAYLIGHT_TARGET


def _rate(ratio: float, habitable: bool, windows: int) -> str:
    if windows == 0:
        return "internal"
    if not habitable:
        return "serving"
    if ratio >= DAYLIGHT_GENEROUS:
        return "generous"
    if ratio >= DAYLIGHT_TARGET:
        return "adequate"
    return "borderline"


def analyse_room(room: Room, north_angle_deg: float, storey_name: str = "") -> RoomDaylight:
    bearings = [compass_bearing(w.side, north_angle_deg) for w in room.windows]
    orientations: List[str] = []
    periods: List[str] = []
    for b in bearings:
        name = compass_name(b)
        if name not in orientations:
            orientations.append(name)
        for p in sun_periods(b):
            if p not in periods and p != "no direct sun":
                periods.append(p)

    floor_area = room.area
    glazed = room.glazed_area
    ratio = (glazed / floor_area) if floor_area > 0 else 0.0
    return RoomDaylight(
        room_id=room.id,
        name=room.name,
        storey=storey_name,
        floor_area=floor_area,
        glazed_area=glazed,
        ratio=ratio,
        habitable=room.is_habitable,
        orientations=orientations,
        sun=periods or (["no direct sun"] if room.windows else []),
        rating=_rate(ratio, room.is_habitable, len(room.windows)),
        window_count=len(room.windows),
    )


def analyse_building(building: Building) -> List[RoomDaylight]:
    """Daylight report for every room on every storey."""
    results: List[RoomDaylight] = []
    storeys = building.storeys or [Storey(name="Ground floor", rooms=building.rooms)]
    for storey in storeys:
        for room in storey.rooms:
            results.append(analyse_room(room, building.north_angle_deg, storey.name))
    return results


def summarise(building: Building, report: Optional[List[RoomDaylight]] = None) -> Dict:
    """Aggregate daylight figures plus the building's facade orientations."""
    report = report if report is not None else analyse_building(building)
    habitable = [r for r in report if r.habitable and r.window_count > 0]
    short = [r for r in report if r.habitable and not r.meets_target]

    facades = {}
    for side in ("N", "E", "S", "W"):
        bearing = building.side_bearing(side)
        facades[side] = {
            "bearing": round(bearing, 1),
            "compass": compass_name(bearing),
            "sun": sun_periods(bearing),
            "blind": side in building.blind_sides,
        }

    total_glazed = sum(r.glazed_area for r in report)
    total_habitable_area = sum(r.floor_area for r in report if r.habitable)
    return {
        "facades": facades,
        "total_glazed_area": round(total_glazed, 2),
        "habitable_floor_area": round(total_habitable_area, 2),
        "average_daylight_ratio": round(
            sum(r.ratio for r in habitable) / len(habitable), 4
        ) if habitable else 0.0,
        "rooms_below_target": [r.name for r in short],
        "target_ratio": DAYLIGHT_TARGET,
    }


def format_report(building: Building, report: Optional[List[RoomDaylight]] = None) -> str:
    """Human-readable daylight/orientation table for the console."""
    report = report if report is not None else analyse_building(building)
    unit = "m²" if building.units == "m" else "sq ft"
    lines = []
    lines.append(f"Daylight & orientation - {building.name}")
    facades = summarise(building, report)["facades"]
    facing = ", ".join(
        f"{side}={facades[side]['compass']}" + (" (party wall)" if facades[side]["blind"] else "")
        for side in ("N", "E", "S", "W")
    )
    lines.append(f"  Plan sides face: {facing}")
    lines.append("")
    header = f"  {'Room':<22}{'Storey':<16}{'Floor':>9}{'Glazed':>9}{'Ratio':>8}  {'Facing':<10}{'Rating'}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for r in report:
        facing = "/".join(r.orientations) if r.orientations else "-"
        lines.append(
            f"  {r.name[:21]:<22}{r.storey[:15]:<16}"
            f"{r.floor_area:>8.1f}{'':1}{r.glazed_area:>8.1f}{'':1}"
            f"{r.ratio*100:>7.1f}%  {facing:<10}{r.rating}"
        )
    s = summarise(building, report)
    lines.append("")
    lines.append(
        f"  Average daylight ratio in glazed habitable rooms: {s['average_daylight_ratio']*100:.1f}% "
        f"(target {DAYLIGHT_TARGET*100:.0f}% of floor area, areas in {unit})"
    )
    if s["rooms_below_target"]:
        lines.append(f"  Below target: {', '.join(s['rooms_below_target'])}")
    return "\n".join(lines)
