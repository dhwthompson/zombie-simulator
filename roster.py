import attr
from collections import Counter
from enum import Enum
from itertools import chain
import math
from typing import (
    Callable,
    Collection,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore

from space import Area, BoundingBox, Point, Vector
from tree import PartitionTree


class HasLifeState(Protocol):
    @property
    def living(self) -> bool:
        ...

    @property
    def undead(self) -> bool:
        ...


class LifeState(Enum):
    LIVING = 1
    DEAD = 2
    UNDEAD = 3

    @classmethod
    def for_attributes(cls, *, living: bool, undead: bool) -> "LifeState":
        if living and undead:
            raise ValueError("Illegal living/undead state")
        if undead:
            return LifeState.UNDEAD
        if living:
            return LifeState.LIVING
        else:
            return LifeState.DEAD

    @classmethod
    def for_character(cls, character: HasLifeState) -> "LifeState":
        return cls.for_attributes(living=character.living, undead=character.undead)


CharacterType = TypeVar("CharacterType", bound=HasLifeState)


@attr.s(auto_attribs=True, frozen=True)
class Match(Generic[CharacterType]):
    position: Point
    character: CharacterType


class Roster(Generic[CharacterType]):
    @classmethod
    def for_mapping(
        cls, character_positions: Mapping[Point, CharacterType], area: Area
    ) -> "Roster[CharacterType]":

        characters: Set[CharacterType] = set()
        positions: PartitionTree[LifeState, CharacterType] = PartitionTree.build(
            area, LifeState.for_character
        )

        for position, character in character_positions.items():
            if position not in area:
                raise ValueError(f"{position} is not in the world area")
            if position in positions:
                raise ValueError(f"Multiple characters at position {position}")
            if character in characters:
                raise ValueError(f"Character {character} in multiple places")

            positions = positions.set(position, character)
            characters.add(character)

        return Roster(area=area, positions=positions, characters=characters)

    def __init__(
        self,
        *,
        area: Area,
        characters: Set[CharacterType],
        positions: PartitionTree[LifeState, CharacterType],
    ):
        self._area = area
        self._characters = characters
        self._positions = positions

    @property
    def width(self) -> int:
        return self._area.width

    @property
    def height(self) -> int:
        return self._area.height

    def character_at(self, position: Point) -> Optional[CharacterType]:
        return self._positions.get(position)

    def characters_in(self, area: Area) -> Set[Match[CharacterType]]:
        return {Match(i.point, i.value) for i in self._positions.items_in(area)}

    def nearest_to(
        self, origin: Point, *, key: LifeState,
    ) -> Optional[Match[CharacterType]]:
        match = self._positions.nearest_to(origin, key=key)

        if match:
            return Match(position=match.point, character=match.value)
        else:
            return None

    def move_character(
        self, old_position: Point, new_position: Point
    ) -> "Roster[CharacterType]":
        if new_position not in self._area:
            raise ValueError(f"{new_position} is not in the world area")

        if new_position in self._positions:
            raise ValueError(f"Attempt to move to occupied position {new_position}")

        try:
            character = self._positions[old_position]
        except KeyError:
            raise ValueError(f"Attempt to move from unoccupied position {old_position}")

        positions = self._positions.unset(old_position).set(new_position, character)
        return Roster(area=self._area, characters=self._characters, positions=positions)

    def change_character(
        self, position: Point, change: Callable[[CharacterType], CharacterType]
    ) -> "Roster[CharacterType]":
        try:
            old_character = self._positions[position]
        except KeyError:
            raise ValueError(
                f"Attempt to change character at unoccupied position {position}"
            )

        new_character = change(old_character)
        positions = self._positions.unset(position).set(position, new_character)

        new_characters = self._characters - set([old_character]) | set([new_character])

        return Roster(area=self._area, characters=new_characters, positions=positions)

    def __contains__(self, character: CharacterType) -> bool:
        return character in self._characters

    @property
    def positions(self) -> Iterable[Tuple[Point, CharacterType]]:
        return self._positions.items()

    def __len__(self) -> int:
        return len(self._positions)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Roster):
            return False
        return self._positions == other._positions


class Viewpoint(Generic[CharacterType]):
    def __init__(self, origin: Point, roster: Roster[CharacterType]):
        self._origin = origin
        self._roster = roster

    def occupied_points_in(self, box: BoundingBox) -> Set[Vector]:
        area = box.to_area(self._origin)
        return {m.position - self._origin for m in self._roster.characters_in(area)}

    def nearest(self, key: LifeState) -> Optional[Vector]:
        nearest = self._roster.nearest_to(self._origin, key=key)
        if nearest:
            return nearest.position - self._origin
        else:
            return None

    def from_offset(self, offset: Vector) -> "Viewpoint[CharacterType]":
        return Viewpoint(self._origin + offset, self._roster)


@attr.s(auto_attribs=True, frozen=True)
class Move(Generic[CharacterType]):
    _character: CharacterType
    _old_position: Point
    _new_position: Point

    def next_roster(self, roster: Roster[CharacterType]) -> Roster[CharacterType]:
        old_position = self._old_position
        new_position = self._new_position

        if old_position == new_position:
            return roster

        character = self._character

        if character not in roster:
            raise ValueError(f"Attempt to move non-existent character {character}")

        return roster.move_character(old_position, new_position)


@attr.s(auto_attribs=True, frozen=True)
class ChangeCharacter(Generic[CharacterType]):
    _instigator: CharacterType
    _position: Point
    _change: Callable[[CharacterType], CharacterType]

    def next_roster(self, roster: Roster[CharacterType]) -> Roster[CharacterType]:
        if self._instigator not in roster:
            raise ValueError(f"Action by non-existent character {self._instigator}")

        character = roster.character_at(self._position)
        if character is None:
            raise ValueError(f"Action on non-existent character at {self._position}")

        return roster.change_character(self._position, self._change)
