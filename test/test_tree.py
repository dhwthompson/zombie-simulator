from hypothesis import example, given, note, settings
from hypothesis import strategies as st
from .strategies import list_and_element
import pytest

from space import Area, Point
from tree import SpaceTree


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

    walk_tree(tree)
    best_match = tree.nearest_to(origin)

    assert best_match is not None
    assert tree[best_match.point] == best_match.value
    for point in points:
        if point != origin:
            assert (best_match.point - origin).distance <= (point - origin).distance


def walk_tree(tree):
    output = []

    def print_node(node, indent):
        output.append(f"{' ' * indent}- {node._area}")
        if hasattr(node, "_lower_child"):
            for child in [node._lower_child, node._upper_child]:
                print_node(child, indent + 2)
        else:
            output.extend(
                f"{' ' * indent}* {pos} = {value}"
                for pos, value in node._positions.items()
            )

    print_node(tree._root, indent=0)
    note("\n".join(output))
