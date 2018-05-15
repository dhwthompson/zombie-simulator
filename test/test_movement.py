from character import Human, Zombie
from world import World


def test_zombies_approach_humans():
    zombie = Zombie()
    human = Human()

    characters = {
            (0, 0): zombie,
            (2, 2): human
    }

    world = World(3, 3, characters)

    world = world.tick()

    assert world.rows == [[None, None, None],
                          [None, zombie, None],
                          [None, None, human]]


def test_zombie_non_collision():
    """Make sure the tick can't take two zombies onto the same spot."""
    zombie, zombie2, human = Zombie(), Zombie(), Human()
    characters = {
            (1, 0): zombie,
            (2, 0): zombie2,
            (2, 2): human
    }

    world = World(3, 3, characters)

    world = world.tick()

    cells = sum(world.rows, [])

    assert zombie in cells
    assert zombie2 in cells
    assert human in cells


def test_world_boundaries():
    """Make sure zombies can't move off the map."""
    characters = {
            (0, 0): Zombie(),
            (1, 0): Zombie(),
            (2, 0): Human()
    }

    world = World(3, 1, characters)
    assert world.tick().rows == world.rows
