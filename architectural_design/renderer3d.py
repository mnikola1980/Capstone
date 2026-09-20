"""Pseudo-3D / isometric interior visual.

Extrudes each room's floor rectangle upward into wall panels and renders
furniture as boxes, using matplotlib's mplot3d. This is not a
physically-based renderer, but gives a quick, presentable 3D massing view
of the generated layout without pulling in a full 3D graphics stack.
"""

from __future__ import annotations

from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .models import Building, Room
from .renderer import ROOM_COLORS

WALL_HEIGHT = 9.0  # feet
FURNITURE_HEIGHT = 2.5  # feet, generic box height for furniture glyphs


def _box_faces(x, y, z, w, d, h):
    """Return the 6 quad faces of an axis-aligned box as lists of (x,y,z) verts."""
    x0, x1 = x, x + w
    y0, y1 = y, y + d
    z0, z1 = z, z + h
    verts = {
        "bottom": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        "top": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "s": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        "n": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "w": [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
        "e": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
    }
    return verts


def _add_box(ax, x, y, z, w, d, h, facecolor, alpha=1.0, edgecolor="#333333", linewidth=0.3, faces=None):
    verts = _box_faces(x, y, z, w, d, h)
    keys = faces or list(verts.keys())
    polys = [verts[k] for k in keys]
    coll = Poly3DCollection(polys, facecolor=facecolor, edgecolor=edgecolor, linewidths=linewidth, alpha=alpha)
    ax.add_collection3d(coll)


def render_isometric(
    building: Building,
    out_path: str,
    title: Optional[str] = None,
    dpi: int = 160,
    wall_height: float = WALL_HEIGHT,
    elev: float = 42,
    azim: float = -55,
    cutaway: bool = True,
) -> str:
    """Render a pseudo-3D isometric massing view of the building and save it.

    If `cutaway` is True, exterior walls facing the camera are left off so
    the interior (rooms + furniture) is visible, like a doll-house view.
    """
    fig = plt.figure(figsize=(9, 7.5))
    ax = fig.add_subplot(111, projection="3d")

    for room in building.rooms:
        r = room.rect
        color = ROOM_COLORS.get(room.room_type, ROOM_COLORS[room.room_type.GENERIC])
        # Floor slab
        _add_box(ax, r.x, r.y, -0.15, r.w, r.h, 0.15, facecolor="#d9cdb8", alpha=1.0, faces=["top"])
        # Perimeter walls, thin shells, skip faces on the building's exterior
        # boundary on the "front" (south/west) so we can see inside.
        wall_faces = []
        eps = 1e-6
        touches_s = r.y <= eps
        touches_w = r.x <= eps
        if not (cutaway and touches_s):
            wall_faces.append("s")
        if not (cutaway and touches_w):
            wall_faces.append("w")
        wall_faces += ["n", "e"]
        _add_box(
            ax,
            r.x,
            r.y,
            0,
            r.w,
            r.h,
            wall_height,
            facecolor=color,
            alpha=0.35,
            faces=wall_faces,
        )

        for item in room.furniture:
            fr = item.rect
            _add_box(
                ax,
                fr.x,
                fr.y,
                0,
                fr.w,
                fr.h,
                FURNITURE_HEIGHT * 0.55 if item.kind in ("table", "console", "bench") else FURNITURE_HEIGHT,
                facecolor=item.color,
                alpha=0.95,
            )

    ax.set_xlim(0, building.width)
    ax.set_ylim(0, building.height)
    ax.set_zlim(0, max(building.width, building.height) * 0.5)
    ax.set_box_aspect((building.width, building.height, max(building.width, building.height) * 0.45))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title or f"{building.name} — 3D massing view", fontsize=13, fontweight="bold")

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path
