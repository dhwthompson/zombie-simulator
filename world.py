from space import BoundingBox, Point, Vector


class World:
    def __init__(self, width, height, characters=None):
        self._width = width
        self._height = height
        self._characters = dict(characters or {})

    @property
    def rows(self):
        return [self._row(y) for y in range(self._height)]

    def _row(self, y):
        return [self._character_at((x, y)) for x in range(self._width)]

    def _character_at(self, position):
        return self._characters.get(position)

    @property
    def _character_positions(self):
        return [(Point(*position), character)
                for position, character in self._characters.items()]

    def with_character(self, position, character):
        if character is None:
            raise ValueError('Cannot add a null character')

        new_characters = dict([(pos, char) for (pos, char) in
                self._character_positions if char != character])
        if position in new_characters:
            message = 'Invalid move to occupied space {}'.format(position)
            raise ValueError(message)
        new_characters.update({position: character})
        return World(self._width, self._height, new_characters)

    def viewpoint(self, origin):
        return set([(position - origin, character)
                    for position, character in self._character_positions])

    def tick(self):
        world = self
        for (position, character) in self._character_positions:
            viewpoint = world.viewpoint(position)
            limits = BoundingBox(Point(0, 0) - position,
                                 Point(self._width, self._height) - position)
            move = character.move(viewpoint, limits)
            world = world.with_character(position + move, character)
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
