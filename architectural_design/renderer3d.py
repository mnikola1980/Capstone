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

from .heritage import style_for
from .models import Building, Room, RoomType, Storey
from .renderer import _room_colors

WALL_HEIGHT_M = 2.74      # storey height used for the extrusion
FURNITURE_HEIGHT_M = 0.76  # generic box height for furniture glyphs


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
    wall_height: Optional[float] = None,
    elev: float = 42,
    azim: float = -55,
    cutaway: bool = True,
    storey: Optional[Storey] = None,
    style: Optional[str] = None,
) -> str:
    """Render a pseudo-3D isometric massing view of the building and save it.

    If `cutaway` is True, exterior walls facing the camera are left off so
    the interior (rooms + furniture) is visible, like a doll-house view.
    """
    style_name = style or getattr(building, "style", "modern")
    st = style_for(style_name)
    colors = _room_colors(style_name)
    scale = 3.280839895013123 if building.units == "ft" else 1.0
    if wall_height is None:
        wall_height = (storey.ceiling_height if storey is not None else WALL_HEIGHT_M) * scale
    furniture_height = FURNITURE_HEIGHT_M * scale
    rooms = storey.rooms if storey is not None else building.rooms

    fig = plt.figure(figsize=(9, 7.5))
    fig.patch.set_facecolor(st["paper"])
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(st["paper"])

    for room in rooms:
        r = room.rect
        color = colors.get(room.room_type, colors[RoomType.GENERIC])
        # Floor slab
        slab = 0.05 * scale
        _add_box(ax, r.x, r.y, -slab, r.w, r.h, slab,
                 facecolor=st["paper_edge"], alpha=1.0, faces=["top"], edgecolor=st["ink_light"])
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
                furniture_height * 0.55 if item.kind in ("table", "console", "bench") else furniture_height,
                facecolor=item.color,
                alpha=0.95,
            )

    ax.set_xlim(0, building.width)
    ax.set_ylim(0, building.height)
    ax.set_zlim(0, max(building.width, building.height) * 0.5)
    ax.set_box_aspect((building.width, building.height, max(building.width, building.height) * 0.45))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    heading = title or (
        f"{building.name} \u2014 {storey.name} \u2014 3D massing view" if storey is not None
        else f"{building.name} \u2014 3D massing view"
    )
    ax.set_title(heading, fontsize=13, fontweight="bold", color=st["text"], family=st["title_font"])

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path
