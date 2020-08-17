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
from roster import Roster, ChangeCharacter, LifeState, Move, Viewpoint
from space import Area, BoundingBox, Point, Vector
import tracing


@attr.s(auto_attribs=True, frozen=True)
class Tick:
    roster: Roster[Character, LifeState]

    def next(self) -> Roster[Character, LifeState]:
        roster = self.roster
        area = self.roster._area

        for (position, character) in self.roster.positions:
            context = {
                "character_living": character.living,
                "character_undead": character.undead,
            }
            with tracing.span("character_action", context):
                if character not in roster:
                    continue
                viewpoint = Viewpoint(position, roster)
                limits = area.from_origin(position)
                actions = AvailableActions(position, character)

                action: Action = character.next_action(viewpoint, limits, actions)

                roster = action.next_roster(roster)
        return roster


class Action(Protocol):
    def next_roster(
        self, roster: Roster[Character, LifeState]) -> Roster[Character, LifeState]:
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


class Builder:
    def __init__(
        self, width: int, height: int, population: Iterable[Optional[Character]]
    ):
        grid = self._grid(width, height)
        area = self._area(width, height)

        starting_positions = {
            point: character
            for point, character in zip(grid, population)
            if character is not None
        }

        self._roster = Roster.for_mapping(starting_positions, area=area)

    def _area(self, width: int, height: int) -> Area:
        return Area(Point(0, 0), Point(width, height))

    def _grid(self, width: int, height: int) -> Generator[Point, None, None]:
        for y in range(height):
            for x in range(width):
                yield Point(x, y)

    @property
    def roster(self) -> Roster[Character, LifeState]:
        return self._roster
