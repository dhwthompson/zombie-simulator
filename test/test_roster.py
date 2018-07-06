from hypothesis import assume, given
from hypothesis import strategies as st

import pytest

from roster import Attack, Move, Roster
from space import Point, Vector


def positions_unique(positions):
    return len(set(p[0] for p in positions)) == len(positions)

characters = st.builds(object)
position_lists = st.lists(st.tuples(st.from_type(Point), characters))
unique_position_lists = position_lists.filter(positions_unique)


def list_and_element(l):
    """Given a list, return a strategy of that list and one of its elements.

    This can be connected onto an existing list strategy using the `flatmap`
    method.
    """
    return st.tuples(st.just(l), st.sampled_from(l))


class TestRoster:

    @given(unique_position_lists)
    def test_takes_position_character_pairs(self, positions):
        Roster(positions)

    @given(unique_position_lists.flatmap(list_and_element))
    def test_character_at_position(self, positions_and_item):
        positions, (position, character) = positions_and_item

        assert Roster(positions).character_at(position) == character

    @given(st.from_type(Point))
    def test_rejects_duplicate_position(self, point):
        positions = [(point, object()), (point, object())]
        with pytest.raises(ValueError):
            Roster(positions)

    @given(characters)
    def test_rejects_duplicate_character(self, character):
        positions = [(Point(0, 0), character), (Point(1, 1), character)]
        with pytest.raises(ValueError) as e:
            Roster(positions)

    @given(unique_position_lists)
    def test_value_equality(self, positions):
        assert Roster(positions) == Roster(list(positions))

    @given(unique_position_lists)
    def test_order_indifference(self, positions):
        assert Roster(positions) == Roster(reversed(positions))

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
        positions, (_, character) = positions_and_item
        roster = Roster(positions)
        assert Move(character, Vector.ZERO).next_roster(roster) == roster

    @given(unique_position_lists.flatmap(list_and_element), st.from_type(Vector))
    def test_character_moves(self, positions_and_item, move_vector):
        positions, (position, character) = positions_and_item
        new_position = position + move_vector
        assume(not any(pos == new_position for pos, _ in positions))
        roster = Roster(positions)
        move = Move(character, move_vector)

        next_roster = move.next_roster(roster)

        assert next_roster.character_at(new_position) == character

    def test_move_to_occupied_position(self):
        a, b = object(), object()
        roster = Roster([(Point(0, 0), a), (Point(1, 1), b)])
        move = Move(b, Vector(-1, -1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    def test_move_of_non_existent_character(self):
        a, b = object(), object()
        roster = Roster([(Point(0, 0), a)])
        move = Move(b, Vector(1, 1))
        with pytest.raises(ValueError):
            move.next_roster(roster)

    def test_move_preserves_non_moving_character(self):
        a, b = object(), object()
        roster = Roster([(Point(0, 0), a), (Point(1, 1), b)])
        move = Move(a, Vector(0, 1))
        assert move.next_roster(roster).character_at(Point(1, 1)) is b


class Target:

    def __init__(self, attack_result):
        self._attack_result = attack_result

    def attacked(self):
        return self._attack_result


class TestAttack:

    def test_fails_if_target_not_in_roster(self):
        attacker, target = object(), object()
        roster = Roster([(Point(0, 0), attacker)])
        attack = Attack(attacker, target)
        with pytest.raises(ValueError):
            attack.next_roster(roster)

    def test_fails_if_attacker_not_in_roster(self):
        attacker, target = object(), object()

        roster = Roster([(Point(0, 0), target)])
        attack = Attack(attacker, target)
        with pytest.raises(ValueError):
            attack.next_roster(roster)

    def test_attacks_target(self):
        attacker = object()
        attacked = object()
        target = Target(attacked)

        roster = Roster([(Point(0, 0), attacker), (Point(1, 1), target)])
        attack = Attack(attacker, target)
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(1, 1)) is attacked

    def test_preserves_attacker(self):
        attacker = object()
        target = Target(object())

        roster = Roster([(Point(0, 0), attacker), (Point(1, 1), target)])
        attack = Attack(attacker, target)
        new_roster = attack.next_roster(roster)
        assert new_roster.character_at(Point(0, 0)) is attacker


