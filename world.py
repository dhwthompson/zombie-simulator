import attr
from typing import (
    Collection,
    Generator,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeVar,
)

from barriers import Barriers
from character import Character, LifeState, State
from roster import Roster, ChangeCharacter, Move, Viewpoint
from space import Area, BoundingBox, Point, Vector
import tracing


@attr.s(auto_attribs=True, frozen=True)
class Tick:
    roster: Roster[Character, LifeState]
    barriers: Barriers = Barriers.NONE

    def next(self) -> Roster[Character, LifeState]:
        roster = self.roster
        area = self.roster._area

        for (position, character) in self.roster.positions:
            context = {
                "character_state": character.life_state.name,
            }
            with tracing.span("character_action", context):
                if character not in roster:
                    continue
                viewpoint = Viewpoint(position, roster, self.barriers)
                limits = area.from_origin(position)
                actions = AvailableActions(position, character)

                action: Action = character.next_action(viewpoint, limits, actions)

                roster = action.next_roster(roster)
        return roster


class Action(Protocol):
    def next_roster(
        self, roster: Roster[Character, LifeState]
    ) -> Roster[Character, LifeState]:
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
        self,
        area: Area,
        population: Iterable[Optional[Character]],
        barriers: Barriers = Barriers.NONE,
    ):
        character_positions = (p for p in area if not barriers.occupied(p))

        starting_positions = {
            point: character
            for point, character in zip(character_positions, population)
            if character is not None
        }

        self._roster = Roster.partitioned(
            starting_positions, area=area, partition_func=LifeState.for_character
        )

    @property
    def roster(self) -> Roster[Character, LifeState]:
        return self._roster
