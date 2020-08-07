import attr
from typing import (
    Collection,
    Generator,
    Generic,
    Iterable,
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

from character import Character, State
from roster import Roster, ChangeCharacter, Move
from space import Area, BoundingBox, Point, Vector
import tracing


@attr.s(auto_attribs=True, frozen=True)
class World:
    _area: Area
    _roster: Roster[Character]

    @classmethod
    def for_mapping(
        cls, width: int, height: int, characters: Mapping[Point, Character],
    ) -> "World":
        area = Area(Point(0, 0), Point(width, height))
        roster = Roster.for_mapping(characters, area=area)
        return World(area=area, roster=roster)

    @property
    def width(self) -> int:
        return self._area.width

    @property
    def height(self) -> int:
        return self._area.height

    @property
    def positions(self) -> Iterable[Tuple[Point, Character]]:
        return iter(self._roster)

    def viewpoint(self, origin: Point) -> "Viewpoint":
        return Viewpoint(origin, self._roster)


@attr.s(auto_attribs=True, frozen=True)
class Tick:
    world: World

    def next(self) -> World:
        world = self.world
        area = self.world._area

        for (position, character) in self.world._roster:
            context = {
                "character_living": character.living,
                "character_undead": character.undead,
            }
            with tracing.span("character_action", context):
                if character not in world._roster:
                    continue
                viewpoint = world.viewpoint(position)
                limits = area.from_origin(position)
                actions = AvailableActions(position, character)

                action: Action = character.next_action(viewpoint, limits, actions)

                new_roster = action.next_roster(world._roster)
                world = World(area, new_roster)
        return world


class Action(Protocol):
    def next_roster(self, roster: Roster[Character]) -> Roster[Character]:
        ...


class AvailableActions:
    def __init__(self, position: Point, character: Character):
        self._position = position
        self._character = character

    def move(self, vector: Vector) -> Action:
        return Move(self._character, self._position, self._position + vector)

    def attack(self, vector: Vector) -> Action:
        return ChangeCharacter(
            self._character, self._position + vector, Character.attacked
        )

    def change_state(self, new_state: State) -> Action:
        return ChangeCharacter(
            self._character, self._position, lambda c: c.with_state(new_state)
        )


class Viewpoint:
    def __init__(self, origin: Point, roster: Roster[Character]):
        self._origin = origin
        self._roster = roster

    def __iter__(self) -> Iterable[Tuple[Vector, Character]]:
        return iter(
            (position - self._origin, character) for position, character in self._roster
        )

    def __len__(self) -> int:
        return len(self._roster)

    def character_at(self, offset: Vector) -> Optional[Character]:
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

    def from_offset(self, offset: Vector) -> "Viewpoint":
        return Viewpoint(self._origin + offset, self._roster)


class WorldBuilder:
    def __init__(
        self, width: int, height: int, population: Iterable[Optional[Character]]
    ):
        grid = self._grid(width, height)

        starting_positions = {
            point: character
            for point, character in zip(grid, population)
            if character is not None
        }

        self._world = World.for_mapping(width, height, starting_positions)

    def _grid(self, width: int, height: int) -> Generator[Point, None, None]:
        for y in range(height):
            for x in range(width):
                yield Point(x, y)

    @property
    def world(self) -> World:
        return self._world
