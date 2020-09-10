from typing import FrozenSet, Iterable

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from barriers import Barriers
from space import Area, Point


@st.composite
def areas(
    draw, max_modulus=50, min_width=0, max_width=None, min_height=0, max_height=None
):
    lower = draw(
        st.builds(
            Point,
            st.integers(min_value=-max_modulus, max_value=max_modulus - min_width),
            st.integers(min_value=-max_modulus, max_value=max_modulus - min_height),
        )
    )

    max_x = max_y = max_modulus
    if max_width is not None:
        max_x = min(max_x, lower.x + max_width)
    if max_height is not None:
        max_y = min(max_y, lower.y + max_height)

    upper = draw(
        st.builds(
            Point,
            st.integers(min_value=lower.x + min_width, max_value=max_x),
            st.integers(min_value=lower.y + min_height, max_value=max_y),
        )
    )

    return Area(lower, upper)


def area_and_point(area):
    return st.tuples(
        st.just(area),
        st.builds(
            Point,
            x=st.integers(min_value=area._lower.x, max_value=area._upper.x - 1),
            y=st.integers(min_value=area._lower.y, max_value=area._upper.y - 1),
        ),
    )


def all_points_in(areas: Iterable[Area]) -> FrozenSet[Point]:
    points: FrozenSet[Point] = frozenset()
    for area in areas:
        points = points.union(area)
    return points


class TestBarriers:
    @given(barrier_areas=st.sets(areas()), area=areas())
    @settings(max_examples=25)
    def test_occupied_points(self, barrier_areas, area):
        barriers = Barriers.for_areas(barrier_areas)
        points = barriers.occupied_points_in(area)
        all_area_points = all_points_in(barrier_areas)
        for point in points:
            assert point in all_area_points
            assert barriers.occupied(point)

    @given(
        barrier_areas=st.sets(areas()),
        area_and_point=areas(min_width=1, min_height=1).flatmap(area_and_point),
    )
    @settings(max_examples=25)
    def test_unoccupied_point(self, barrier_areas, area_and_point):
        area, point = area_and_point
        assume(not any(point in b for b in barrier_areas))
        barriers = Barriers.for_areas(barrier_areas)
        assert point not in barriers.occupied_points_in(area)
        assert not barriers.occupied(point)

    @given(barrier_areas=st.sets(st.one_of([areas(max_width=1), areas(max_height=1)])))
    @settings(max_examples=25)
    def test_positions(self, barrier_areas):
        barriers = Barriers.for_areas(barrier_areas)
        positions = {point for (point, _) in barriers.positions}

        assert positions == all_points_in(barrier_areas)
