from hypothesis import assume, example, given
from hypothesis import strategies as st

import pytest

from space import Point, Vector
from world import Move, Roster, World, WorldBuilder


points = st.builds(Point, st.integers(), st.integers())
world_dimensions = st.integers(min_value=0, max_value=50)


class TestWorld:

    @given(width=world_dimensions, height=world_dimensions)
    @example(0, 0)
    @example(1, 1)
    def test_world_dimensions(self, width, height):
        world = World(width, height, characters=None)
        assert world.rows == [[None] * width] * height

    def test_explicitly_empty_world(self):
        assert World(2, 2, {}).rows == [[None, None], [None, None]]

    def test_world_with_character(self):
        character = object()
        world = World(2, 2, {(1, 1): character})
        assert world.rows == [[None, None], [None, character]]

    def test_character_out_of_bounds(self):
        with pytest.raises(ValueError):
            World(2, 2, {(2, 2): object()})

    def test_moving_existing_character(self):
        character = object()
        world = World(2, 2, {(0, 0): character})
        world = world.move_character(character, (1, 1))
        assert world.rows == [[None, None], [None, character]]

    def test_non_moving_character(self):
        moving_char = object()
        non_moving_char = object()
        world = World(2, 2, {(0, 0): moving_char, (1, 1): non_moving_char})
        world = world.move_character(moving_char, (1, 0))

        assert world.rows == [[None, moving_char], [None, non_moving_char]]

    def test_moving_non_existent_character(self):
        world = World(2, 2, {(0, 0): object(), (1, 1): object()})
        with pytest.raises(ValueError):
            world.move_character(object(), (1, 0))

    def test_move_to_same_position(self):
        character = object()
        other_char = object()
        world = World(2, 2, {(0, 0): character, (1, 1): other_char})
        new_world = world.move_character(character, (0, 0))
        assert new_world.rows == world.rows

    def test_moving_character_onto_another(self):
        character = object()
        other_char = object()
        world = World(2, 2, {(0, 0): character, (1, 1): other_char})
        with pytest.raises(ValueError):
            world.move_character(character, (1, 1))

    def test_empty_viewpoint(self):
        world = World(2, 2, characters=None)
        assert len(world.viewpoint((1, 1))) == 0

    def test_viewpoint_single_character(self):
        character = object()
        world = World(2, 2, {(1, 1): character})
        viewpoint = world.viewpoint((1, 1))
        assert len(viewpoint) == 1
        assert (Vector.ZERO, character) in viewpoint

    def test_viewpoint_multiple_characters(self):
        char1, char2 = object(), object()
        world = World(3, 3, {(1, 1): char1, (2, 0): char2})
        viewpoint = world.viewpoint((0, 1))
        assert len(viewpoint) == 2
        assert (Vector(1, 0), char1) in viewpoint
        assert (Vector(2, -1), char2) in viewpoint


def list_and_element(l):
    """Given a list, return a strategy of that list and one of its elements.

    This can be connected onto an existing list strategy using the `flatmap`
    method.
    """
    return st.tuples(st.just(l), st.sampled_from(l))


characters = st.builds(object)
position_lists = st.lists(st.tuples(points, characters))


def positions_unique(positions):
    return len(set(p[0] for p in positions)) == len(positions)

unique_position_lists = position_lists.filter(positions_unique)


class TestRoster:

    @given(unique_position_lists)
    def test_takes_position_character_pairs(self, positions):
        Roster(positions)

    @given(unique_position_lists.flatmap(list_and_element))
    def test_character_at_position(self, positions_and_item):
        positions, (position, character) = positions_and_item

        assert Roster(positions).character_at(position) == character

    @given(points)
    def test_rejects_duplicate_position(self, point):
        positions = [(point, object()), (point, object())]
        with pytest.raises(ValueError):
            Roster(positions)

    @given(characters)
    def test_rejects_duplicate_character(self, character):
        positions = [(Point(0, 0), character), (Point(1, 1), character)]
        with pytest.raises(ValueError) as e:
            Roster(positions)

    def test_roster_for_dict(self):
        character = object()
        roster = Roster.for_value({(0, 1): character})
        assert roster.character_at(Point(0, 1)) == character

    def test_roster_for_nothing(self):
        roster = Roster.for_value(None)
        assert not list(roster)

    def test_roster_for_itself(self):
        roster = Roster([((0, 2), object())])
        assert roster.for_value(roster) is roster


class TestMove:

    @given(unique_position_lists.flatmap(list_and_element))
    def test_zero_move_preserves_roster(self, positions_and_item):
        positions, (old_position, character) = positions_and_item
        roster = Roster(positions)
        assert Move(character, old_position).next_roster(roster) == roster

    @given(unique_position_lists.flatmap(list_and_element), points)
    def test_character_moves(self, positions_and_item, new_position):
        positions, (_, character) = positions_and_item
        assume(not any(pos == new_position for pos, _ in positions))
        roster = Roster(positions)
        move = Move(character, new_position)

        next_roster = move.next_roster(roster)

        assert next_roster.character_at(new_position) == character

    def test_move_to_occupied_position(self):
        a, b = object(), object()
        roster = Roster([(Point(0, 0), a), (Point(1, 1), b)])
        move = Move(b, Point(0, 0))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    def test_move_of_non_existent_character(self):
        a, b = object(), object()
        roster = Roster([(Point(0, 0), a)])
        move = Move(b, Point(0, 0))
        with pytest.raises(ValueError):
            move.next_roster(roster)


class TestWorldBuilder:

    def test_populated_world(self):
        population = iter(['foo', 'bar', 'baz', 'boop'])
        builder = WorldBuilder(2, 2, population)
        assert builder.world.rows == [['foo', 'bar'], ['baz', 'boop']]

    @given(st.iterables(elements=st.one_of(st.integers(), st.just(None)),
                        min_size=25,
                        unique=True))
    def test_integer_population(self, population):
        builder = WorldBuilder(5, 5, population)
