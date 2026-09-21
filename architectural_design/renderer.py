"""2D architectural floor-plan renderer, built on matplotlib.

Draws building and interior walls (with gaps for doors and windows), room
fills colour-coded by room type, room name/area labels, furniture glyphs,
dimension lines, a compass-correct north arrow and a scale bar.

Two styles are available:

* ``modern``   - white sheet, black line work, blue window glazing.
* ``heritage`` - the 1931 Dutch drawing idiom: aged linen paper, sepia
  ink, solid poché walls, muted tinted rooms and a period title block.

Windows carry their real width and number of *lights* (panes), so the
divided upper lights typical of the 1931 facades read on the plan.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # headless rendering - no display needed
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, Polygon, Rectangle

from .heritage import HERITAGE_ROOM_COLORS, PROVENANCE, style_for
from .models import (
    Building,
    Door,
    Room,
    RoomType,
    Storey,
    Window,
    area_label,
    bearing_to_vector,
    compass_name,
)

ROOM_COLORS = {
    RoomType.BEDROOM: "#eef3fb",
    RoomType.MASTER_BEDROOM: "#e5edf9",
    RoomType.LIVING_ROOM: "#fbf3e6",
    RoomType.SALON: "#faf0e2",
    RoomType.KITCHEN: "#eaf6ea",
    RoomType.DINING_ROOM: "#fdf0e9",
    RoomType.BATHROOM: "#e7f6f8",
    RoomType.TOILET: "#eaf4f6",
    RoomType.OFFICE: "#f3eef8",
    RoomType.HALLWAY: "#f2f2f2",
    RoomType.LANDING: "#f2f2f2",
    RoomType.CLOSET: "#ececec",
    RoomType.STORAGE: "#ececec",
    RoomType.LAUNDRY: "#eef2f5",
    RoomType.GARAGE: "#e6e6e6",
    RoomType.ENTRY: "#f7f2e9",
    RoomType.ATTIC: "#f1eee8",
    RoomType.BALCONY: "#eef0ea",
    RoomType.BAY: "#faf0e2",
    RoomType.GENERIC: "#f0f0f0",
}


def _room_colors(style_name: str) -> Dict:
    return HERITAGE_ROOM_COLORS if str(style_name).lower().startswith("herit") else ROOM_COLORS


# ---------------------------------------------------------------------------
# Wall / opening drawing
# ---------------------------------------------------------------------------


def _draw_wall_with_openings(ax, x1, y1, x2, y2, openings, st, lw=None):
    """Draw a wall segment, leaving gaps for `openings` given as
    (start_frac, end_frac) pairs along the segment."""
    color = st["ink"]
    lw = lw if lw is not None else 2.2
    if not openings:
        ax.add_line(Line2D([x1, x2], [y1, y2], color=color, linewidth=lw, solid_capstyle="butt", zorder=5))
        return
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 1e-9:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    cursor = 0.0
    for s, e in sorted(openings):
        s, e = max(0.0, s), min(1.0, e)
        if s > cursor:
            ax.add_line(
                Line2D(
                    [x1 + dx * cursor * length, x1 + dx * s * length],
                    [y1 + dy * cursor * length, y1 + dy * s * length],
                    color=color, linewidth=lw, solid_capstyle="butt", zorder=5,
                )
            )
        cursor = max(cursor, e)
    if cursor < 1.0:
        ax.add_line(
            Line2D(
                [x1 + dx * cursor * length, x2],
                [y1 + dy * cursor * length, y2],
                color=color, linewidth=lw, solid_capstyle="butt", zorder=5,
            )
        )


def _wall_endpoints(room: Room, side: str):
    r = room.rect
    return {
        "S": (r.x, r.y, r.x2, r.y),
        "N": (r.x, r.y2, r.x2, r.y2),
        "W": (r.x, r.y, r.x, r.y2),
        "E": (r.x2, r.y, r.x2, r.y2),
    }[side]


def _draw_window(ax, room: Room, win: Window, st, jamb: float):
    """Draw a window in the architectural plan convention: the opening is
    blanked out of the wall, the frame is drawn as a pair of lines across
    it, and one tick is drawn per *light* (pane) - which is what gives the
    1931 openings, with their divided upper lights, their period reading.

    `jamb` is the drawn half-thickness of the wall, in plan units.
    """
    r = room.rect
    half = win.width / 2
    x1, y1, _, _ = _wall_endpoints(room, win.side)
    lights = max(1, win.lights)
    horizontal = win.side in ("N", "S")

    if horizontal:
        a, b = r.x + win.position - half, r.x + win.position + half
        # blank the wall through the opening, then draw the frame
        ax.add_line(Line2D([a, b], [y1, y1], color=st["paper"], linewidth=5.0,
                           solid_capstyle="butt", zorder=6))
        for off in (-jamb, jamb):
            ax.add_line(Line2D([a, b], [y1 + off, y1 + off], color=st["glass"],
                               linewidth=1.1, solid_capstyle="butt", zorder=7))
        ax.add_line(Line2D([a, b], [y1, y1], color=st["glass"], linewidth=0.8, zorder=7))
        ax.add_line(Line2D([a, a], [y1 - jamb, y1 + jamb], color=st["ink"], linewidth=1.2, zorder=7))
        ax.add_line(Line2D([b, b], [y1 - jamb, y1 + jamb], color=st["ink"], linewidth=1.2, zorder=7))
        for i in range(1, lights):
            xm = a + (b - a) * i / lights
            ax.add_line(Line2D([xm, xm], [y1 - jamb, y1 + jamb], color=st["glass"],
                               linewidth=0.7, zorder=7))
    else:
        a, b = r.y + win.position - half, r.y + win.position + half
        ax.add_line(Line2D([x1, x1], [a, b], color=st["paper"], linewidth=5.0,
                           solid_capstyle="butt", zorder=6))
        for off in (-jamb, jamb):
            ax.add_line(Line2D([x1 + off, x1 + off], [a, b], color=st["glass"],
                               linewidth=1.1, solid_capstyle="butt", zorder=7))
        ax.add_line(Line2D([x1, x1], [a, b], color=st["glass"], linewidth=0.8, zorder=7))
        ax.add_line(Line2D([x1 - jamb, x1 + jamb], [a, a], color=st["ink"], linewidth=1.2, zorder=7))
        ax.add_line(Line2D([x1 - jamb, x1 + jamb], [b, b], color=st["ink"], linewidth=1.2, zorder=7))
        for i in range(1, lights):
            ym = a + (b - a) * i / lights
            ax.add_line(Line2D([x1 - jamb, x1 + jamb], [ym, ym], color=st["glass"],
                               linewidth=0.7, zorder=7))


def _draw_door_symbol(ax, room: Room, door: Door, st):
    r = room.rect
    length = r.w if door.side in ("N", "S") else r.h
    half = door.width / 2
    lo = max(0.0, door.position - half)
    hi = min(length, door.position + half)
    w = hi - lo
    if w <= 0:
        return
    color = st["ink_light"]

    if door.kind == "sliding":
        # Ensuite sliding doors (schuifdeuren): a pair of parallel leaves.
        if door.side in ("N", "S"):
            y = r.y if door.side == "S" else r.y2
            ax.add_line(Line2D([r.x + lo, r.x + lo + w / 2], [y, y], color=color, linewidth=2.0, zorder=6))
            off = r.h * 0.012
            ax.add_line(
                Line2D([r.x + lo + w / 2, r.x + hi], [y + off, y + off], color=color, linewidth=2.0, zorder=6)
            )
        else:
            x = r.x if door.side == "W" else r.x2
            ax.add_line(Line2D([x, x], [r.y + lo, r.y + lo + w / 2], color=color, linewidth=2.0, zorder=6))
            off = r.w * 0.012
            ax.add_line(
                Line2D([x + off, x + off], [r.y + lo + w / 2, r.y + hi], color=color, linewidth=2.0, zorder=6)
            )
        return

    if door.kind == "opening":  # cased opening, no leaf
        return

    if door.side == "S":
        hinge, end, theta = (r.x + lo, r.y), (r.x + lo, r.y + w), (0, 90)
    elif door.side == "N":
        hinge, end, theta = (r.x + lo, r.y2), (r.x + lo, r.y2 - w), (270, 360)
    elif door.side == "W":
        hinge, end, theta = (r.x, r.y + lo), (r.x + w, r.y + lo), (0, 90)
    else:  # E
        hinge, end, theta = (r.x2, r.y + lo), (r.x2 - w, r.y + lo), (90, 180)

    lw = 1.3 if door.kind == "front_door" else 1.0
    ax.add_line(Line2D([hinge[0], end[0]], [hinge[1], end[1]], color=color, linewidth=lw, zorder=6))
    ax.add_patch(
        Arc(hinge, 2 * w, 2 * w, angle=0, theta1=theta[0], theta2=theta[1],
            color=color, linewidth=lw * 0.8, zorder=6)
    )


def _draw_furniture(ax, room: Room, st, label_min: float):
    for item in room.furniture:
        r = item.rect
        ax.add_patch(
            Rectangle(
                (r.x, r.y), r.w, r.h,
                facecolor=item.color, edgecolor=st["furniture_edge"],
                linewidth=0.7, alpha=0.92, zorder=3,
            )
        )
        if item.kind == "stair":
            # treads
            n = 7
            if r.w >= r.h:
                for i in range(1, n):
                    x = r.x + r.w * i / n
                    ax.add_line(Line2D([x, x], [r.y, r.y2], color=st["furniture_edge"],
                                       linewidth=0.5, zorder=4))
            else:
                for i in range(1, n):
                    y = r.y + r.h * i / n
                    ax.add_line(Line2D([r.x, r.x2], [y, y], color=st["furniture_edge"],
                                       linewidth=0.5, zorder=4))
        if min(r.w, r.h) > label_min:
            ax.text(
                r.center.x, r.center.y, item.name,
                ha="center", va="center", fontsize=5.4, color=st["text"], zorder=4,
            )


def _dimension_line(ax, x1, y1, x2, y2, text, st, offset=0.0):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color=st["ink_light"], linewidth=0.8),
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + offset, text, ha="center", va="center", fontsize=7.5, color=st["text"])


def _draw_north_arrow(ax, x, y, size, north_angle_deg, st):
    """North arrow pointing at the true bearing of north on this plan.

    `north_angle_deg` is the bearing of plan-up; north therefore lies at
    -north_angle_deg from plan-up on the sheet.
    """
    theta = math.radians(-north_angle_deg)
    dx, dy = math.sin(theta), math.cos(theta)
    px, py = -dy, dx  # perpendicular
    tip = (x + dx * size, y + dy * size)
    tail = (x - dx * size * 0.55, y - dy * size * 0.55)
    left = (tail[0] + px * size * 0.28, tail[1] + py * size * 0.28)
    right = (tail[0] - px * size * 0.28, tail[1] - py * size * 0.28)
    ax.add_patch(Polygon([tip, left, (tail[0], tail[1]), right],
                         closed=True, facecolor=st["ink"], edgecolor=st["ink"],
                         linewidth=0.8, zorder=8))
    ax.text(tip[0] + dx * size * 0.42, tip[1] + dy * size * 0.42, "N",
            ha="center", va="center", fontsize=9, fontweight="bold", color=st["ink"], zorder=8)


def _draw_title_block(ax, building: Building, storey: Optional[Storey], st, x, y, width):
    """Period title block for the heritage style."""
    lines = []
    if building.address:
        lines.append(building.address)
    meta = []
    if building.year_built:
        meta.append(str(building.year_built))
    if building.architect:
        meta.append(building.architect)
    if meta:
        lines.append(" · ".join(meta))
    if storey is not None:
        lines.append(f"{storey.name} — h = {storey.ceiling_height:.2f} m")
    if building.scale_note:
        lines.append(building.scale_note)
    facing = " ".join(f"{s}→{building.side_compass(s)}" for s in ("N", "E", "S", "W"))
    lines.append(f"Oriëntatie: {facing}")
    ax.text(x, y, "\n".join(lines), ha="left", va="top", fontsize=7.2,
            color=st["text"], family=st["title_font"], zorder=8, linespacing=1.6)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_floorplan_2d(
    building: Building,
    out_path: str,
    title: Optional[str] = None,
    dpi: int = 160,
    show_dims: bool = True,
    storey: Optional[Storey] = None,
    style: Optional[str] = None,
) -> str:
    """Render one storey's 2D floor plan and save it to `out_path`
    (the extension picks the format, e.g. .png or .svg)."""
    style_name = style or getattr(building, "style", "modern")
    st = style_for(style_name)
    colors = _room_colors(style_name)
    rooms = storey.rooms if storey is not None else building.rooms

    span = max(building.width, building.height)
    metric = building.units == "m"
    fig_scale = 3.5 if not metric else 1.1
    fig, ax = plt.subplots(
        figsize=(max(6.5, building.width / fig_scale + 3.2),
                 max(5.5, building.height / fig_scale + 3.0))
    )
    fig.patch.set_facecolor(st["paper"])
    ax.set_facecolor(st["paper"])

    # Exterior envelope
    ax.add_patch(
        Rectangle((0, 0), building.width, building.height,
                  fill=False, edgecolor=st["ink"], linewidth=3.0, zorder=7)
    )

    label_min = span * 0.035
    jamb = (0.055 if metric else 0.18)  # drawn half-thickness of a wall
    for room in rooms:
        r = room.rect
        color = colors.get(room.room_type, colors[RoomType.GENERIC])
        ax.add_patch(Rectangle((r.x, r.y), r.w, r.h, facecolor=color, edgecolor="none", zorder=1))

        for side in ("S", "N", "W", "E"):
            x1, y1, x2, y2 = _wall_endpoints(room, side)
            length = r.w if side in ("N", "S") else r.h
            openings = []
            for d in room.doors:
                if d.side == side:
                    half = d.width / 2
                    openings.append(((d.position - half) / length, (d.position + half) / length))
            for w in room.windows:
                if w.side == side:
                    half = w.width / 2
                    openings.append(((w.position - half) / length, (w.position + half) / length))
                    _draw_window(ax, room, w, st, jamb)
            _draw_wall_with_openings(ax, x1, y1, x2, y2, openings, st)

        for d in room.doors:
            _draw_door_symbol(ax, room, d, st)

        _draw_furniture(ax, room, st, label_min)

        c = r.center
        small = min(r.w, r.h) < span * 0.16
        name_fs = 6.4 if small else 8.6
        # A translucent backing keeps the label readable where it lands on
        # furniture (a bed or a counter often sits mid-room).
        backing = dict(boxstyle="round,pad=0.22", facecolor=st["paper"],
                       edgecolor="none", alpha=0.78)
        ax.text(c.x, c.y + span * (0.008 if small else 0.014), room.name,
                ha="center", va="center", fontsize=name_fs, fontweight="bold",
                color=st["text"], zorder=8, bbox=backing)
        if not small:
            area_txt = (f"{room.area:.1f} {area_label(building.units)}" if metric
                        else f"{room.area:.0f} {area_label(building.units)}")
            ax.text(c.x, c.y - span * 0.020, area_txt, ha="center", va="center",
                    fontsize=6.6, color=st["ink_light"], zorder=8, bbox=backing)
            if room.note:
                ax.text(c.x, c.y - span * 0.048, room.note, ha="center", va="center",
                        fontsize=5.8, style="italic", color=st["ink_light"],
                        zorder=8, bbox=backing)
        else:
            ax.text(c.x, c.y - span * 0.016,
                    f"{room.area:.1f}" if metric else f"{room.area:.0f}",
                    ha="center", va="center", fontsize=5.4, color=st["ink_light"],
                    zorder=8, bbox=backing)

    if show_dims:
        pad = span * 0.075 + (0.6 if metric else 1.0)
        unit = building.units
        _dimension_line(ax, 0, -pad, building.width, -pad,
                        f"{building.width:.2f} {unit}" if metric else f"{building.width:.1f} {unit}", st)
        _dimension_line(ax, -pad, 0, -pad, building.height,
                        f"{building.height:.2f} {unit}" if metric else f"{building.height:.1f} {unit}", st)

    # Blind party walls get a hatched band so they read as "no openings here".
    for side in building.blind_sides:
        x1, y1, x2, y2 = {
            "S": (0, 0, building.width, 0),
            "N": (0, building.height, building.width, building.height),
            "W": (0, 0, 0, building.height),
            "E": (building.width, 0, building.width, building.height),
        }[side]
        ax.add_line(Line2D([x1, x2], [y1, y2], color=st["ink"], linewidth=6.5,
                           alpha=0.35, solid_capstyle="butt", zorder=7))

    _draw_north_arrow(ax, building.width + span * 0.13, building.height * 0.86,
                      span * 0.075, building.north_angle_deg, st)

    # Scale bar
    bar = 5.0 if not metric else 2.0
    bx, by = 0.0, -(span * 0.075 + (1.5 if metric else 2.6))
    ax.add_line(Line2D([bx, bx + bar], [by, by], color=st["ink"], linewidth=2.5))
    for i in range(int(bar) + 1):
        ax.add_line(Line2D([bx + i, bx + i], [by - span * 0.008, by + span * 0.008],
                           color=st["ink"], linewidth=1.0))
    ax.text(bx + bar / 2, by - span * 0.030, f"{bar:.0f} {building.units}",
            ha="center", fontsize=7, color=st["text"])

    if str(style_name).lower().startswith("herit"):
        _draw_title_block(ax, building, storey, st,
                          building.width + span * 0.04, building.height * 0.62, span)

    heading = title or (f"{building.name} — {storey.name}" if storey else building.name)
    ax.set_xlim(-span * 0.18, building.width + span * 0.42)
    ax.set_ylim(-span * 0.30, building.height + span * 0.16)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(heading, fontsize=13, fontweight="bold", pad=14,
                 color=st["text"], family=st["title_font"])

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def render_all_storeys(building: Building, out_dir: str, slug: str,
                       style: Optional[str] = None, ext: str = "png", dpi: int = 160) -> List[str]:
    """Render every storey of a building; returns the written paths."""
    import os

    paths = []
    for storey in (building.storeys or [Storey(name="Ground floor", rooms=building.rooms)]):
        sslug = "".join(c.lower() if c.isalnum() else "_" for c in storey.name).strip("_")
        path = os.path.join(out_dir, f"{slug}_{storey.level}_{sslug}.{ext}")
        render_floorplan_2d(building, path, storey=storey, style=style, dpi=dpi)
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Daylight / orientation plan
# ---------------------------------------------------------------------------

#: Fill colours for the daylight ratings, light (poor) to saturated (generous).
_DAYLIGHT_FILL = {
    "generous": "#f2c14e",
    "adequate": "#f6dfa4",
    "borderline": "#dfe3e8",
    "serving": "#eceff2",
    "internal": "#cfd4da",
}


def render_daylight_plan(
    building: Building,
    out_path: str,
    storey: Optional[Storey] = None,
    dpi: int = 160,
    title: Optional[str] = None,
) -> str:
    """Shade each room by how well it is daylit and mark which way its
    windows face, with sun arrows for morning/midday/afternoon.

    Rooms are filled by their daylight rating (glazed area as a share of
    floor area), and each room is annotated with that percentage and the
    compass directions its windows look out on.
    """
    from .daylight import DAYLIGHT_TARGET, analyse_room

    st = style_for("modern")
    rooms = storey.rooms if storey is not None else building.rooms
    span = max(building.width, building.height)
    metric = building.units == "m"
    fig_scale = 3.5 if not metric else 1.1
    fig, ax = plt.subplots(
        figsize=(max(6.5, building.width / fig_scale + 3.4),
                 max(5.5, building.height / fig_scale + 3.0))
    )

    for room in rooms:
        d = analyse_room(room, building.north_angle_deg, storey.name if storey else "")
        r = room.rect
        ax.add_patch(Rectangle((r.x, r.y), r.w, r.h,
                               facecolor=_DAYLIGHT_FILL.get(d.rating, "#e6e6e6"),
                               edgecolor="#333333", linewidth=1.2, zorder=2))
        for w in room.windows:
            _draw_window(ax, room, w, st, 0.055 if metric else 0.18)

        c = r.center
        small = min(r.w, r.h) < span * 0.16
        ax.text(c.x, c.y + span * 0.018, room.name, ha="center", va="center",
                fontsize=6.2 if small else 8.2, fontweight="bold", color="#1e1e1e", zorder=6)
        if not small:
            ax.text(c.x, c.y - span * 0.008, f"{d.ratio*100:.0f}% daylight",
                    ha="center", va="center", fontsize=6.8, color="#333333", zorder=6)
            facing = "/".join(d.orientations) if d.orientations else "no window"
            ax.text(c.x, c.y - span * 0.032, facing, ha="center", va="center",
                    fontsize=6.2, style="italic", color="#555555", zorder=6)

    ax.add_patch(Rectangle((0, 0), building.width, building.height, fill=False,
                           edgecolor="black", linewidth=2.6, zorder=7))
    for side in building.blind_sides:
        x1, y1, x2, y2 = {
            "S": (0, 0, building.width, 0),
            "N": (0, building.height, building.width, building.height),
            "W": (0, 0, 0, building.height),
            "E": (building.width, 0, building.width, building.height),
        }[side]
        ax.add_line(Line2D([x1, x2], [y1, y2], color="#444444", linewidth=7.0,
                           alpha=0.45, solid_capstyle="butt", zorder=7))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + (span * 0.045 if side == "E" else -span * 0.045 if side == "W" else 0),
                my + (span * 0.04 if side == "N" else -span * 0.04 if side == "S" else 0),
                "party wall", rotation=90 if side in ("E", "W") else 0,
                ha="center", va="center", fontsize=6.5, color="#555555", zorder=8)

    # Sun arrows: where the sun comes from at three times of day.
    for bearing, label, color in ((90.0, "morning", "#e8a33d"),
                                  (180.0, "midday", "#d8791f"),
                                  (270.0, "afternoon", "#b4571f")):
        # Direction on the sheet that this compass bearing points to.
        theta = math.radians(bearing - building.north_angle_deg)
        dx, dy = math.sin(theta), math.cos(theta)
        # Arrow flies from outside the plan towards the building centre.
        cx, cy = building.width / 2, building.height / 2
        start = (cx + dx * span * 0.82, cy + dy * span * 0.82)
        end = (cx + dx * span * 0.66, cy + dy * span * 0.66)
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color=color, linewidth=2.0), zorder=9)
        ax.text(start[0] + dx * span * 0.07, start[1] + dy * span * 0.07, label,
                ha="center", va="center", fontsize=7, color=color, zorder=9)

    _draw_north_arrow(ax, -span * 0.20, building.height * 0.95,
                      span * 0.07, building.north_angle_deg, st)

    legend = [
        f"generous (≥ 18%)", f"adequate (≥ {DAYLIGHT_TARGET*100:.0f}%)",
        "borderline", "serving space", "internal (no window)",
    ]
    for i, (key, text) in enumerate(zip(
            ["generous", "adequate", "borderline", "serving", "internal"], legend)):
        y = building.height - i * span * 0.075
        x = building.width + span * 0.22
        ax.add_patch(Rectangle((x, y - span * 0.028), span * 0.055, span * 0.045,
                               facecolor=_DAYLIGHT_FILL[key], edgecolor="#333333", linewidth=0.8))
        ax.text(x + span * 0.075, y - span * 0.006, text, fontsize=6.8,
                ha="left", va="center", color="#333333")

    heading = title or (
        f"{building.name} — {storey.name} — daylight & orientation"
        if storey is not None else f"{building.name} — daylight & orientation"
    )
    ax.set_xlim(-span * 0.34, building.width + span * 0.70)
    ax.set_ylim(-span * 0.26, building.height + span * 0.26)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(heading, fontsize=12.5, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path
