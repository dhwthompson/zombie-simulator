from roster import Roster, Attack, Move, StateChange
from space import Area, Point
import tracing


class World:

    def __init__(self, width, height, characters):
        self._area = Area(Point(0, 0), Point(width, height))
        self._width = width
        self._height = height
        self._roster = Roster.for_value(characters)

        bad_positions = [p for p, _ in self._roster if p not in self._area]
        if bad_positions:
            raise ValueError('Off-world characters at '
                             '{}'.format(bad_positions))

    def __repr__(self):
        return 'World({}, {}, {})'.format(self._width, self._height, self._roster)

    def __eq__(self, other):
        return (isinstance(other, World)
                and self._width == other._width
                and self._height == other._height
                and self._roster == other._roster)

    @property
    def rows(self):
        return [self._row(y) for y in range(self._height)]

    def _row(self, y):
        return [self._roster.character_at((x, y)) for x in range(self._width)]

    def viewpoint(self, origin):
        return Viewpoint(origin, self._roster)

    def tick(self):
        world = self
        for (position, character) in self._roster:
            context = {"character_living":
                character.living, "character_undead": character.undead}
            with tracing.span("character_action", context):
                if character not in world._roster:
                    continue
                viewpoint = world.viewpoint(position)
                limits = self._area.from_origin(position)
                actions = AvailableActions(position, character)

                action = character.next_action(viewpoint, limits, actions)

                new_roster = action.next_roster(world._roster)
                world = World(self._width, self._height, new_roster)
        return world


class AvailableActions:

    def __init__(self, position, character):
        self._position = position
        self._character = character

    def move(self, vector):
        return Move(self._character, vector)

    def attack(self, vector):
        return Attack(self._character, self._position + vector)

    def change_state(self, new_state):
        return StateChange(self._character, new_state)


class Viewpoint:

    def __init__(self, origin, roster):
        self._origin = origin
        self._roster = roster

    def __iter__(self):
        return iter((position - self._origin, character) for position, character in
                self._roster)

    def __len__(self):
        return len(self._roster)

    def nearest(self, predicate):
        nearest = self._roster.nearest_to(self._origin, predicate)
        if nearest:
            return nearest[0] - self._origin

    def from_offset(self, offset):
        return Viewpoint(self._origin + offset, self._roster)


class WorldBuilder:

    def __init__(self, width, height, population):
        grid = self._grid(width, height)

        starting_positions = {point: character
                              for point, character in zip(grid, population)
                              if character is not None}

        self._world = World(width, height, starting_positions)

    def _grid(self, width, height):
        for y in range(height):
            for x in range(width):
                yield Point(x, y)

    @property
    def world(self):
        return self._world
