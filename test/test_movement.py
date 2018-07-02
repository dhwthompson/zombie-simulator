from hypothesis import given
from hypothesis import strategies as st

from character import Human, Zombie
from world import World

@st.composite
def worlds(draw, inhabitants=st.one_of(st.builds(Human), st.builds(Zombie))):
    dimensions = st.integers(min_value=1, max_value=100)
    x, y = draw(dimensions), draw(dimensions)
    points = st.tuples(st.integers(min_value=0, max_value=x-1),
                       st.integers(min_value=0, max_value=y-1))
    characters = draw(st.dictionaries(points, inhabitants))
    return World(x, y, characters)


@given(worlds())
def test_tick_returns_a_world(world):
    assert isinstance(world.tick(), World)


@given(worlds())
def test_characters_preserved(world):
    assert len(sum(world.rows, [])) == len(sum(world.tick().rows, []))


@given(worlds())
def test_tick_keeps_zombies(world):
    old_zombies = set(z for z in sum(world.rows, [])
                      if z and z.undead)
    new_world = world.tick()
    new_zombies = set(z for z in sum(new_world.rows, [])
                      if z and z.undead)

    assert old_zombies == new_zombies


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
