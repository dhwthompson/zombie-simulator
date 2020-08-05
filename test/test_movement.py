from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

from character import default_human, default_zombie
from space import Point
from world import World


@st.composite
def worlds(
    draw, inhabitants=st.one_of(st.builds(default_human), st.builds(default_zombie))
):
    dimensions = st.integers(min_value=1, max_value=100)
    x, y = draw(dimensions), draw(dimensions)
    points = st.builds(
        Point,
        st.integers(min_value=0, max_value=x - 1),
        st.integers(min_value=0, max_value=y - 1),
    )
    characters = draw(st.dictionaries(points, inhabitants))
    return World.for_mapping(x, y, characters)


@pytest.mark.integration
@given(worlds())
@settings(max_examples=25)
def test_tick_returns_a_world(world):
    assert isinstance(world.tick(), World)


@pytest.mark.integration
@given(worlds())
@settings(max_examples=25)
def test_tick_keeps_zombies(world):
    old_zombie_positions = set(pos for pos, char in world.positions if char.undead)
    new_world = world.tick()
    new_zombie_positions = set(pos for pos, char in world.positions if char.undead)

    assert old_zombie_positions == new_zombie_positions


@pytest.mark.integration
def test_zombies_approach_humans():
    zombie = default_zombie()
    human = default_human()

    characters = {Point(0, 0): zombie, Point(2, 2): human}

    world = World.for_mapping(3, 3, characters)

    world = world.tick()

    assert sorted(world.positions) == [(Point(1, 1), zombie), (Point(2, 2), human)]
