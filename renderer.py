from typing import Iterable, Optional

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


class Character(Protocol):
    @property
    def living(self) -> bool:
        ...

    @property
    def undead(self) -> bool:
        ...


Row = Iterable[Optional[Character]]


class World(Protocol):
    @property
    def rows(self) -> Iterable[Row]:
        ...


class Renderer:
    def __init__(self, world: World):
        self._world = world

    @property
    def lines(self) -> Iterable[str]:
        return [self._render_row(row) for row in self._world.rows]

    def _render_row(self, row: Row) -> str:
        return "".join(self._render_character(c) for c in row)

    def _render_character(self, character: Optional[Character]) -> str:
        if not character:
            return ". "
        if character.living:
            return "\U0001F468 "
        elif character.undead:
            return "\U0001F9DF "
        else:
            return "\U0001F480 "
