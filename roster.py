from collections import Counter
import math

from space import Point


class Roster:

    @classmethod
    def for_value(cls, value):
        if isinstance(value, Roster):
            return value
        return Roster(value)

        raise TypeError('Expected Roster instance or dict-like value')

    def __init__(self, character_positions, _characters=None):
        if _characters is not None:
            # This only turns up when we're building up from an existing roster
            self._positions = character_positions
            self._characters = _characters
        else:
            self._build_positions(character_positions)

    def _build_positions(self, character_positions):
        self._positions = {}
        self._characters = set()

        for position, character in character_positions.items():
            point = Point(*position)
            if point in self._positions:
                raise ValueError(f"Multiple characters at position {position}")
            if character in self._characters:
                raise ValueError(f"Character {character} in multiple places")

            self._positions[point] = character
            self._characters.add(character)

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
        positions = self._positions.copy()
        if new_position in positions:
            raise ValueError(f"Attempt to move to occupied position {new_position}")
        positions[new_position] = positions.pop(old_position)
        return Roster(positions, _characters=self._characters)

    def change_character(self, position, change):
        positions = self._positions.copy()
        old_character = positions[position]
        new_character = change(positions[position])
        positions[position] = new_character

        new_characters = self._characters - set([old_character]) | set([new_character])
        return Roster(positions, _characters=new_characters)

    def __contains__(self, character):
        return character in self._characters

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
