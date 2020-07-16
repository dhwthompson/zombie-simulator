from hypothesis import example, given
from hypothesis import strategies as st

import pytest

from space import Point, Vector
from world import World, WorldBuilder


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
        world = World(width, height, characters={})
        assert world.rows == [[None] * width] * height

    def test_explicitly_empty_world(self):
        assert World(2, 2, {}).rows == [[None, None], [None, None]]

    @given(characters())
    def test_world_with_character(self, character):
        world = World(2, 2, {Point(1, 1): character})
        assert world.rows == [[None, None], [None, character]]

    @given(characters())
    def test_character_out_of_bounds(self, character):
        with pytest.raises(ValueError):
            World(2, 2, {Point(2, 2): character})

    def test_empty_viewpoint(self):
        world = World(2, 2, characters={})
        assert len(world.viewpoint(Point(1, 1))) == 0

    @given(characters())
    def test_viewpoint_single_character(self, character):
        world = World(2, 2, {Point(1, 1): character})
        viewpoint = world.viewpoint(Point(1, 1))
        assert len(viewpoint) == 1
        assert (Vector.ZERO, character) in viewpoint

    @given(char1=characters(), char2=characters())
    def test_viewpoint_multiple_characters(self, char1, char2):
        world = World(3, 3, {Point(1, 1): char1, Point(2, 0): char2})
        viewpoint = world.viewpoint(Point(0, 1))
        assert len(viewpoint) == 2
        assert (Vector(1, 0), char1) in viewpoint
        assert (Vector(2, -1), char2) in viewpoint


class TestWorldBuilder:
    @given(st.iterables(elements=st.one_of(characters(), st.just(None)), min_size=25))
    def test_population(self, population):
        builder = WorldBuilder(5, 5, population)
        rows = builder.world.rows
        assert len(rows) == 5
        for row in rows:
            assert len(row) == 5
