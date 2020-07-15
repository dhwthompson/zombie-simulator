from collections import OrderedDict
from operator import itemgetter

from hypothesis import assume, given, note
from hypothesis import strategies as st

import pytest

from .strategies import list_and_element, dict_and_element
from roster import Attack, Move, Roster, StateChange
from space import Area, Point, Vector


class Character:
    # Keeping this as an object to preserve object identity

    def __init__(self, undead, living):
        self.undead = undead
        self.living = living

    def __repr__(self):
        return f"Character(undead={self.undead}, living={self.living})"


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
        Roster.for_value(positions, area_containing(positions))

    @given(position_dicts(min_size=1).flatmap(dict_and_element))
    def test_character_at_position(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions, area_containing(positions))
        assert roster.character_at(position) == character

    @given(characters)
    def test_rejects_duplicate_character(self, character):
        positions = {Point(0, 0): character, Point(1, 1): character}
        with pytest.raises(ValueError) as e:
            Roster.for_value(positions, area_containing(positions))

    @given(position_dicts(), areas())
    def test_characters_outside_area(self, positions, area):
        assume(not all(p in area for p in positions))
        with pytest.raises(ValueError) as e:
            Roster.for_value(positions, area)

    @given(position_dicts())
    def test_value_equality(self, positions):
        area = area_containing(positions)
        assert Roster.for_value(positions, area) == Roster.for_value(
            positions.copy(), area
        )

    def test_empty_roster(self):
        roster = Roster.for_value({}, Area(Point(0, 0), Point(5, 5)))
        assert not roster

    @given(position_dicts(min_size=1))
    def test_non_empty_roster(self, positions):
        roster = Roster.for_value(positions, area_containing(positions))
        assert roster

    @given(characters)
    def test_roster_for_itself(self, character):
        roster = Roster.for_value(
            {(0, 2): character}, area=Area(Point(0, 0), Point(3, 3))
        )
        assert roster.for_value(roster) is roster

    @given(characters)
    def test_no_nearest_character(self, character):
        roster = Roster.for_value(
            {(1, 1): character}, area=Area(Point(0, 0), Point(2, 2))
        )
        assert roster.nearest_to(Point(1, 1), undead=True) is None
        assert roster.nearest_to(Point(1, 1), undead=False) is None

    @given(position_dicts(min_size=2).flatmap(dict_and_element))
    def test_nearest_undead(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions, area_containing(positions))

        assume(
            any(char.undead and char != character for (_, char) in positions.items())
        )

        nearest_position, nearest_character = roster.nearest_to(position, undead=True)

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
        roster = Roster.for_value(positions, area_containing(positions))

        note(f"Roster: {roster}")
        note(f"Sample position: {position}")
        note(f"Character: {character}")

        assume(
            any(
                char.living and not char.undead and char != character
                for (_, char) in positions.items()
            )
        )

        nearest_position, nearest_character = roster.nearest_to(
            position, undead=False, living=True
        )

        assert nearest_character.living


class TestMove:
    @given(position_dicts(min_size=1).flatmap(dict_and_element))
    def test_zero_move_preserves_roster(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions, area_containing(positions))
        assert Move(character, position, position).next_roster(roster) == roster

    @given(position_dicts(min_size=1).flatmap(dict_and_element), st.from_type(Vector))
    def test_character_moves(self, positions_and_item, move_vector):
        positions, (position, character) = positions_and_item
        new_position = position + move_vector

        all_positions = list(positions) + [new_position]

        assume(not any(pos == new_position for pos, _ in positions.items()))
        roster = Roster.for_value(positions, area_containing(all_positions))
        move = Move(character, position, new_position)

        next_roster = move.next_roster(roster)

        assert next_roster.character_at(new_position) == character

    @given(mover=characters, obstacle=characters)
    def test_move_to_occupied_position(self, mover, obstacle):
        positions = {Point(0, 0): mover, Point(1, 1): obstacle}

        roster = Roster.for_value(positions, area_containing(positions))
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

        roster = Roster.for_value(positions, area)
        move = Move(character, position, new_position)

        with pytest.raises(ValueError):
            move.next_roster(roster)

    @given(character=characters, non_existent_character=characters)
    def test_move_of_non_existent_character(self, character, non_existent_character):
        roster = Roster.for_value(
            {Point(0, 0): character}, Area(Point(0, 0), Point(5, 5))
        )
        move = Move(non_existent_character, Point(1, 1), Point(2, 1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    @given(mover=characters, non_mover=characters)
    def test_move_preserves_non_moving_character(self, mover, non_mover):
        positions = {Point(0, 0): mover, Point(1, 1): non_mover}
        roster = Roster.for_value(positions, area_containing(positions))
        move = Move(mover, Point(0, 0), Point(0, 1))
        assert move.next_roster(roster).character_at(Point(1, 1)) is non_mover


class Target:

    undead = False

    def __init__(self, attack_result):
        self._attack_result = attack_result

    def attacked(self):
        return self._attack_result


class TestAttack:
    @given(characters)
    def test_fails_if_target_not_in_roster(self, attacker):
        roster = Roster.for_value(
            {Point(0, 0): attacker}, Area(Point(0, 0), Point(5, 5))
        )
        attack = Attack(attacker, Point(1, 1))
        with pytest.raises(ValueError):
            attack.next_roster(roster)

    @given(attacker=characters, target=characters)
    def test_fails_if_attacker_not_in_roster(self, attacker, target):
        roster = Roster.for_value({Point(0, 0): target}, Area(Point(0, 0), Point(5, 5)))
        attack = Attack(attacker, target)
        with pytest.raises(ValueError):
            attack.next_roster(roster)

    @given(attacker=characters, attacked=characters)
    def test_attacks_target(self, attacker, attacked):
        target = Target(attacked)
        positions = {Point(0, 0): attacker, Point(1, 1): target}

        roster = Roster.for_value(positions, area_containing(positions))
        attack = Attack(attacker, Point(1, 1))
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(1, 1)) is attacked

    @given(attacker=characters, attacked_target=characters)
    def test_preserves_attacker(self, attacker, attacked_target):
        target = Target(attacked_target)
        positions = {Point(0, 0): attacker, Point(1, 1): target}

        roster = Roster.for_value(positions, area_containing(positions))
        attack = Attack(attacker, Point(1, 1))
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(0, 0)) is attacker


class StatefulCharacter:

    undead = False

    def __init__(self, state):
        self.state = state

    def with_state(self, state):
        return StatefulCharacter(state=state)


class TestStateChange:
    def test_fails_if_character_not_in_roster(self):
        character, position, state = object(), Point(0, 0), object()

        state_change = StateChange(character, position, state)

        roster = Roster.for_value({}, Area(Point(0, 0), Point(5, 5)))

        with pytest.raises(ValueError):
            state_change.next_roster(roster)

    def test_changes_character_state(self):
        character, state = StatefulCharacter(state=None), object()
        position = Point(0, 1)
        state_change = StateChange(character, position, state)
        roster = Roster.for_value({position: character}, Area(Point(0, 0), Point(5, 5)))

        next_roster = state_change.next_roster(roster)

        assert next_roster.character_at(Point(0, 1)).state == state
