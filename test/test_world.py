from itertools import repeat

from hypothesis import example, given
from hypothesis import strategies as st

import pytest

from space import Vector
from world import World, WorldBuilder


world_dimensions = st.integers(min_value=0, max_value=50)


class TestWorld:
    def test_single_cell_world(self):
        assert World(1, 1).rows == [[None]]

    def test_single_row_world(self):
        assert World(3, 1).rows == [[None, None, None]]

    def test_multi_row_world(self):
        assert World(2, 2).rows == [[None, None], [None, None]]

    def test_explicitly_empty_world(self):
        assert World(2, 2, {}).rows == [[None, None], [None, None]]

    def test_world_with_character(self):
        character = object()
        world = World(2, 2, {(1, 1): character})
        assert world.rows == [[None, None], [None, character]]

    def test_add_character(self):
        character = object()
        world = World(2, 2).with_character((1, 1), character)
        assert world.rows == [[None, None], [None, character]]

    def test_add_character_does_not_mutate(self):
        character = object()
        world = World(2, 2)
        _ = world.with_character((1, 1), character)
        assert world.rows == [[None, None], [None, None]]

    def test_moving_existing_character(self):
        character = object()
        world = World(2, 2, {(0, 0): character})
        world = world.with_character((1, 1), character)
        assert world.rows == [[None, None], [None, character]]

    def test_non_moving_character(self):
        moving_char = object()
        non_moving_char = object()
        world = World(2, 2, {(0, 0): moving_char, (1, 1): non_moving_char})
        world = world.with_character((1, 0), moving_char)

        assert world.rows == [[None, moving_char], [None, non_moving_char]]

    def test_move_to_same_position(self):
        character = object()
        other_char = object()
        world = World(2, 2, {(0, 0): character, (1, 1): other_char})
        new_world = world.with_character((0, 0), character)
        assert new_world.rows == world.rows

    def test_moving_character_onto_another(self):
        character = object()
        other_char = object()
        world = World(2, 2, {(0, 0): character, (1, 1): other_char})
        with pytest.raises(ValueError):
            world.with_character((1, 1), character)

    def test_add_null_character(self):
        world = World(2, 2)
        with pytest.raises(ValueError):
            world.with_character((1, 1), None)

    def test_empty_viewpoint(self):
        world = World(2, 2)
        assert len(world.viewpoint((1, 1))) == 0

    def test_viewpoint_single_character(self):
        character = object()
        world = World(2, 2, {(1, 1): character})
        viewpoint = world.viewpoint((1, 1))
        assert len(viewpoint) == 1
        assert (Vector.ZERO, character) in viewpoint

    def test_viewpoint_multiple_characters(self):
        char1, char2 = object(), object()
        world = World(2, 2, {(1, 1): char1, (2, 0): char2})
        viewpoint = world.viewpoint((0, 1))
        assert len(viewpoint) == 2
        assert (Vector(1, 0), char1) in viewpoint
        assert (Vector(2, -1), char2) in viewpoint


class TestWorldBuilder:

    def test_populated_world(self):
        population = iter(['foo', 'bar', 'baz', 'boop'])
        builder = WorldBuilder(2, 2, population)
        assert builder.world.rows == [['foo', 'bar'], ['baz', 'boop']]

    @given(world_dimensions, world_dimensions, st.builds(object))
    def test_constant_population(self, width, height, denizen):
        builder = WorldBuilder(width, height, repeat(denizen))
        assert builder.world.rows == [[denizen] * width] * height

    @given(st.iterables(elements=st.one_of(st.integers(), st.just(None)), min_size=25))
    def test_integer_population(self, population):
        builder = WorldBuilder(5, 5, population)
