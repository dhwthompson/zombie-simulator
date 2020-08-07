import attr
from collections import Counter
from itertools import chain
import math
from typing import (
    Callable,
    Collection,
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
from tree import SpaceTree


class SupportsUndead(Protocol):
    @property
    def undead(self) -> bool:
        ...


CharacterType = TypeVar("CharacterType", bound=SupportsUndead)


class HasAttributes:
    def __init__(self, **attributes: bool):
        self._attributes = attributes

    def __call__(self, character: object) -> bool:
        return all(
            getattr(character, name) == value
            for name, value in self._attributes.items()
        )


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

        undead_positions: SpaceTree[CharacterType] = SpaceTree.build(area)
        other_positions: SpaceTree[CharacterType] = SpaceTree.build(area)

        for position, character in character_positions.items():
            if position not in area:
                raise ValueError(f"{position} is not in the world area")
            if position in undead_positions or position in other_positions:
                raise ValueError(f"Multiple characters at position {position}")
            if character in characters:
                raise ValueError(f"Character {character} in multiple places")

            if character.undead:
                undead_positions = undead_positions.set(position, character)
            else:
                other_positions = other_positions.set(position, character)

            characters.add(character)

        return Roster(
            area=area,
            undead_positions=undead_positions,
            non_undead_positions=other_positions,
            characters=characters,
        )

    def __init__(
        self,
        *,
        area: Area,
        characters: Set[CharacterType],
        undead_positions: SpaceTree[CharacterType],
        non_undead_positions: SpaceTree[CharacterType],
    ):
        self._area = area
        self._characters = characters
        self._undead_positions = undead_positions
        self._positions = non_undead_positions

    @property
    def width(self) -> int:
        return self._area.width

    @property
    def height(self) -> int:
        return self._area.height

    def character_at(self, position: Point) -> Optional[CharacterType]:
        return self._undead_positions.get(position) or self._positions.get(position)

    def characters_in(self, area: Area) -> Set[Match[CharacterType]]:
        all_items = self._undead_positions.items_in(area) | self._positions.items_in(
            area
        )
        return {Match(i.point, i.value) for i in all_items}

    def nearest_to(
        self, origin: Point, *, undead: bool, **attributes: bool
    ) -> Optional[Match[CharacterType]]:
        if undead:
            match = self._undead_positions.nearest_to(
                origin, HasAttributes(**attributes)
            )
        else:
            match = self._positions.nearest_to(origin, HasAttributes(**attributes))

        if match:
            return Match(position=match.point, character=match.value)
        else:
            return None

    def move_character(
        self, old_position: Point, new_position: Point
    ) -> "Roster[CharacterType]":
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
            area=self._area,
            characters=self._characters,
            undead_positions=undead_positions,
            non_undead_positions=other_positions,
        )

    def change_character(
        self, position: Point, change: Callable[[CharacterType], CharacterType]
    ) -> "Roster[CharacterType]":
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
            area=self._area,
            characters=new_characters,
            undead_positions=undead_positions,
            non_undead_positions=other_positions,
        )

    def __contains__(self, character: CharacterType) -> bool:
        return character in self._characters

    def __iter__(self) -> Iterator[Tuple[Point, CharacterType]]:
        return iter(self.positions)

    @property
    def positions(self) -> Iterable[Tuple[Point, CharacterType]]:
        return chain(self._positions.items(), self._undead_positions.items())

    def __len__(self) -> int:
        return len(self._positions) + len(self._undead_positions)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Roster):
            return False
        return (
            self._positions == other._positions
            and self._undead_positions == other._undead_positions
        )


class Viewpoint(Generic[CharacterType]):
    def __init__(self, origin: Point, roster: Roster[CharacterType]):
        self._origin = origin
        self._roster = roster

    def __iter__(self) -> Iterable[Tuple[Vector, CharacterType]]:
        return iter(
            (position - self._origin, character) for position, character in self._roster
        )

    def __len__(self) -> int:
        return len(self._roster)

    def character_at(self, offset: Vector) -> Optional[CharacterType]:
        return self._roster.character_at(self._origin + offset)

    def occupied_points_in(self, box: BoundingBox) -> Set[Vector]:
        area = box.to_area(self._origin)
        return {m.position - self._origin for m in self._roster.characters_in(area)}

    def nearest(self, **attributes: bool) -> Optional[Vector]:
        nearest = self._roster.nearest_to(self._origin, **attributes)
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
