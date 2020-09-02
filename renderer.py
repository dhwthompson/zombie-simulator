from barriers import BarrierPoint
from character import LifeState
from space import Point
from typing import Any, Iterable, Optional, Tuple

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


class Character(Protocol):
    @property
    def life_state(self) -> LifeState:
        ...


Row = Iterable[Optional[Character]]


class World(Protocol):
    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...

    @property
    def positions(self) -> Iterable[Tuple[Point, Character]]:
        ...


class Barriers(Protocol):
    @property
    def positions(self) -> Iterable[Tuple[Point, BarrierPoint]]:
        ...


class NoBarriers:
    @property
    def positions(self) -> Iterable[Any]:
        return []


class Renderer:
    def __init__(self, world: World, barriers: Optional[Barriers] = None):
        self._world = world
        self._barriers: Barriers = barriers or NoBarriers()

    @property
    def lines(self) -> Iterable[str]:
        all_lines = [[". "] * self._world.width for _ in range(self._world.height)]
        for position, barrier in self._barriers.positions:
            all_lines[position.y][position.x] = self._render_barrier(barrier)
        for position, character in self._world.positions:
            all_lines[position.y][position.x] = self._render_character(character)
        return ["".join(line) for line in all_lines]

    def _render_row(self, row: Row) -> str:
        return "".join(self._render_character(c) for c in row)

    def _render_barrier(self, barrier: BarrierPoint) -> str:
        barrier_glyphs = {
            BarrierPoint(): "\u2573",
            BarrierPoint(above=True): "\u2575",
            BarrierPoint(below=True): "\u2577",
            BarrierPoint(left=True): "\u2574",
            BarrierPoint(right=True): "\u2576",
            BarrierPoint(above=True, below=True): "\u2502",
            BarrierPoint(above=True, left=True): "\u2518",
            BarrierPoint(above=True, right=True): "\u2514",
            BarrierPoint(below=True, left=True): "\u2510",
            BarrierPoint(below=True, right=True): "\u250C",
            BarrierPoint(left=True, right=True): "\u2500",
            BarrierPoint(above=True, below=True, left=True): "\u2524",
            BarrierPoint(above=True, below=True, right=True): "\u251C",
            BarrierPoint(above=True, left=True, right=True): "\u2534",
            BarrierPoint(below=True, left=True, right=True): "\u252C",
            BarrierPoint(above=True, below=True, left=True, right=True): "\u253C",
        }
        return barrier_glyphs[barrier] + ("\u2500" if barrier.right else " ")

    def _render_character(self, character: Optional[Character]) -> str:
        if not character:
            return ". "

        character_strings = {
            LifeState.LIVING: "\U0001F9D1 ",
            LifeState.UNDEAD: "\U0001F9DF ",
            LifeState.DEAD: "\U0001F480 ",
        }
        return character_strings[character.life_state]
