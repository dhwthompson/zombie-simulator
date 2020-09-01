from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

import pytest

from character import default_human, default_zombie, LifeState
from space import Area, Point, Vector
from roster import Roster
from world import Barriers, Builder, Tick


world_dimensions = st.integers(min_value=0, max_value=50)


class FakeCharacter:
    def __init__(self, life_state):
        self.life_state = life_state


characters = st.builds(FakeCharacter, st.sampled_from(LifeState))


class TestBuilder:
    @given(st.iterables(elements=st.one_of(characters, st.just(None)), min_size=25))
    def test_population(self, population):
        builder = Builder(5, 5, population)
        roster = builder.roster
        assert roster.width == 5
        assert roster.height == 5
        for position, character in roster.positions:
            assert 0 <= position.x < 5
            assert 0 <= position.y < 5
            assert character is not None


@st.composite
def rosters(
    draw, inhabitants=st.one_of(st.builds(default_human), st.builds(default_zombie))
):
    width, height = draw(world_dimensions), draw(world_dimensions)
    assume(width > 0)
    assume(height > 0)
    area = Area(Point(0, 0), Point(width, height))
    points = st.builds(
        Point,
        st.integers(min_value=0, max_value=width - 1),
        st.integers(min_value=0, max_value=height - 1),
    )
    characters = draw(st.dictionaries(points, inhabitants))
    return Roster.partitioned(
        characters, area=area, partition_func=LifeState.for_character
    )


@pytest.mark.integration
class TestTick:
    @given(rosters())
    @settings(max_examples=25)
    def test_next_returns_a_roster(self, roster):
        assert isinstance(Tick(roster).next(), Roster)

    @given(rosters())
    @settings(max_examples=25)
    def test_preserves_character_count(self, roster):
        new_roster = Tick(roster).next()
        assert len(list(roster.positions)) == len(list(new_roster.positions))

    def test_zombie_approaches_human(self):
        zombie = default_zombie()
        human = default_human()

        characters = {Point(0, 0): zombie, Point(2, 2): human}
        area = Area(Point(0, 0), Point(3, 3))
        roster = Roster.partitioned(
            characters, area=area, partition_func=LifeState.for_character
        )

        roster = Tick(roster).next()

        assert sorted(roster.positions) == [(Point(1, 1), zombie), (Point(2, 2), human)]


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
        barriers = Barriers(barrier_areas)
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
        barriers = Barriers(barrier_areas)
        assert point not in barriers.occupied_points_in(area)
        assert not barriers.occupied(point)
