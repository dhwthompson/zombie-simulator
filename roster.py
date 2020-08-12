import attr
from collections import Counter
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

        positions: Dict[bool, SpaceTree[CharacterType]] = {
            True: SpaceTree.build(area),
            False: SpaceTree.build(area),
        }

        for position, character in character_positions.items():
            if position not in area:
                raise ValueError(f"{position} is not in the world area")
            if any(position in tree for tree in positions.values()):
                raise ValueError(f"Multiple characters at position {position}")
            if character in characters:
                raise ValueError(f"Character {character} in multiple places")

            key = character.undead
            positions[key] = positions[key].set(position, character)

            characters.add(character)

        return Roster(area=area, positions=positions, characters=characters)

    def __init__(
        self,
        *,
        area: Area,
        characters: Set[CharacterType],
        positions: Dict[bool, SpaceTree[CharacterType]],
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
        for tree in self._positions.values():
            if (char := tree.get(position)) is not None:
                return char
        else:
            return None

    def characters_in(self, area: Area) -> Set[Match[CharacterType]]:
        matches: Set[Match[CharacterType]] = set()
        for tree in self._positions.values():
            matches |= {Match(i.point, i.value) for i in tree.items_in(area)}
        return matches

    def nearest_to(
        self, origin: Point, *, undead: bool, **attributes: bool
    ) -> Optional[Match[CharacterType]]:
        tree = self._positions[undead]
        tree_match = tree.nearest_to(origin, HasAttributes(**attributes))

        if tree_match:
            return Match(position=tree_match.point, character=tree_match.value)
        else:
            return None

    def move_character(
        self, old_position: Point, new_position: Point
    ) -> "Roster[CharacterType]":
        if new_position not in self._area:
            raise ValueError(f"{new_position} is not in the world area")

        if any(new_position in tree for tree in self._positions.values()):
            raise ValueError(f"Attempt to move to occupied position {new_position}")

        positions = self._positions.copy()

        for key, tree in positions.items():
            if old_position in tree:
                character = tree[old_position]
                positions[key] = tree.unset(old_position).set(new_position, character)
                break
        else:
            raise ValueError(f"Attempt to move from unoccupied position {old_position}")

        return Roster(area=self._area, characters=self._characters, positions=positions)

    def change_character(
        self, position: Point, change: Callable[[CharacterType], CharacterType]
    ) -> "Roster[CharacterType]":
        positions = self._positions.copy()

        for key, tree in positions.items():
            if position in tree:
                old_character = tree[position]
                positions[key] = tree.unset(position)

        new_character = change(old_character)

        positions[new_character.undead] = positions[new_character.undead].set(
            position, new_character
        )

        new_characters = self._characters - set([old_character]) | set([new_character])

        return Roster(area=self._area, characters=new_characters, positions=positions)

    def __contains__(self, character: CharacterType) -> bool:
        return character in self._characters

    def __iter__(self) -> Iterator[Tuple[Point, CharacterType]]:
        return iter(self.positions)

    @property
    def positions(self) -> Iterable[Tuple[Point, CharacterType]]:
        return chain.from_iterable(t.items() for t in self._positions.values())

    def __len__(self) -> int:
        return sum(len(t) for t in self._positions.values())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Roster):
            return False
        return self._positions == other._positions


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
