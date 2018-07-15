from collections import Counter

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

        return Roster(value)

    def __init__(self, character_positions):
        self._positions = [(Point(*position), character)
                           for position, character in character_positions]

        self._check_unique((p[0] for p in self._positions),
                           'Multiply-occupied points in roster')

        self._check_unique((p[1] for p in self._positions),
                           'Characters in multiple places')

    def _check_unique(self, collection, message):
        duplicates = [item for item, count in Counter(collection).items()
                      if count > 1]
        if duplicates:
            raise ValueError('{}: {}'.format(message, duplicates))

    def character_at(self, position):
        for p, char in self._positions:
            if p == position:
                return char
        else:
            return None

    def __contains__(self, character):
        return any(c == character for _, c in self._positions)

    def __iter__(self):
        return iter(self._positions)

    def __repr__(self):
        return 'Roster({})'.format(self._positions)

    def __eq__(self, other):
        return sorted(self._positions) == sorted(other._positions)


class Move:

    def __init__(self, character, move_vector):
        self._character = character
        self._move_vector = move_vector

    def next_roster(self, roster):
        if not self._move_vector:
            return roster

        character = self._character

        if character not in roster:
            raise ValueError('Attempt to move non-existent character '
                             '{}'.format(character))

        new_positions = [(pos + self._move_vector if char == character else pos, char)
                         for (pos, char) in roster]
        return Roster(new_positions)

    def __eq__(self, other):
        return (isinstance(other, Move)
                and self._character == other._character
                and self._move_vector == other._move_vector)


    def __repr__(self):
        return f'Move({self._character}, {self._move_vector})'


class Attack:

    def __init__(self, attacker, target):
        self._attacker = attacker
        self._target = target

    def next_roster(self, roster):
        attacker = self._attacker
        target = self._target

        if attacker not in roster:
            raise ValueError('Attack by non-existent character '
                             '{}'.format(attacker))
        if target not in roster:
            raise ValueError('Attack on non-existent character '
                             '{}'.format(target))

        new_positions = [(pos, char.attacked() if char == target else char)
                         for (pos, char) in roster]
        return Roster(new_positions)

    def __eq__(self, other):
        return (isinstance(other, Attack)
                and self._attacker == other._attacker
                and self._target == other._target)

    def __repr__(self):
        return f'Attack({self._attacker}, {self._target})'


