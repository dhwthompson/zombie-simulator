from hypothesis import example, given, settings
from hypothesis import strategies as st

import pytest

from character import default_human, default_zombie
from space import Point, Vector
from world import Tick, World, WorldBuilder


world_dimensions = st.integers(min_value=0, max_value=50)


class FakeCharacter:
    def __init__(self, undead):
        self.undead = undead


def characters():
    return st.booleans().map(FakeCharacter)


class TestWorld:
    @given(width=world_dimensions, height=world_dimensions)
    @example(0, 0)
    @example(1, 1)
    def test_world_dimensions(self, width, height):
        world = World.for_mapping(width, height, characters={})
        assert world.width == width
        assert world.height == height

    def test_explicitly_empty_world(self):
        assert list(World.for_mapping(2, 2, {}).positions) == []

    @given(characters())
    def test_world_with_character(self, character):
        world = World.for_mapping(2, 2, {Point(1, 1): character})
        assert list(world.positions) == [(Point(1, 1), character)]

    @given(characters())
    def test_character_out_of_bounds(self, character):
        with pytest.raises(ValueError):
            World.for_mapping(2, 2, {Point(2, 2): character})

    def test_empty_viewpoint(self):
        world = World.for_mapping(2, 2, characters={})
        assert len(world.viewpoint(Point(1, 1))) == 0

    @given(characters())
    def test_viewpoint_single_character(self, character):
        world = World.for_mapping(2, 2, {Point(1, 1): character})
        viewpoint = world.viewpoint(Point(1, 1))
        assert len(viewpoint) == 1
        assert viewpoint.character_at(Vector.ZERO) == character

    @given(char1=characters(), char2=characters())
    def test_viewpoint_multiple_characters(self, char1, char2):
        world = World.for_mapping(3, 3, {Point(1, 1): char1, Point(2, 0): char2})
        viewpoint = world.viewpoint(Point(0, 1))
        assert len(viewpoint) == 2
        assert viewpoint.character_at(Vector(1, 0)) == char1
        assert viewpoint.character_at(Vector(2, -1)) == char2


class TestWorldBuilder:
    @given(st.iterables(elements=st.one_of(characters(), st.just(None)), min_size=25))
    def test_population(self, population):
        builder = WorldBuilder(5, 5, population)
        world = builder.world
        assert world.width == 5
        assert world.height == 5
        for position, character in world.positions:
            assert 0 <= position.x < 5
            assert 0 <= position.y < 5
            assert character.undead in [True, False]


@st.composite
def worlds(
    draw, inhabitants=st.one_of(st.builds(default_human), st.builds(default_zombie))
):
    dimensions = st.integers(min_value=1, max_value=100)
    x, y = draw(dimensions), draw(dimensions)
    points = st.builds(
        Point,
        st.integers(min_value=0, max_value=x - 1),
        st.integers(min_value=0, max_value=y - 1),
    )
    characters = draw(st.dictionaries(points, inhabitants))
    return World.for_mapping(x, y, characters)

@pytest.mark.integration
class TestTick:

    @given(worlds())
    @settings(max_examples=25)
    def test_next_returns_a_world(self, world):
        assert isinstance(Tick(world).next(), World)


    @given(worlds())
    @settings(max_examples=25)
    def test_preserves_character_count(self, world):
        new_world = Tick(world).next()
        assert len(list(world.positions)) == len(list(new_world.positions))

    def test_zombie_approaches_human(self):
        zombie = default_zombie()
        human = default_human()

        characters = {Point(0, 0): zombie, Point(2, 2): human}

        world = World.for_mapping(3, 3, characters)

        world = Tick(world).next()

        assert sorted(world.positions) == [(Point(1, 1), zombie), (Point(2, 2), human)]
