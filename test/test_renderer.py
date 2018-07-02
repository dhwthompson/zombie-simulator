from collections import namedtuple

from renderer import Renderer


World = namedtuple('World', ['rows'])
Character = namedtuple('Character', ['living', 'undead'])


class TestRenderer:

    def test_single_cell_world(self):
        world = World([[None]])
        renderer = Renderer(world)
        assert renderer.lines == ['. ']

    def test_single_row_world(self):
        world = World([[None] * 5])
        renderer = Renderer(world)
        assert renderer.lines == ['. . . . . ']

    def test_multi_row_world(self):
        world = World([[None] * 5] * 3)
        renderer = Renderer(world)
        assert renderer.lines == ['. . . . . ', '. . . . . ', '. . . . . ']

    def test_human(self):
        human = Character(living=True, undead=False)
        world = World([[None, human, None]])
        renderer = Renderer(world)
        assert renderer.lines == ['. \U0001F468 . ']

    def test_dead_human(self):
        dead_human = Character(living=False, undead=False)
        world = World([[None, dead_human, None]])
        renderer = Renderer(world)
        assert renderer.lines == ['. \U0001F480 . ']

    def test_zombie(self):
        zombie = Character(living=False, undead=True)
        world = World([[None, zombie, None]])
        renderer = Renderer(world)
        assert renderer.lines == ['. \U0001F9DF . ']
