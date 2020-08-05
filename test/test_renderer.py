import attr

from renderer import Renderer
from space import Point


@attr.s(frozen=True)
class World:
    width = attr.ib(default=None)
    height = attr.ib(default=None)
    positions = attr.ib(default=None)


@attr.s(auto_attribs=True, frozen=True)
class Character:
    living: bool
    undead: bool


class TestRenderer:
    def test_single_cell_world(self):
        world = World(width=1, height=1, positions=[])
        renderer = Renderer(world)
        assert renderer.lines == [". "]

    def test_single_row_world(self):
        world = World(width=5, height=1, positions=[])
        renderer = Renderer(world)
        assert renderer.lines == [". . . . . "]

    def test_multi_row_world(self):
        world = World(width=5, height=3, positions=[])
        renderer = Renderer(world)
        assert renderer.lines == [". . . . . ", ". . . . . ", ". . . . . "]

    def test_human(self):
        human = Character(living=True, undead=False)
        world = World(width=3, height=1, positions=[(Point(1, 0), human)])
        renderer = Renderer(world)
        assert renderer.lines == [". \U0001F468 . "]

    def test_dead_human(self):
        dead_human = Character(living=False, undead=False)
        world = World(width=3, height=1, positions=[(Point(1, 0), dead_human)],)
        renderer = Renderer(world)
        assert renderer.lines == [". \U0001F480 . "]

    def test_zombie(self):
        zombie = Character(living=False, undead=True)
        world = World(width=3, height=1, positions=[(Point(1, 0), zombie)])
        renderer = Renderer(world)
        assert renderer.lines == [". \U0001F9DF . "]
