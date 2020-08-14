from hypothesis import example, given, note, settings
from hypothesis import strategies as st
from .strategies import list_and_element
import pytest

from typing import Any, Tuple

from space import Area, Point
from tree import Match, PartitionTree, SpaceTree

Unit = Tuple[()]


def areas(min_size_x=1, min_size_y=1, max_dimension=1000):
    def points_greater_than(p):
        return st.builds(
            Point,
            x=st.integers(min_value=p.x + min_size_x),
            y=st.integers(min_value=p.y + min_size_y),
        )

    points = st.builds(
        Point,
        x=st.integers(min_value=-max_dimension, max_value=max_dimension),
        y=st.integers(min_value=-max_dimension, max_value=max_dimension),
    )

    return points.flatmap(lambda p: st.builds(Area, st.just(p), points_greater_than(p)))


def points_in(area):
    return st.builds(
        Point,
        x=st.integers(min_value=area._lower.x, max_value=area._upper.x - 1),
        y=st.integers(min_value=area._lower.y, max_value=area._upper.y - 1),
    )


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_empty_tree_item(area_and_point):
    area, point = area_and_point
    tree: SpaceTree[object] = SpaceTree.build(area, None)
    with pytest.raises(KeyError):
        tree[point]


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_empty_tree_get(area_and_point):
    area, point = area_and_point
    tree: SpaceTree[object] = SpaceTree.build(area, None)
    assert tree.get(point) is None


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_tree_item(area_and_point):
    area, point = area_and_point
    value = object()
    tree = SpaceTree.build(area=area, positions={point: value})

    assert tree[point] is value


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_no_nearest(area_and_point):
    area, point = area_and_point
    tree = SpaceTree.build(area=area, positions={point: object()})

    assert tree.nearest_to(point) is None


@settings(max_examples=25)
@given(
    areas().flatmap(
        lambda a: st.tuples(
            st.just(a),
            st.lists(points_in(a), min_size=2, unique=True).flatmap(list_and_element),
        )
    )
)
@example(
    area_and_points=(
        Area(Point(x=-257, y=0), Point(x=0, y=3)),
        (
            [
                Point(x=-1, y=0),
                Point(x=-3, y=0),
                Point(x=-1, y=1),
                Point(x=-1, y=2),
                Point(x=-2, y=1),
                Point(x=-5, y=0),
                Point(x=-6, y=0),
                Point(x=-7, y=0),
                Point(x=-2, y=0),
            ],
            Point(x=-3, y=0),
        ),
    ),
)
def test_nearest(area_and_points):
    area, (points, origin) = area_and_points
    tree = SpaceTree.build(area=area, positions={point: object() for point in points})

    best_match = tree.nearest_to(origin)

    assert best_match is not None
    assert tree[best_match.point] == best_match.value
    for point in points:
        if point != origin:
            assert (best_match.point - origin).distance <= (point - origin).distance


@given(
    areas().flatmap(lambda a: st.tuples(st.just(a), st.lists(points_in(a)))), areas()
)
@example(
    (Area(Point(0, 0), Point(10, 10)), [Point(1, 1), Point(8, 8)]),
    Area(Point(1, 1), Point(3, 3)),
)
def test_items_in(area_and_points, inclusion_area):
    tree_area = area_and_points[0]
    positions = {point: object() for point in area_and_points[1]}

    tree = SpaceTree.build(area=tree_area, positions=positions)

    matches_in_area = tree.items_in(inclusion_area)

    for point, character in positions.items():
        if point in inclusion_area:
            assert Match(point, character) in matches_in_area
        else:
            assert Match(point, character) not in matches_in_area


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_empty_partition_tree_item(area_and_point):
    area, point = area_and_point
    tree: PartitionTree[Unit, Any] = PartitionTree.build(area, lambda item: (), None)
    with pytest.raises(KeyError):
        tree[point]


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_empty_partition_tree_get(area_and_point):
    area, point = area_and_point
    tree: PartitionTree[Unit, Any] = PartitionTree.build(area, lambda item: (), None)
    assert tree.get(point) is None


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_partition_tree_item(area_and_point):
    area, point = area_and_point
    value = object()
    tree = PartitionTree.build(
        area=area, partition_func=lambda item: (), positions={point: value}
    )

    assert tree[point] is value


@given(areas().flatmap(lambda a: st.tuples(st.just(a), points_in(a))))
def test_partition_tree_no_nearest(area_and_point):
    area, point = area_and_point
    tree = PartitionTree.build(
        area=area, partition_func=lambda item: (), positions={point: object()}
    )

    assert tree.nearest_to(point, key=()) is None


@settings(max_examples=25)
@given(
    areas().flatmap(
        lambda a: st.tuples(
            st.just(a),
            st.lists(points_in(a), min_size=2, unique=True).flatmap(list_and_element),
        )
    )
)
@example(
    area_and_points=(
        Area(Point(x=-257, y=0), Point(x=0, y=3)),
        (
            [
                Point(x=-1, y=0),
                Point(x=-3, y=0),
                Point(x=-1, y=1),
                Point(x=-1, y=2),
                Point(x=-2, y=1),
                Point(x=-5, y=0),
                Point(x=-6, y=0),
                Point(x=-7, y=0),
                Point(x=-2, y=0),
            ],
            Point(x=-3, y=0),
        ),
    ),
)
def test_partition_tree_nearest(area_and_points):
    area, (points, origin) = area_and_points
    tree = PartitionTree.build(
        area=area,
        partition_func=lambda item: (),
        positions={point: object() for point in points},
    )

    best_match = tree.nearest_to(origin, key=())

    assert best_match is not None
    assert tree[best_match.point] == best_match.value
    for point in points:
        if point != origin:
            assert (best_match.point - origin).distance <= (point - origin).distance


@given(
    areas().flatmap(lambda a: st.tuples(st.just(a), st.lists(points_in(a)))), areas()
)
@example(
    (Area(Point(0, 0), Point(10, 10)), [Point(1, 1), Point(8, 8)]),
    Area(Point(1, 1), Point(3, 3)),
)
def test_partition_items_in(area_and_points, inclusion_area):
    tree_area = area_and_points[0]
    positions = {point: object() for point in area_and_points[1]}

    tree = PartitionTree.build(
        area=tree_area, partition_func=lambda item: (), positions=positions
    )

    matches_in_area = tree.items_in(inclusion_area)

    for point, character in positions.items():
        if point in inclusion_area:
            assert Match(point, character) in matches_in_area
        else:
            assert Match(point, character) not in matches_in_area
