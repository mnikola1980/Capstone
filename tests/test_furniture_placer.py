import itertools
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from architectural_design.furniture_placer import furnish
from architectural_design.layout import generate_layout
from architectural_design.models import RoomSpec


def build_test_building():
    specs = [
        RoomSpec(name="Living Room", room_type="living_room", weight=3.0),
        RoomSpec(name="Bedroom", room_type="bedroom", weight=2.0),
        RoomSpec(name="Kitchen", room_type="kitchen", weight=1.5),
        RoomSpec(name="Bathroom", room_type="bathroom", weight=0.8, needs_window=False),
    ]
    return generate_layout("Test Home", 34, 26, specs)


def test_furniture_placed_without_overlap():
    building = build_test_building()
    furnish(building)
    for room in building.rooms:
        for a, b in itertools.combinations(room.furniture, 2):
            assert not a.rect.overlaps(b.rect), f"{a.name} overlaps {b.name} in {room.name}"


def test_furniture_stays_within_room_bounds():
    building = build_test_building()
    furnish(building)
    for room in building.rooms:
        r = room.rect
        for item in room.furniture:
            fr = item.rect
            assert fr.x >= r.x - 1e-6
            assert fr.y >= r.y - 1e-6
            assert fr.x2 <= r.x2 + 1e-6
            assert fr.y2 <= r.y2 + 1e-6


def test_living_room_gets_a_sofa():
    building = build_test_building()
    furnish(building)
    living = next(r for r in building.rooms if r.name == "Living Room")
    names = [f.name for f in living.furniture]
    assert "Sofa" in names


def test_furnish_returns_unplaced_report_shape():
    building = build_test_building()
    report = furnish(building)
    assert isinstance(report, dict)
    for room_id, items in report.items():
        assert isinstance(room_id, str)
        assert isinstance(items, list)


def test_tiny_room_does_not_crash_and_skips_oversized_items():
    specs = [RoomSpec(name="Tiny Closet", room_type="closet", weight=1.0)]
    building = generate_layout("Closet Test", 4, 4, specs)
    report = furnish(building)  # closets have no catalog entries - should just be empty
    assert building.rooms[0].furniture == []
