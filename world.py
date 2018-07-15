from roster import Roster
from space import Area, Point


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

    @property
    def rows(self):
        return [self._row(y) for y in range(self._height)]

    def _row(self, y):
        return [self._roster.character_at((x, y)) for x in range(self._width)]

    def viewpoint(self, origin):
        return set([(position - origin, character)
                    for position, character in self._roster])

    def tick(self):
        world = self
        for (position, character) in self._roster:
            if character not in world._roster:
                continue
            viewpoint = world.viewpoint(position)
            limits = self._area.from_origin(position)
            action = character.next_action(viewpoint, limits)
            new_roster = action.next_roster(world._roster)
            world = World(self._width, self._height, new_roster)
        return world


class WorldBuilder:

    def __init__(self, width, height, population):
        grid = self._grid(width, height)

        starting_positions = [(point, character)
                              for point, character in zip(grid, population)
                              if character is not None]

        self._world = World(width, height, starting_positions)

    def _grid(self, width, height):
        for y in range(height):
            for x in range(width):
                yield Point(x, y)

    @property
    def world(self):
        return self._world
