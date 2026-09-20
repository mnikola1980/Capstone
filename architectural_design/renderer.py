"""2D architectural floor-plan renderer, built on matplotlib.

Draws building + interior walls (with gaps for doors and windows), room
fills color-coded by room type, room name/area labels, simple furniture
glyphs, dimension lines, a north arrow and a scale bar, then saves to
PNG/SVG.
"""

from __future__ import annotations

from typing import Optional

import matplotlib

matplotlib.use("Agg")  # headless rendering - no display needed
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrow, Rectangle
from matplotlib.lines import Line2D

from .models import Building, Door, Room, RoomType, Window

WALL_THICKNESS = 0.35  # feet, drawing weight only

ROOM_COLORS = {
    RoomType.BEDROOM: "#eef3fb",
    RoomType.MASTER_BEDROOM: "#e5edf9",
    RoomType.LIVING_ROOM: "#fbf3e6",
    RoomType.KITCHEN: "#eaf6ea",
    RoomType.DINING_ROOM: "#fdf0e9",
    RoomType.BATHROOM: "#e7f6f8",
    RoomType.OFFICE: "#f3eef8",
    RoomType.HALLWAY: "#f2f2f2",
    RoomType.CLOSET: "#ececec",
    RoomType.LAUNDRY: "#eef2f5",
    RoomType.GARAGE: "#e6e6e6",
    RoomType.ENTRY: "#f7f2e9",
    RoomType.GENERIC: "#f0f0f0",
}


def _draw_wall_with_openings(ax, x1, y1, x2, y2, openings):
    """Draw a wall segment from (x1,y1)-(x2,y2), leaving gaps for `openings`,
    a list of (start_frac, end_frac) along the segment to skip."""
    if not openings:
        ax.add_line(Line2D([x1, x2], [y1, y2], color="black", linewidth=2.2, solid_capstyle="butt"))
        return
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if length < 1e-9:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    openings = sorted(openings)
    cursor = 0.0
    for s, e in openings:
        s, e = max(0.0, s), min(1.0, e)
        if s > cursor:
            ax.add_line(
                Line2D(
                    [x1 + dx * cursor * length, x1 + dx * s * length],
                    [y1 + dy * cursor * length, y1 + dy * s * length],
                    color="black",
                    linewidth=2.2,
                    solid_capstyle="butt",
                )
            )
        cursor = max(cursor, e)
    if cursor < 1.0:
        ax.add_line(
            Line2D(
                [x1 + dx * cursor * length, x2],
                [y1 + dy * cursor * length, y2],
                color="black",
                linewidth=2.2,
                solid_capstyle="butt",
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


def _draw_door_symbol(ax, room: Room, door: Door):
    r = room.rect
    length = room.rect.w if door.side in ("N", "S") else room.rect.h
    half = door.width / 2
    lo = max(0.0, door.position - half)
    hi = min(length, door.position + half)
    w = hi - lo
    if w <= 0:
        return
    if door.side == "S":
        hinge = (r.x + lo, r.y)
        end = (r.x + lo, r.y + w)
        theta1, theta2 = 0, 90
    elif door.side == "N":
        hinge = (r.x + lo, r.y2)
        end = (r.x + lo, r.y2 - w)
        theta1, theta2 = 270, 360
    elif door.side == "W":
        hinge = (r.x, r.y + lo)
        end = (r.x + w, r.y + lo)
        theta1, theta2 = 0, 90
    else:  # E
        hinge = (r.x2, r.y + lo)
        end = (r.x2 - w, r.y + lo)
        theta1, theta2 = 90, 180

    ax.add_line(Line2D([hinge[0], end[0]], [hinge[1], end[1]], color="#5a5a5a", linewidth=1.0))
    ax.add_patch(
        Arc(hinge, 2 * w, 2 * w, angle=0, theta1=theta1, theta2=theta2, color="#5a5a5a", linewidth=1.0)
    )


def _draw_furniture(ax, room: Room):
    for item in room.furniture:
        r = item.rect
        ax.add_patch(
            Rectangle(
                (r.x, r.y),
                r.w,
                r.h,
                facecolor=item.color,
                edgecolor="#3a3a3a",
                linewidth=0.8,
                alpha=0.9,
                zorder=3,
            )
        )
        if min(r.w, r.h) > 1.2:
            ax.text(
                r.center.x,
                r.center.y,
                item.name,
                ha="center",
                va="center",
                fontsize=5.5,
                color="#2a2a2a",
                zorder=4,
                wrap=True,
            )


def _dimension_line(ax, x1, y1, x2, y2, text, offset=0.0):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color="#555555", linewidth=0.8),
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + offset, text, ha="center", va="center", fontsize=7, color="#333333")


def render_floorplan_2d(
    building: Building,
    out_path: str,
    title: Optional[str] = None,
    dpi: int = 160,
    show_dims: bool = True,
) -> str:
    """Render the building's 2D floor plan and save it to `out_path`
    (extension picks the format, e.g. .png or .svg). Returns out_path."""
    fig, ax = plt.subplots(figsize=(max(6, building.width / 3.5 + 2), max(5, building.height / 3.5 + 2)))

    # Exterior envelope
    ax.add_patch(
        Rectangle(
            (0, 0),
            building.width,
            building.height,
            fill=False,
            edgecolor="black",
            linewidth=3.0,
            zorder=5,
        )
    )

    for room in building.rooms:
        r = room.rect
        color = ROOM_COLORS.get(room.room_type, ROOM_COLORS[RoomType.GENERIC])
        ax.add_patch(Rectangle((r.x, r.y), r.w, r.h, facecolor=color, edgecolor="none", zorder=1))

        for side in ("S", "N", "W", "E"):
            x1, y1, x2, y2 = _wall_endpoints(room, side)
            length = room.rect.w if side in ("N", "S") else room.rect.h
            openings = []
            for d in room.doors:
                if d.side == side:
                    half = d.width / 2
                    openings.append(((d.position - half) / length, (d.position + half) / length))
            for w in room.windows:
                if w.side == side:
                    half = w.width / 2
                    openings.append(((w.position - half) / length, (w.position + half) / length))
                    # draw a thin double-line to mark the window in the gap
                    if side in ("N", "S"):
                        wx1, wx2 = x1 + (w.position - half), x1 + (w.position + half)
                        ax.add_line(Line2D([wx1, wx2], [y1, y1], color="#4a90d9", linewidth=3.0, zorder=2))
                    else:
                        wy1, wy2 = y1 + (w.position - half), y1 + (w.position + half)
                        ax.add_line(Line2D([x1, x1], [wy1, wy2], color="#4a90d9", linewidth=3.0, zorder=2))
            _draw_wall_with_openings(ax, x1, y1, x2, y2, openings)

        for d in room.doors:
            _draw_door_symbol(ax, room, d)

        _draw_furniture(ax, room)

        c = room.center = room.rect.center
        ax.text(
            c.x,
            c.y + 0.35,
            room.name,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#222222",
            zorder=6,
        )
        ax.text(
            c.x,
            c.y - 0.35,
            f"{room.area:.0f} sq {building.units}",
            ha="center",
            va="center",
            fontsize=7,
            color="#555555",
            zorder=6,
        )

    if show_dims:
        pad = max(building.width, building.height) * 0.06 + 1.0
        _dimension_line(ax, 0, -pad, building.width, -pad, f"{building.width:.1f} {building.units}")
        _dimension_line(
            ax, -pad, 0, -pad, building.height, f"{building.height:.1f} {building.units}"
        )

    # North arrow
    nx, ny = building.width + 1.2, building.height - 1.5
    if nx < building.width + 3:
        ax.annotate(
            "N",
            xy=(nx, ny + 1.2),
            xytext=(nx, ny),
            ha="center",
            fontsize=9,
            fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", linewidth=1.5, color="black"),
        )

    # Scale bar (5 units)
    bar_len = 5.0
    bx, by = 0.5, -3.2 if show_dims else -1.5
    ax.add_line(Line2D([bx, bx + bar_len], [by, by], color="black", linewidth=2))
    ax.text(bx + bar_len / 2, by - 0.6, f"{bar_len:.0f} {building.units}", ha="center", fontsize=7)

    ax.set_xlim(-4, building.width + 4)
    ax.set_ylim(-5, building.height + 3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title or building.name, fontsize=13, fontweight="bold", pad=14)

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path
