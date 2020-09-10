from hypothesis import assume, given
from hypothesis import strategies as st

from barriers import Barriers
from space import Area, Point

points = st.builds(
    Point,
    st.integers(min_value=-50, max_value=50),
    st.integers(min_value=-50, max_value=50),
)

areas = st.builds(Area, points, points)


@st.composite
def non_empty_areas(draw):
    lower = draw(points)
    upper = draw(
        st.builds(
            Point,
            x=st.integers(min_value=lower.x + 1, max_value=51),
            y=st.integers(min_value=lower.y + 1, max_value=51),
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


class TestBarriers:
    @given(barrier_areas=st.sets(areas), area=areas)
    def test_occupied_points(self, barrier_areas, area):
        barriers = Barriers.for_areas(barrier_areas)
        points = barriers.occupied_points_in(area)
        for point in points:
            assert any(point in area for area in barrier_areas)
            assert barriers.occupied(point)

    @given(
        barrier_areas=st.sets(areas),
        area_and_point=non_empty_areas().flatmap(area_and_point),
    )
    def test_unoccupied_point(self, barrier_areas, area_and_point):
        area, point = area_and_point
        assume(not any(point in b for b in barrier_areas))
        barriers = Barriers.for_areas(barrier_areas)
        assert point not in barriers.occupied_points_in(area)
        assert not barriers.occupied(point)
