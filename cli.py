from itertools import islice
from os import environ
import re
import shutil
import sys
import time

from character import default_human, default_zombie
from population import Population
from renderer import Renderer
from world import WorldBuilder


def get_world_size(size_string, get_terminal_size, default):
    if not size_string:
        return default

    if size_string == 'auto':
        terminal_size = get_terminal_size()
        return (terminal_size.columns // 2, terminal_size.lines - 1)

    size_match = re.match(r'(\d+)x(\d+)$', size_string)

    if size_match:
        return tuple([int(d) for d in size_match.groups()])

    raise ValueError('Unrecognised format "{}"'.format(size_string))


world_width, world_height = get_world_size(environ.get('WORLD_SIZE'),
                                           shutil.get_terminal_size,
                                           default=(60, 30))

DENSITY = float(environ.get('DENSITY', 0.05))
ZOMBIE_CHANCE = float(environ.get('ZOMBIE_CHANCE', 0.2))
TICK = float(environ.get('TICK', 0.1))

MAX_AGE = None

if environ.get('MAX_AGE'):
    MAX_AGE = int(environ.get('MAX_AGE'))

population = Population((DENSITY * (1 - ZOMBIE_CHANCE), default_human),
                        (DENSITY * ZOMBIE_CHANCE, default_zombie))
world = WorldBuilder(world_width, world_height, population).world
renderer = Renderer(world)

def each_interval(interval, current_time=time.time, sleep=time.sleep):
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


def clear():
    print('\033[H\033[J', end='')


if __name__ == '__main__':
    ticks = each_interval(TICK)
    if MAX_AGE is not None:
        ticks = islice(ticks, MAX_AGE)

    try:
        for _ in ticks:
            clear()
            for line in renderer.lines:
                print(line)
            world = world.tick()
            renderer = Renderer(world)
    except KeyboardInterrupt:
        sys.exit(1)
