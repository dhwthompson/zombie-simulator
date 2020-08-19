from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

import pytest

from character import default_human, default_zombie, LifeState
from space import Area, Point, Vector
from roster import Roster
from world import Builder, Tick


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
