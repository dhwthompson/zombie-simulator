from collections import OrderedDict
from operator import itemgetter

from hypothesis import assume, given, note
from hypothesis import strategies as st

import pytest

from .strategies import list_and_element, dict_and_element
from roster import Attack, Move, Roster, StateChange
from space import Point, Vector


characters = st.builds(object)

def position_dicts(min_size=0):
    # Using OrderedDict so Hypothesis can pick a random element
    return st.dictionaries(st.from_type(Point), characters, min_size=min_size, dict_class=OrderedDict)


class TestRoster:

    @given(position_dicts())
    def test_takes_position_character_map(self, positions):
        Roster.for_value(positions)

    @given(position_dicts(min_size=1).flatmap(dict_and_element))
    def test_character_at_position(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions)
        assert roster.character_at(position) == character

    @given(characters)
    def test_rejects_duplicate_character(self, character):
        positions = {Point(0, 0): character, Point(1, 1): character}
        with pytest.raises(ValueError) as e:
            Roster.for_value(positions)

    @given(position_dicts())
    def test_value_equality(self, positions):
        assert Roster.for_value(positions) == Roster.for_value(positions.copy())

    def test_empty_roster(self):
        roster = Roster.for_value({})
        assert not roster

    def test_roster_for_itself(self):
        roster = Roster.for_value({(0, 2): object()})
        assert roster.for_value(roster) is roster

    def test_no_nearest_character(self):
        roster = Roster.for_value({(1, 1): object()})
        assert roster.nearest_to(Point(1, 1)) is None

    @given(position_dicts(min_size=2).flatmap(dict_and_element))
    def test_nearest_to(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions)

        nearest_position, nearest_character = roster.nearest_to(position)

        assert nearest_position != position
        assert nearest_character != character

        best_distance = min((p - position).distance for p, c in positions.items() if c != character)
        assert best_distance == (nearest_position - position).distance

    @given(st.lists(st.tuples(st.from_type(Point), st.integers()), min_size=2,
        unique_by=(itemgetter(0), itemgetter(1))).map(OrderedDict).flatmap(dict_and_element))
    def test_nearest_to_predicate(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions)

        note(f"Roster: {roster}")
        note(f"Sample position: {position}")
        note(f"Character: {character}")

        def predicate(char):
            return char % 2 == 0

        assume(any(predicate(char) and char != character for (_, char) in positions.items()))

        nearest_position, nearest_character = roster.nearest_to(position, predicate)

        assert nearest_character % 2 == 0


class TestMove:

    @given(position_dicts(min_size=1).flatmap(dict_and_element))
    def test_zero_move_preserves_roster(self, positions_and_item):
        positions, (position, character) = positions_and_item
        roster = Roster.for_value(positions)
        assert Move(character, position, position).next_roster(roster) == roster

    @given(position_dicts(min_size=1).flatmap(dict_and_element), st.from_type(Vector))
    def test_character_moves(self, positions_and_item, move_vector):
        positions, (position, character) = positions_and_item
        new_position = position + move_vector
        assume(not any(pos == new_position for pos, _ in positions.items()))
        roster = Roster.for_value(positions)
        move = Move(character, position, new_position)

        next_roster = move.next_roster(roster)

        assert next_roster.character_at(new_position) == character

    def test_move_to_occupied_position(self):
        a, b = object(), object()
        roster = Roster.for_value({Point(0, 0): a, Point(1, 1): b})
        move = Move(b, Point(0, 0), Point(1, 1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    def test_move_of_non_existent_character(self):
        a, b = object(), object()
        roster = Roster.for_value({Point(0, 0): a})
        move = Move(b, Point(1, 1), Point(2, 1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    def test_move_preserves_non_moving_character(self):
        a, b = object(), object()
        roster = Roster.for_value({Point(0, 0): a, Point(1, 1): b})
        move = Move(a, Point(0, 0), Point(0, 1))
        assert move.next_roster(roster).character_at(Point(1, 1)) is b


class Target:

    def __init__(self, attack_result):
        self._attack_result = attack_result

    def attacked(self):
        return self._attack_result


class TestAttack:

    def test_fails_if_target_not_in_roster(self):
        attacker, target = object(), object()
        roster = Roster.for_value({Point(0, 0): attacker})
        attack = Attack(attacker, target)
        with pytest.raises(ValueError):
            attack.next_roster(roster)

    def test_fails_if_attacker_not_in_roster(self):
        attacker, target = object(), object()

        roster = Roster.for_value({Point(0, 0): target})
        attack = Attack(attacker, target)
        with pytest.raises(ValueError):
            attack.next_roster(roster)

    def test_attacks_target(self):
        attacker = object()
        attacked = object()
        target = Target(attacked)

        roster = Roster.for_value({Point(0, 0): attacker, Point(1, 1): target})
        attack = Attack(attacker, Point(1, 1))
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(1, 1)) is attacked

    def test_preserves_attacker(self):
        attacker = object()
        target = Target(object())

        roster = Roster.for_value({Point(0, 0): attacker, Point(1, 1): target})
        attack = Attack(attacker, Point(1, 1))
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(0, 0)) is attacker


class Character:

    def __init__(self, state):
        self.state = state

    def with_state(self, state):
        return Character(state=state)


class TestStateChange:

    def test_fails_if_character_not_in_roster(self):
        character, position, state = object(), Point(0, 0), object()

        state_change = StateChange(character, position, state)

        roster = Roster.for_value({})

        with pytest.raises(ValueError):
            state_change.next_roster(roster)

    def test_changes_character_state(self):
        character, state = Character(state=None), object()
        position = Point(0, 1)
        state_change = StateChange(character, position, state)
        roster = Roster.for_value({position: character})

        next_roster = state_change.next_roster(roster)

        assert next_roster.character_at(Point(0, 1)).state == state

