from os import environ
import re
import shutil
import sys
from time import sleep

from character import Population
from renderer import Renderer
from world import World

def _get_world_size(size_string, default):
    if not size_string:
        return default

    if size_string == 'auto':
        terminal_size = shutil.get_terminal_size()
        return (terminal_size.columns // 2, terminal_size.lines - 1)

    size_match = re.match('(\d+)x(\d+)$', size_string)

    if size_match:
        return tuple([int(d) for d in size_match.groups()])

    raise ValueError('Unrecognised format "{}"'.format(size_string))


world_width, world_height = _get_world_size(environ.get('WORLD_SIZE'),
                                            default=(60, 30))

HUMAN_DENSITY = float(environ.get('DENSITY', 0.05))
ZOMBIE_CHANCE = float(environ.get('ZOMBIE_CHANCE', 0.9))

population = Population(HUMAN_DENSITY, ZOMBIE_CHANCE)
world = World.populated_by(world_width, world_height, population)
renderer = Renderer(world)

def clear():
    print('\033[H\033[J', end='')

try:
    while True:
        clear()
        for line in renderer.lines:
            print(line)
        sleep(0.2)
        world = world.tick()
        renderer = Renderer(world)
except KeyboardInterrupt:
    sys.exit(1)
