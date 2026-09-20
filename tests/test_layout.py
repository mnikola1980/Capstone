import itertools
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from architectural_design.layout import generate_layout
from architectural_design.models import RoomSpec


def make_specs():
    return [
        RoomSpec(name="Living Room", room_type="living_room", weight=3.0),
        RoomSpec(name="Bedroom", room_type="bedroom", weight=2.0),
        RoomSpec(name="Kitchen", room_type="kitchen", weight=1.5),
        RoomSpec(name="Bathroom", room_type="bathroom", weight=0.8, needs_window=False),
    ]


def test_generates_one_room_per_spec():
    building = generate_layout("Test Home", 30, 24, make_specs())
    assert len(building.rooms) == len(make_specs())


def test_rooms_do_not_overlap():
    building = generate_layout("Test Home", 30, 24, make_specs())
    for a, b in itertools.combinations(building.rooms, 2):
        assert not a.rect.overlaps(b.rect), f"{a.name} overlaps {b.name}"


def test_rooms_within_building_bounds():
    building = generate_layout("Test Home", 30, 24, make_specs())
    for r in building.rooms:
        assert r.rect.x >= -1e-6
        assert r.rect.y >= -1e-6
        assert r.rect.x2 <= building.width + 1e-6
        assert r.rect.y2 <= building.height + 1e-6


def test_total_room_area_matches_footprint():
    building = generate_layout("Test Home", 30, 24, make_specs())
    assert building.total_room_area() == pytest.approx(building.footprint_area(), rel=1e-6)


def test_area_proportional_to_weight():
    building = generate_layout("Test Home", 30, 24, make_specs())
    by_name = {r.name: r.area for r in building.rooms}
    # Living room (weight 3.0) should end up bigger than bathroom (weight 0.8)
    assert by_name["Living Room"] > by_name["Bathroom"]
    total_weight = sum(s.weight for s in make_specs())
    total_area = building.footprint_area()
    for spec in make_specs():
        expected = total_area * (spec.weight / total_weight)
        assert by_name[spec.name] == pytest.approx(expected, rel=1e-6)


def test_every_room_has_at_least_one_door():
    building = generate_layout("Test Home", 30, 24, make_specs())
    for r in building.rooms:
        assert len(r.doors) >= 1, f"{r.name} has no door"


def test_rejects_empty_spec_list():
    with pytest.raises(ValueError):
        generate_layout("Empty", 10, 10, [])


def test_rejects_nonpositive_dimensions():
    with pytest.raises(ValueError):
        generate_layout("Bad", 0, 10, make_specs())


def test_single_room_fills_envelope():
    specs = [RoomSpec(name="Studio", room_type="living_room", weight=1.0)]
    building = generate_layout("One Room", 20, 15, specs)
    assert len(building.rooms) == 1
    r = building.rooms[0].rect
    assert r.x == 0 and r.y == 0
    assert r.w == pytest.approx(20)
    assert r.h == pytest.approx(15)
