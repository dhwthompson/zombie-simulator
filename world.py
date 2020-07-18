import attr

from roster import Roster, Attack, Move, StateChange
from space import Area, Point
import tracing


@attr.s(auto_attribs=True, frozen=True)
class World:
    _area: Area
    _roster: Roster

    @classmethod
    def for_mapping(cls, width, height, characters):
        area = Area(Point(0, 0), Point(width, height))
        roster = Roster.for_mapping(characters, area=area)
        return World(area=area, roster=roster)

    @property
    def rows(self):
        return [self._row(y) for y in range(self._area.height)]

    def _row(self, y):
        return [self._roster.character_at(Point(x, y)) for x in range(self._area.width)]

    def viewpoint(self, origin):
        return Viewpoint(origin, self._roster)

    def tick(self):
        world = self
        for (position, character) in self._roster:
            context = {
                "character_living": character.living,
                "character_undead": character.undead,
            }
            with tracing.span("character_action", context):
                if character not in world._roster:
                    continue
                viewpoint = world.viewpoint(position)
                limits = self._area.from_origin(position)
                actions = AvailableActions(position, character)

                action = character.next_action(viewpoint, limits, actions)

                new_roster = action.next_roster(world._roster)
                world = World(self._area, new_roster)
        return world


class AvailableActions:
    def __init__(self, position, character):
        self._position = position
        self._character = character

    def move(self, vector):
        return Move(self._character, self._position, self._position + vector)

    def attack(self, vector):
        return Attack(self._character, self._position + vector)

    def change_state(self, new_state):
        return StateChange(self._character, self._position, new_state)


class Viewpoint:
    def __init__(self, origin, roster):
        self._origin = origin
        self._roster = roster

    def __iter__(self):
        return iter(
            (position - self._origin, character) for position, character in self._roster
        )

    def __len__(self):
        return len(self._roster)

    def character_at(self, offset):
        return self._roster.character_at(self._origin + offset)

    def nearest(self, **attributes):
        nearest = self._roster.nearest_to(self._origin, **attributes)
        if nearest:
            return nearest.position - self._origin

    def from_offset(self, offset):
        return Viewpoint(self._origin + offset, self._roster)


class WorldBuilder:
    def __init__(self, width, height, population):
        grid = self._grid(width, height)

        starting_positions = {
            point: character
            for point, character in zip(grid, population)
            if character is not None
        }

        self._world = World.for_mapping(width, height, starting_positions)

    def _grid(self, width, height):
        for y in range(height):
            for x in range(width):
                yield Point(x, y)

    @property
    def world(self):
        return self._world
