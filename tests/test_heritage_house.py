"""Tests for the surveyed 1931 house: geometry, orientation and daylight.

These pin the facts taken from the source material so a refactor cannot
quietly change what the drawings and the brochure say:

  * unit width 7.15 m and a 9.90 m body (9.00 m drawn + the "0.90 m dieper"
    note on the approved sheet), giving ~212 m2 gross over three storeys
    against the brochure's 198 m2 net;
  * seven bedrooms and two bathrooms;
  * the corner unit's free side faces south, the garden west, the street
    east, and the party wall north.
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from architectural_design import daylight
from architectural_design.furniture_placer import furnish
from architectural_design.layout import building_from_spec
from architectural_design.models import RoomType, compass_name
from architectural_design.spec import load_spec

SPEC = os.path.join(os.path.dirname(__file__), "..", "examples", "rhijngeesterstraatweg_143.json")


@pytest.fixture(scope="module")
def house():
    return building_from_spec(load_spec(SPEC))


def test_footprint_matches_the_1931_unit(house):
    assert house.width == pytest.approx(7.15)
    assert house.height == pytest.approx(9.90)
    assert house.units == "m"
    assert house.year_built == 1931


def test_three_storeys(house):
    assert [s.level for s in house.storeys] == [0, 1, 2]
    assert [s.name for s in house.storeys] == ["Begane grond", "Eerste etage", "Tweede etage"]


def test_every_storey_tiles_the_footprint_without_overlaps(house):
    for storey in house.storeys:
        assert storey.area == pytest.approx(house.footprint_area(), rel=1e-4), storey.name
        for a, b in itertools.combinations(storey.rooms, 2):
            assert not a.rect.overlaps(b.rect), f"{a.name} overlaps {b.name} on {storey.name}"


def test_rooms_stay_inside_the_envelope(house):
    for room in house.all_rooms():
        assert room.rect.x >= -1e-9
        assert room.rect.y >= -1e-9
        assert room.rect.x2 <= house.width + 1e-9
        assert room.rect.y2 <= house.height + 1e-9


def test_gross_area_is_consistent_with_the_brochure(house):
    # 198 m2 net (NEN 2580, excluding walls and the stair void) against a
    # ~212 m2 gross tiling of three identical floor plates.
    assert house.total_floor_area() == pytest.approx(212.4, abs=1.0)


def test_seven_bedrooms_and_two_bathrooms(house):
    rooms = house.all_rooms()
    bedrooms = [r for r in rooms if r.room_type is RoomType.BEDROOM]
    bathrooms = [r for r in rooms if r.room_type is RoomType.BATHROOM]
    assert len(bedrooms) == 7
    assert len(bathrooms) == 2


def test_dutch_room_names_map_onto_room_types(house):
    by_name = {r.name: r.room_type for r in house.storeys[0].rooms}
    assert by_name["Keuken"] is RoomType.KITCHEN
    assert by_name["Huiskamer"] is RoomType.LIVING_ROOM
    assert by_name["Salon"] is RoomType.SALON
    assert by_name["Hal"] is RoomType.HALLWAY
    assert by_name["Entree"] is RoomType.ENTRY
    assert by_name["Toilet"] is RoomType.TOILET


def test_orientation_of_the_corner_plot(house):
    # Plan is drawn garden-up; +Y therefore faces west.
    assert house.north_angle_deg == pytest.approx(270.0)
    assert house.side_compass("N") == "W"   # rear garden, west
    assert house.side_compass("S") == "E"   # front door, to the street
    assert house.side_compass("W") == "S"   # the sunny free side, side garden
    assert house.side_compass("E") == "N"   # party wall


def test_party_wall_is_blind(house):
    assert house.blind_sides == ["E"]
    for room in house.all_rooms():
        assert not any(w.side == "E" for w in room.windows), (
            f"{room.name} has a window on the party wall"
        )


def test_front_door_faces_the_street(house):
    ground = house.storeys[0]
    fronts = [(r, d) for r in ground.rooms for d in r.doors if d.kind == "front_door"]
    assert len(fronts) == 1
    room, door = fronts[0]
    assert room.name == "Entree"
    assert house.side_compass(door.side) == "E"


def test_principal_rooms_are_well_daylit(house):
    report = {d.name: d for d in daylight.analyse_building(house)}
    for name in ("Salon", "Huiskamer", "Keuken"):
        assert report[name].ratio >= daylight.DAYLIGHT_TARGET, name
        assert report[name].rating == "generous", name


def test_sun_periods_follow_the_compass(house):
    report = {(d.name, d.storey): d for d in daylight.analyse_building(house)}
    salon = report[("Salon", "Begane grond")]
    huiskamer = report[("Huiskamer", "Begane grond")]
    assert salon.orientations == ["E"] and "morning sun" in salon.sun
    assert huiskamer.orientations == ["W"] and "afternoon sun" in huiskamer.sun


def test_windows_carry_period_lights(house):
    salon = next(r for r in house.storeys[0].rooms if r.name == "Salon")
    win = salon.windows[0]
    assert win.lights >= 2, "1931 openings carry divided lights"
    assert win.transom is True
    assert win.glazed_area == pytest.approx(win.width * win.height)


def test_stair_is_pinned_by_the_survey_not_the_placer(house):
    hal = next(r for r in house.storeys[0].rooms if r.name == "Hal")
    stairs = [f for f in hal.furniture if f.kind == "stair"]
    assert len(stairs) == 1
    assert hal.rect.contains_point(stairs[0].rect.center)


def test_furnishing_keeps_pinned_fixtures_and_avoids_overlaps(house):
    furnish(house, style="heritage")
    for room in house.all_rooms():
        for a, b in itertools.combinations(room.furniture, 2):
            assert not a.rect.overlaps(b.rect), f"{a.name}/{b.name} overlap in {room.name}"
        for item in room.furniture:
            assert item.rect.x >= room.rect.x - 1e-6
            assert item.rect.y >= room.rect.y - 1e-6
            assert item.rect.x2 <= room.rect.x2 + 1e-6
            assert item.rect.y2 <= room.rect.y2 + 1e-6
    hal = next(r for r in house.storeys[0].rooms if r.name == "Hal")
    assert any(f.kind == "stair" for f in hal.furniture)


def test_compass_name_rounding():
    assert compass_name(0) == "N"
    assert compass_name(90) == "E"
    assert compass_name(180) == "S"
    assert compass_name(270) == "W"
    assert compass_name(45) == "NE"
    assert compass_name(359) == "N"
