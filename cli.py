from contextlib import ExitStack
from itertools import islice
from os import environ
import re
import shutil
import sys
import time
from typing import Callable, Generator, Iterator, Optional, Tuple

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore

from character import Character, default_human, default_zombie
from population import Population
from renderer import Renderer
import tracing
from world import WorldBuilder


class TerminalSize(Protocol):
    columns: int
    lines: int


def get_world_size(
    size_string: Optional[str],
    get_terminal_size: Callable[[], TerminalSize],
    default: Tuple[int, int],
) -> Tuple[int, int]:
    if not size_string:
        return default

    if size_string == "auto":
        terminal_size = get_terminal_size()
        return (terminal_size.columns // 2, terminal_size.lines - 1)

    size_match = re.match(r"(\d+)x(\d+)$", size_string)

    if size_match:
        return (int(size_match.group(1)), int(size_match.group(2)))

    raise ValueError(f'Unrecognised format "{size_string}"')


world_width, world_height = get_world_size(
    environ.get("WORLD_SIZE"), shutil.get_terminal_size, default=(60, 30)
)

DENSITY = float(environ.get("DENSITY", 0.05))
ZOMBIE_CHANCE = float(environ.get("ZOMBIE_CHANCE", 0.2))
TICK = float(environ.get("TICK", 0.1))

MAX_AGE = None

max_age_str = environ.get("MAX_AGE")
MAX_AGE = int(max_age_str) if max_age_str else None


def each_interval(
    interval: float,
    current_time: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
) -> Generator[None, None, None]:
    """Yield at regular intervals.

    This generator waits at least `interval` seconds between each value it
    yields. If it has been more than `interval` seconds since the last yielded
    value, it will yield the next one immediately, but will not "race" to catch
    up.
    """
    while True:
        next_tick = current_time() + interval
        yield
        sleep_time = max(next_tick - current_time(), 0)
        sleep(sleep_time)


def clear() -> None:
    print("\033[H\033[J", end="")


if __name__ == "__main__":
    population = Population[Character](
        (DENSITY * (1 - ZOMBIE_CHANCE), default_human),
        (DENSITY * ZOMBIE_CHANCE, default_zombie),
    )
    world = WorldBuilder(world_width, world_height, population).world
    renderer = Renderer(world)

    ticks: Iterator[None] = each_interval(TICK)
    if MAX_AGE is not None:
        ticks = islice(ticks, MAX_AGE)

    tracing_context = ExitStack()

    trace_file_name = environ.get("TRACEFILE")
    if trace_file_name:
        trace_file = open(trace_file_name, mode="w")
        tracing_context.enter_context(trace_file)
        tracing_context.enter_context(tracing.file_tracing(trace_file))

    with tracing_context:
        try:
            for _ in ticks:
                clear()
                for line in renderer.lines:
                    print(line)

                with tracing.span("tick"):
                    old_world, world = world, world.tick()

                if old_world == world:
                    break
                renderer = Renderer(world)
        except KeyboardInterrupt:
            sys.exit(1)
