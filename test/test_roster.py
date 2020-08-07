from collections import OrderedDict
from operator import itemgetter

from hypothesis import assume, given, note
from hypothesis import strategies as st

import pytest

from .strategies import list_and_element, dict_and_element
from roster import ChangeCharacter, Move, Roster, Viewpoint
from space import Area, Point, Vector


class Character:
    # Keeping this as an object to preserve object identity

    def __init__(self, undead, living):
        self.undead = undead
        self.living = living

    def __repr__(self):
        return f"Character(undead={self.undead}, living={self.living})"


def do_nothing(c: Character) -> Character:
    return c


def kill(c: Character) -> Character:
    return Character(undead=c.undead, living=False)


def reanimate(c: Character) -> Character:
    return Character(undead=True, living=False)


characters = st.builds(Character, undead=st.booleans(), living=st.booleans())


def points(max_dimension=1000):
    return st.builds(
        Point,
        x=st.integers(min_value=-max_dimension, max_value=max_dimension),
        y=st.integers(min_value=-max_dimension, max_value=max_dimension),
    )


def position_dicts(min_size=0, max_size=None, max_dimension=1000):
    # Using OrderedDict so Hypothesis can pick a random element
    return st.dictionaries(
        points(),
        characters,
        min_size=min_size,
        max_size=max_size,
        dict_class=OrderedDict,
    )


def areas(min_size_x=1, min_size_y=1):
    def points_greater_than(p):
        return st.builds(
            Point,
            x=st.integers(min_value=p.x + min_size_x),
            y=st.integers(min_value=p.y + min_size_y),
        )

    return points().flatmap(
        lambda p: st.builds(Area, st.just(p), points_greater_than(p))
    )


def position_dicts_in(area, min_size=0, max_size=None):
    return st.dictionaries(
        st.builds(
            Point,
            x=st.integers(min_value=area._lower.x, max_value=area._upper.x - 1),
            y=st.integers(min_value=area._lower.y, max_value=area._upper.y - 1),
        ),
        characters,
        min_size=min_size,
        max_size=max_size,
        dict_class=OrderedDict,
    )


def area_containing(points):
    min_x = min((p.x for p in points), default=0)
    min_y = min((p.y for p in points), default=0)
    max_x = max((p.x for p in points), default=0)
    max_y = max((p.y for p in points), default=0)

    return Area(lower=Point(min_x, min_y), upper=Point(max_x + 1, max_y + 1))


class TestRoster:
    @given(position_dicts())
    def test_takes_position_character_map(self, positions):
        Roster.for_mapping(positions, area_containing(positions))

    @given(position_dicts(min_size=1).flatmap(dict_and_element))
    def test_character_at_position(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_mapping(positions, area_containing(positions))
        assert roster.character_at(position) == character

    @given(characters)
    def test_rejects_duplicate_character(self, character):
        positions = {Point(0, 0): character, Point(1, 1): character}
        with pytest.raises(ValueError) as e:
            Roster.for_mapping(positions, area_containing(positions))

    @given(position_dicts(), areas())
    def test_characters_outside_area(self, positions, area):
        assume(not all(p in area for p in positions))
        with pytest.raises(ValueError) as e:
            Roster.for_mapping(positions, area)

    @given(position_dicts())
    def test_value_equality(self, positions):
        area = area_containing(positions)
        assert Roster.for_mapping(positions, area) == Roster.for_mapping(
            positions.copy(), area
        )

    def test_empty_roster(self):
        roster: Roster[Character] = Roster.for_mapping(
            {}, Area(Point(0, 0), Point(5, 5))
        )
        assert not roster

    @given(position_dicts(min_size=1))
    def test_non_empty_roster(self, positions):
        roster = Roster.for_mapping(positions, area_containing(positions))
        assert roster

    @given(characters)
    def test_no_nearest_character(self, character):
        roster = Roster.for_mapping(
            {Point(1, 1): character}, area=Area(Point(0, 0), Point(2, 2))
        )
        assert roster.nearest_to(Point(1, 1), undead=True) is None
        assert roster.nearest_to(Point(1, 1), undead=False) is None

    @given(position_dicts(min_size=2).flatmap(dict_and_element))
    def test_nearest_undead(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_mapping(positions, area_containing(positions))

        assume(
            any(char.undead and char != character for (_, char) in positions.items())
        )

        nearest = roster.nearest_to(position, undead=True)
        assert nearest is not None
        nearest_position, nearest_character = nearest.position, nearest.character

        assert nearest_position != position
        assert nearest_character != character

        best_distance = min(
            (p - position).distance
            for p, c in positions.items()
            if c != character and c.undead
        )
        assert best_distance == (nearest_position - position).distance

    @given(position_dicts(min_size=2).flatmap(dict_and_element))
    def test_nearest_non_undead(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_mapping(positions, area_containing(positions))

        note(f"Roster: {roster}")
        note(f"Sample position: {position}")
        note(f"Character: {character}")

        assume(
            any(
                char.living and not char.undead and char != character
                for (_, char) in positions.items()
            )
        )

        nearest = roster.nearest_to(position, undead=False, living=True)
        assert nearest is not None
        assert nearest.character.living


class TestViewpoint:
    def test_empty_viewpoint(self):
        roster: Roster[Character] = Roster.for_mapping(
            {}, area=Area(Point(0, 0), Point(2, 2))
        )
        assert len(Viewpoint(Point(1, 1), roster)) == 0

    @given(characters)
    def test_viewpoint_single_character(self, character):
        roster = Roster.for_mapping(
            {Point(1, 1): character}, area=Area(Point(0, 0), Point(2, 2))
        )
        viewpoint = Viewpoint(Point(1, 1), roster)
        assert len(viewpoint) == 1
        assert viewpoint.character_at(Vector.ZERO) == character

    @given(char1=characters, char2=characters)
    def test_viewpoint_multiple_characters(self, char1, char2):
        roster = Roster.for_mapping(
            {Point(1, 1): char1, Point(2, 0): char2},
            area=Area(Point(0, 0), Point(3, 3)),
        )
        viewpoint = Viewpoint(Point(0, 1), roster)
        assert len(viewpoint) == 2
        assert viewpoint.character_at(Vector(1, 0)) == char1
        assert viewpoint.character_at(Vector(2, -1)) == char2


class TestMove:
    @given(position_dicts(min_size=1).flatmap(dict_and_element))
    def test_zero_move_preserves_roster(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_mapping(positions, area_containing(positions))
        assert Move(character, position, position).next_roster(roster) == roster

    @given(position_dicts(min_size=1).flatmap(dict_and_element), st.from_type(Vector))
    def test_character_moves(self, positions_and_item, move_vector):
        positions, (position, character) = positions_and_item
        new_position = position + move_vector

        all_positions = list(positions) + [new_position]

        assume(not any(pos == new_position for pos, _ in positions.items()))
        roster = Roster.for_mapping(positions, area_containing(all_positions))
        move = Move(character, position, new_position)

        next_roster = move.next_roster(roster)

        assert next_roster.character_at(new_position) == character

    @given(mover=characters, obstacle=characters)
    def test_move_to_occupied_position(self, mover, obstacle):
        positions = {Point(0, 0): mover, Point(1, 1): obstacle}

        roster = Roster.for_mapping(positions, area_containing(positions))
        move = Move(mover, Point(0, 0), Point(1, 1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    @given(
        areas().flatmap(
            lambda area: st.tuples(st.just(area), position_dicts_in(area, min_size=1))
        ),
        st.from_type(Point),
    )
    def test_move_out_of_bounds(self, area_and_positions, new_position):
        area, positions = area_and_positions
        position, character = next(iter(positions.items()))

        assume(new_position not in area)

        roster = Roster.for_mapping(positions, area)
        move = Move(character, position, new_position)

        with pytest.raises(ValueError):
            move.next_roster(roster)

    @given(character=characters, non_existent_character=characters)
    def test_move_of_non_existent_character(self, character, non_existent_character):
        roster = Roster.for_mapping(
            {Point(0, 0): character}, Area(Point(0, 0), Point(5, 5))
        )
        move = Move(non_existent_character, Point(1, 1), Point(2, 1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    @given(mover=characters, non_mover=characters)
    def test_move_preserves_non_moving_character(self, mover, non_mover):
        positions = {Point(0, 0): mover, Point(1, 1): non_mover}
        roster = Roster.for_mapping(positions, area_containing(positions))
        move = Move(mover, Point(0, 0), Point(0, 1))
        assert move.next_roster(roster).character_at(Point(1, 1)) is non_mover


class Target:

    undead = False

    def __init__(self, attack_result):
        self._attack_result = attack_result

    def attacked(self):
        return self._attack_result


class TestChangeCharacter:
    @given(characters)
    def test_fails_if_target_not_in_roster(self, instigator):
        roster = Roster.for_mapping(
            {Point(0, 0): instigator}, Area(Point(0, 0), Point(5, 5))
        )
        action = ChangeCharacter(instigator, Point(1, 1), do_nothing)
        with pytest.raises(ValueError):
            action.next_roster(roster)

    @given(instigator=characters, target=characters)
    def test_fails_if_instigator_not_in_roster(self, instigator, target):
        roster = Roster.for_mapping(
            {Point(0, 0): target}, Area(Point(0, 0), Point(5, 5))
        )
        action = ChangeCharacter(instigator, target, do_nothing)
        with pytest.raises(ValueError):
            action.next_roster(roster)

    @given(attacker=characters)
    def test_attacks_target(self, attacker):
        target = Character(living=True, undead=False)
        positions = {Point(0, 0): attacker, Point(1, 1): target}

        roster = Roster.for_mapping(positions, area_containing(positions))
        attack = ChangeCharacter(attacker, Point(1, 1), kill)
        new_roster = attack.next_roster(roster)

        new_character = new_roster.character_at(Point(1, 1))
        assert new_character is not None
        assert not new_character.living

    @given(attacker=characters, target=characters)
    def test_preserves_attacker(self, attacker, target):
        positions = {Point(0, 0): attacker, Point(1, 1): target}

        roster = Roster.for_mapping(positions, area_containing(positions))
        attack = ChangeCharacter(attacker, Point(1, 1), kill)
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(0, 0)) is attacker

    def test_changes_character_state(self):
        character = Character(living=False, undead=False)
        position = Point(0, 1)
        state_change = ChangeCharacter(character, position, reanimate)
        roster = Roster.for_mapping(
            {position: character}, Area(Point(0, 0), Point(5, 5))
        )

        next_roster = state_change.next_roster(roster)

        new_character = next_roster.character_at(Point(0, 1))
        assert new_character is not None
        assert new_character.undead
