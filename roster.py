from collections import Counter
import math

from space import Point


class Roster:

    @classmethod
    def for_value(cls, value):
        if isinstance(value, Roster):
            return value
        if hasattr(value, 'items'):
            return Roster(value.items())
        if value is None:
            return Roster([])

        raise TypeError('Expected Roster instance or dict-like value')

    def __init__(self, character_positions):
        self._positions = {}
        seen_characters = set()
        for position, character in character_positions:
            point = Point(*position)
            if point in self._positions:
                raise ValueError(f"Multiple characters at position {position}")
            if character in seen_characters:
                raise ValueError(f"Character {character} in multiple places")

            self._positions[point] = character
            seen_characters.add(character)

    def character_at(self, position):
        return self._positions.get(position)

    def nearest_to(self, origin, predicate=None):
        min_distance = math.inf
        best_position = None
        closest_character = None
        if predicate is None:
            predicate = lambda item: True

        for pos, char in self:
            if pos == origin or not predicate(char):
                continue
            distance = (pos - origin).distance
            if distance < min_distance:
                min_distance = distance
                best_position = pos
                closest_character = char

        if closest_character is None:
            return None
        else:
            return (best_position, closest_character)

    def move_character(self, old_position, new_position):
        new_positions = [(new_position if pos == old_position else pos, char)
                         for (pos, char) in self._positions.items()]
        return Roster(new_positions)

    def change_character(self, position, change):
        new_positions = [(pos, change(char) if pos == position else char)
                         for (pos, char) in self._positions.items()]
        return Roster(new_positions)


    def __contains__(self, character):
        return character in self._positions.values()

    def __iter__(self):
        return iter(self._positions.items())

    def __len__(self):
        return len(self._positions)

    def __repr__(self):
        return 'Roster({})'.format(self._positions)

    def __eq__(self, other):
        return self._positions == other._positions


class Move:

    def __init__(self, character, old_position, new_position):
        self._character = character
        self._old_position = old_position
        self._new_position = new_position

    def next_roster(self, roster):
        old_position = self._old_position
        new_position = self._new_position

        if old_position == new_position:
            return roster

        character = self._character

        if character not in roster:
            raise ValueError('Attempt to move non-existent character '
                             '{}'.format(character))

        return roster.move_character(old_position, new_position)

    def __eq__(self, other):
        return (isinstance(other, Move)
                and self._character == other._character
                and self._old_position == old_position
                and self._new_position == new_position)

    def __repr__(self):
        return f'Move({self._character}, {self._old_position, self._new_position})'


class Attack:

    def __init__(self, attacker, target_position):
        self._attacker = attacker
        self._target_position = target_position

    def next_roster(self, roster):
        attacker = self._attacker
        target_position = self._target_position

        if attacker not in roster:
            raise ValueError('Attack by non-existent character '
                             '{}'.format(attacker))
        if roster.character_at(self._target_position) is None:
            raise ValueError('Attack on non-existent character at '
                             '{}'.format(target_position))

        return roster.change_character(target_position, self._attack)

    def _attack(self, character):
        return character.attacked()

    def __eq__(self, other):
        return (isinstance(other, Attack)
                and self._attacker == other._attacker
                and self._target == other._target_position)

    def __repr__(self):
        return f'Attack({self._attacker}, {self._target})'


class StateChange:

    def __init__(self, character, position, new_state):
        self._character = character
        self._position = position
        self._new_state = new_state

    def next_roster(self, roster):
        character = self._character
        position = self._position

        if character not in roster:
            raise ValueError('Attempt to change non-existent character '
                             '{}'.format(character))

        return roster.change_character(position, self._change_state)

    def _change_state(self, character):
        return character.with_state(self._new_state)

    def __eq__(self, other):
        return (isinstance(other, StateChange)
                and self._character == other._character
                and self._new_state == other._new_state)

    def __repr__(self):
        return f'StateChange({self._character}, {self._new_state})'
