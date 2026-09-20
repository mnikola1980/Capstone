"""
architectural_design
=====================

A small toolkit for generating architectural interior floor-plan layouts
and rendering them as 2D and pseudo-3D visuals.

Pipeline:
    JSON spec -> layout.generate_layout()      -> Building (rooms placed, no overlaps)
              -> furniture_placer.furnish()     -> Building (furniture added per room)
              -> renderer.render_floorplan_2d() -> PNG/SVG floor plan
              -> renderer3d.render_isometric()  -> PNG pseudo-3D view
"""

from .models import Point, Rect, Door, Window, FurnitureItem, Room, Building, RoomSpec

__all__ = [
    "Point",
    "Rect",
    "Door",
    "Window",
    "FurnitureItem",
    "Room",
    "Building",
    "RoomSpec",
]

__version__ = "0.1.0"
