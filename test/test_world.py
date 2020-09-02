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
    @given(st.lists(elements=st.one_of(characters, st.just(None)), min_size=25, max_size=25))
    @settings(max_examples=25)
    def test_population(self, population):
        world_area = Area.from_zero(5, 5)
        builder = Builder(world_area, population)
        roster = builder.roster
        assert roster.width == 5
        assert roster.height == 5
        total_characters = 0
        for position, character in roster.positions:
            assert position in world_area
            assert character in population
            total_characters = total_characters + 1
        assert total_characters == len([c for c in population if c is not None])


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
