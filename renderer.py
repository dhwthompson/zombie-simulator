from character import LifeState
from space import Point
from typing import Iterable, Optional, Tuple

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


class Renderer:
    def __init__(self, world: World):
        self._world = world

    @property
    def lines(self) -> Iterable[str]:
        all_lines = [[". "] * self._world.width for _ in range(self._world.height)]
        for position, character in self._world.positions:
            all_lines[position.y][position.x] = self._render_character(character)
        return ["".join(line) for line in all_lines]

    def _render_row(self, row: Row) -> str:
        return "".join(self._render_character(c) for c in row)

    def _render_character(self, character: Optional[Character]) -> str:
        if not character:
            return ". "

        character_strings = {
            LifeState.LIVING: "\U0001F9D1 ",
            LifeState.UNDEAD: "\U0001F9DF ",
            LifeState.DEAD: "\U0001F480 ",
        }
        return character_strings[character.life_state]
