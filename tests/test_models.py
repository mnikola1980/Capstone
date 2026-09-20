import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from architectural_design.models import Point, Rect


def test_rect_area_and_center():
    r = Rect(0, 0, 10, 4)
    assert r.area == 40
    assert r.center == Point(5, 2)


def test_rect_overlap_detects_overlap():
    a = Rect(0, 0, 5, 5)
    b = Rect(3, 3, 5, 5)
    assert a.overlaps(b)
    assert b.overlaps(a)


def test_rect_overlap_touching_edges_is_not_overlap():
    a = Rect(0, 0, 5, 5)
    b = Rect(5, 0, 5, 5)  # shares the x=5 edge only
    assert not a.overlaps(b)


def test_rect_overlap_disjoint():
    a = Rect(0, 0, 5, 5)
    b = Rect(10, 10, 5, 5)
    assert not a.overlaps(b)


def test_shared_edge_detected():
    a = Rect(0, 0, 5, 5)
    b = Rect(5, 0, 5, 5)
    shared = a.shared_edge(b)
    assert shared is not None
    side, lo, hi = shared
    assert side == "E"
    assert lo == 0 and hi == 5


def test_shared_edge_none_when_disjoint():
    a = Rect(0, 0, 5, 5)
    b = Rect(10, 10, 5, 5)
    assert a.shared_edge(b) is None


def test_contains_point():
    r = Rect(0, 0, 10, 10)
    assert r.contains_point(Point(5, 5))
    assert not r.contains_point(Point(15, 5))
