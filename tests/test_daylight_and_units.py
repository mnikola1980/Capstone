"""Tests for the daylight/orientation calculation and metric unit handling."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from architectural_design.daylight import (
    DAYLIGHT_TARGET,
    analyse_room,
    sun_periods,
)
from architectural_design.furniture_catalog import catalog_for
from architectural_design.models import (
    FT_PER_M,
    Building,
    Rect,
    Room,
    RoomType,
    Storey,
    Window,
    compass_bearing,
    to_units,
)


def _room(width=4.0, height=5.0, windows=()):
    return Room(id="r", name="Room", room_type=RoomType.LIVING_ROOM,
                rect=Rect(0, 0, width, height), windows=list(windows))


# --------------------------------------------------------------- orientation


def test_compass_bearing_with_north_up_plan():
    assert compass_bearing("N", 0) == 0
    assert compass_bearing("E", 0) == 90
    assert compass_bearing("S", 0) == 180
    assert compass_bearing("W", 0) == 270


def test_compass_bearing_with_rotated_plan():
    # Plan drawn with "up" facing west: the top wall then faces west.
    assert compass_bearing("N", 270) == 270
    assert compass_bearing("S", 270) == 90
    assert compass_bearing("E", 270) == 0
    assert compass_bearing("W", 270) == 180


def test_sun_periods_by_facade():
    assert "morning sun" in sun_periods(90)      # east
    assert "midday sun" in sun_periods(180)      # south
    assert "afternoon sun" in sun_periods(270)   # west
    assert sun_periods(0) == ["no direct sun"]   # north


# ------------------------------------------------------------------ daylight


def test_daylight_ratio_is_glazing_over_floor_area():
    win = Window(side="S", position=2.0, width=2.0, height=1.5)
    room = _room(4.0, 5.0, [win])           # 20 m2 floor, 3 m2 glazing
    d = analyse_room(room, north_angle_deg=0)
    assert d.glazed_area == pytest.approx(3.0)
    assert d.floor_area == pytest.approx(20.0)
    assert d.ratio == pytest.approx(0.15)
    assert d.meets_target


def test_room_below_target_is_flagged():
    win = Window(side="S", position=2.0, width=1.0, height=1.0)
    d = analyse_room(_room(4.0, 5.0, [win]), north_angle_deg=0)
    assert d.ratio == pytest.approx(0.05)
    assert not d.meets_target
    assert d.rating == "borderline"


def test_room_without_windows_is_internal():
    d = analyse_room(_room(), north_angle_deg=0)
    assert d.window_count == 0
    assert d.rating == "internal"
    assert d.ratio == 0.0


def test_serving_rooms_are_not_judged_against_the_target():
    room = Room(id="h", name="Hal", room_type=RoomType.HALLWAY,
                rect=Rect(0, 0, 2, 3),
                windows=[Window(side="S", position=1.0, width=0.5, height=0.5)])
    d = analyse_room(room, north_angle_deg=0)
    assert not d.habitable
    assert d.rating == "serving"


def test_window_orientation_follows_the_plan_rotation():
    win = Window(side="N", position=2.0, width=2.0, height=1.5)
    room = _room(4.0, 5.0, [win])
    assert analyse_room(room, north_angle_deg=0).orientations == ["N"]
    assert analyse_room(room, north_angle_deg=270).orientations == ["W"]


def test_target_is_the_dutch_ten_percent_rule():
    assert DAYLIGHT_TARGET == pytest.approx(0.10)


# --------------------------------------------------------------------- units


def test_to_units_conversion():
    assert to_units(1.0, "m") == pytest.approx(1.0)
    assert to_units(1.0, "ft") == pytest.approx(FT_PER_M)


def test_catalog_scales_between_metric_and_imperial():
    metric = {t.name: t for t in catalog_for(RoomType.BEDROOM, units="m")}
    imperial = {t.name: t for t in catalog_for(RoomType.BEDROOM, units="ft")}
    assert imperial["Bed"].width == pytest.approx(metric["Bed"].width * FT_PER_M)
    assert imperial["Bed"].min_room_area == pytest.approx(
        metric["Bed"].min_room_area * FT_PER_M ** 2
    )


def test_heritage_catalog_is_dutch_and_metric():
    items = {t.name for t in catalog_for(RoomType.BEDROOM, units="m", style="heritage")}
    assert "Ledikant" in items       # not "Bed"
    assert "Linnenkast" in items


def test_building_wraps_a_flat_room_list_in_one_storey():
    rooms = [_room()]
    b = Building(name="X", width=4, height=5, rooms=rooms)
    assert len(b.storeys) == 1
    assert b.storeys[0].rooms is rooms
    assert b.all_rooms() == rooms


def test_building_with_storeys_exposes_ground_floor_as_rooms():
    ground = Storey(name="Ground", rooms=[_room()], level=0)
    upper = Storey(name="First", rooms=[_room()], level=1)
    b = Building(name="X", width=4, height=5, storeys=[ground, upper])
    assert b.rooms is ground.rooms
    assert len(b.all_rooms()) == 2
    assert b.total_floor_area() == pytest.approx(40.0)
