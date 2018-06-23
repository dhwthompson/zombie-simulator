from collections import Counter

from space import BoundingBox, Point, Vector


class World:
    def __init__(self, width, height, characters=None):
        self._width = width
        self._height = height
        self._roster = Roster.for_value(characters)

    @property
    def rows(self):
        return [self._row(y) for y in range(self._height)]

    def _row(self, y):
        return [self._roster.character_at((x, y)) for x in range(self._width)]

    def move_character(self, character, new_position):
        if character not in self._roster:
            raise ValueError('Attempt to move non-existent character '
                             '{}'.format(character))
        if self._roster.character_at(new_position) == character:
            return self
        if self._roster.character_at(new_position) is not None:
            raise ValueError('Invalid move to occupied space '
                             '{}'.format(new_position))

        new_positions = [(new_position if char == character else pos, char)
                         for (pos, char) in self._roster]

        return World(self._width, self._height, new_positions)

    def viewpoint(self, origin):
        return set([(position - origin, character)
                    for position, character in self._roster])

    def tick(self):
        world = self
        for (position, character) in self._roster:
            viewpoint = world.viewpoint(position)
            limits = BoundingBox(Point(0, 0) - position,
                                 Point(self._width, self._height) - position)
            move = character.move(viewpoint, limits)
            world = world.move_character(character, position + move)
        return world


class Roster:

    @classmethod
    def for_value(cls, value):
        if isinstance(value, Roster):
            return value
        if hasattr(value, 'items'):
            return Roster(value.items())
        if value is None:
            return Roster([])

        return Roster(value)

    def __init__(self, character_positions):
        self._positions = [(Point(*position), character)
                           for position, character in character_positions]
        position_counts = Counter(p[0] for p in self._positions)

        self._check_unique((p[0] for p in self._positions),
                           'Multiply-occupied points in roster')

        self._check_unique((p[1] for p in self._positions),
                           'Characters in multiple places')

    def _check_unique(self, collection, message):
        duplicates = [item for item, count in Counter(collection).items()
                      if count > 1]
        if duplicates:
            raise ValueError('{}: {}'.format(message, duplicates))


    def character_at(self, position):
        for p, char in self._positions:
            if p == position:
                return char
        else:
            return None

    def __contains__(self, character):
        return any(c == character for _, c in self._positions)

    def __iter__(self):
        return iter(self._positions)


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
