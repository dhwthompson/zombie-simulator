class Renderer:
    def __init__(self, world):
        self._world = world

    @property
    def lines(self):
        return [self._render_row(row) for row in self._world.rows]

    def _render_row(self, row):
        return ''.join(self._render_character(c) for c in row)

    def _render_character(self, character):
        if not character:
            return '. '
        if character.living:
            return '\U0001F468 '
        else:
            return '\U0001F9DF '
