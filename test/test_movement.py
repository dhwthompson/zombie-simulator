from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

from character import default_human, default_zombie
from world import World

@st.composite
def worlds(draw, inhabitants=st.one_of(st.builds(default_human), st.builds(default_zombie))):
    dimensions = st.integers(min_value=1, max_value=100)
    x, y = draw(dimensions), draw(dimensions)
    points = st.tuples(st.integers(min_value=0, max_value=x-1),
                       st.integers(min_value=0, max_value=y-1))
    characters = draw(st.dictionaries(points, inhabitants))
    return World(x, y, characters)


@pytest.mark.integration
@given(worlds())
@settings(max_examples=25)
def test_tick_returns_a_world(world):
    assert isinstance(world.tick(), World)


@pytest.mark.integration
@given(worlds())
@settings(max_examples=25)
def test_characters_preserved(world):
    assert len(sum(world.rows, [])) == len(sum(world.tick().rows, []))


@pytest.mark.integration
@given(worlds())
@settings(max_examples=25)
def test_tick_keeps_zombies(world):
    old_zombies = set(z for z in sum(world.rows, [])
                      if z and z.undead)
    new_world = world.tick()
    new_zombies = set(z for z in sum(new_world.rows, [])
                      if z and z.undead)

    assert old_zombies == new_zombies


@pytest.mark.integration
def test_zombies_approach_humans():
    zombie = default_zombie()
    human = default_human()

    characters = {
            (0, 0): zombie,
            (2, 2): human
    }

    world = World(3, 3, characters)

    world = world.tick()

    assert world.rows == [[None, None, None],
                          [None, zombie, None],
                          [None, None, human]]
