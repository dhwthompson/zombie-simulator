from collections import Counter
from itertools import chain
import math

from tree import SpaceTree


class HasAttributes:
    def __init__(self, **attributes):
        self._attributes = attributes

    def __call__(self, character):
        return all(
            getattr(character, name) == value
            for name, value in self._attributes.items()
        )


class Roster:
    @classmethod
    def for_value(cls, value, area=None):
        if isinstance(value, Roster):
            return value

        if area is None:
            raise ValueError("Roster requires area parameter")

        return Roster(value, area)

    def __init__(
        self, character_positions, area, *, _undead_positions=None, _characters=None
    ):
        if _characters is not None:
            # This only turns up when we're building up from an existing roster
            self._positions = character_positions
            self._area = area
            self._undead_positions = _undead_positions
            self._characters = _characters
        else:
            self._build_positions(character_positions, area)

    def _build_positions(self, character_positions, area):
        self._characters = set()
        self._area = area

        undead_positions = SpaceTree.build(area)
        other_positions = SpaceTree.build(area)

        for position, character in character_positions.items():
            if position not in self._area:
                raise ValueError(f"{position} is not in the world area")
            if position in undead_positions or position in other_positions:
                raise ValueError(f"Multiple characters at position {position}")
            if character in self._characters:
                raise ValueError(f"Character {character} in multiple places")

            if character.undead:
                undead_positions = undead_positions.set(position, character)
            else:
                other_positions = other_positions.set(position, character)

            self._characters.add(character)

        self._undead_positions = undead_positions
        self._positions = other_positions

    def character_at(self, position):
        return self._undead_positions.get(position) or self._positions.get(position)

    def nearest_to(self, origin, *, undead, **attributes):
        if undead:
            return self._undead_positions.nearest_to(
                origin, HasAttributes(**attributes)
            )
        else:
            return self._positions.nearest_to(origin, HasAttributes(**attributes))

    def move_character(self, old_position, new_position):
        if new_position not in self._area:
            raise ValueError(f"{new_position} is not in the world area")

        if new_position in self._undead_positions or new_position in self._positions:
            raise ValueError(f"Attempt to move to occupied position {new_position}")

        undead_positions = self._undead_positions
        other_positions = self._positions

        if old_position in undead_positions:
            character = undead_positions[old_position]
            undead_positions = undead_positions.unset(old_position).set(
                new_position, character
            )
        elif old_position in other_positions:
            character = other_positions[old_position]
            other_positions = other_positions.unset(old_position).set(
                new_position, character
            )
        else:
            raise ValueError(f"Attempt to move from unoccupied position {old_position}")

        return Roster(
            other_positions,
            self._area,
            _characters=self._characters,
            _undead_positions=undead_positions,
        )

    def change_character(self, position, change):
        undead_positions = self._undead_positions
        other_positions = self._positions

        if position in undead_positions:
            old_character = undead_positions[position]
            undead_positions = undead_positions.unset(position)
        elif position in other_positions:
            old_character = other_positions[position]
            other_positions = other_positions.unset(position)

        new_character = change(old_character)
        if new_character.undead:
            undead_positions = undead_positions.set(position, new_character)
        else:
            other_positions = other_positions.set(position, new_character)

        new_characters = self._characters - set([old_character]) | set([new_character])
        return Roster(
            other_positions,
            self._area,
            _characters=new_characters,
            _undead_positions=undead_positions,
        )

    def __contains__(self, character):
        return character in self._characters

    def __iter__(self):
        return iter(chain(self._positions.items(), self._undead_positions.items()))

    def __len__(self):
        return len(self._positions) + len(self._undead_positions)

    def __eq__(self, other):
        return (
            self._positions == other._positions
            and self._undead_positions == other._undead_positions
        )


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
            raise ValueError(f"Attempt to move non-existent character {character}")

        return roster.move_character(old_position, new_position)

    def __eq__(self, other):
        return (
            isinstance(other, Move)
            and self._character == other._character
            and self._old_position == old_position
            and self._new_position == new_position
        )

    def __repr__(self):
        return f"Move({self._character}, {self._old_position, self._new_position})"


class Attack:
    def __init__(self, attacker, target_position):
        self._attacker = attacker
        self._target_position = target_position

    def next_roster(self, roster):
        attacker = self._attacker
        target_position = self._target_position

        if attacker not in roster:
            raise ValueError(f"Attack by non-existent character {attacker}")
        if roster.character_at(self._target_position) is None:
            raise ValueError(f"Attack on non-existent character at {target_position}")

        return roster.change_character(target_position, self._attack)

    def _attack(self, character):
        return character.attacked()

    def __eq__(self, other):
        return (
            isinstance(other, Attack)
            and self._attacker == other._attacker
            and self._target == other._target_position
        )

    def __repr__(self):
        return f"Attack({self._attacker}, {self._target})"


class StateChange:
    def __init__(self, character, position, new_state):
        self._character = character
        self._position = position
        self._new_state = new_state

    def next_roster(self, roster):
        character = self._character
        position = self._position

        if character not in roster:
            raise ValueError(f"Attempt to change non-existent character {character}")

        return roster.change_character(position, self._change_state)

    def _change_state(self, character):
        return character.with_state(self._new_state)

    def __eq__(self, other):
        return (
            isinstance(other, StateChange)
            and self._character == other._character
            and self._new_state == other._new_state
        )

    def __repr__(self):
        return f"StateChange({self._character}, {self._new_state})"
