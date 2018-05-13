from time import sleep

from character import Population
from renderer import Renderer
from world import World

WORLD_WIDTH = 60
WORLD_HEIGHT = 30
HUMAN_DENSITY = 0.05
ZOMBIE_CHANCE = 0.9

population = Population(HUMAN_DENSITY, ZOMBIE_CHANCE)
world = World.populated_by(WORLD_WIDTH, WORLD_HEIGHT, population)
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
    pass
