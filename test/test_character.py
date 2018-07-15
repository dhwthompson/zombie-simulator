from hypothesis import assume, example, given, note
from hypothesis import strategies as st

import pytest

from .strategies import list_and_element
from character import Character, CharacterState, default_human, default_zombie
from character import (MaximiseShortestDistance, MinimiseDistance,
                       MoveShortestDistance, nearest, Obstacles)
from space import BoundingBox, Vector


def vectors(max_offset=None):
    if max_offset is not None:
        coordinates = st.integers(min_value=-max_offset, max_value=max_offset)
    else:
        coordinates = st.integers()
    return st.builds(Vector, dx=coordinates, dy=coordinates)


humans = st.builds(default_human)
zombies = st.builds(default_zombie)
characters = st.one_of(humans, zombies)

containing_boxes = (st.from_type(BoundingBox)
                    .filter(lambda box: Vector.ZERO in box))

def environments(characters=characters, min_size=None, max_size=None):
    all_envs = st.lists(st.tuples(vectors(), characters),
                        min_size=min_size,
                        max_size=max_size)
    return all_envs.filter(lambda e: not any(pos == Vector.ZERO for pos, _ in e))


class TestObstacles:

    @given(environments())
    @example([])
    @example([(Vector.ZERO, object())])
    def test_never_includes_zero_vector(self, environment):
        assert Vector.ZERO not in Obstacles(environment)

    @given(environments().flatmap(list_and_element))
    def test_includes_entry(self, env_and_entry):
        environment, (position, _) = env_and_entry
        assume(position != Vector.ZERO)

        assert position in Obstacles(environment)


class TestMinimiseDistance:

    def test_fails_with_no_target(self):
        with pytest.raises(ValueError):
            MinimiseDistance(target=None)

    @given(target=vectors(), moves=st.lists(vectors(), min_size=1))
    def test_picks_from_available_moves(self, target, moves):
        strategy = MinimiseDistance(target)
        assert strategy.best_move(moves) in moves

    @given(target=vectors(), moves=st.lists(vectors(), min_size=1))
    def test_gets_as_close_to_target_as_possible(self, target, moves):
        strategy = MinimiseDistance(target)

        best_move = strategy.best_move(moves)

        distance_after_move = (target - best_move).distance
        assert all(distance_after_move <= (target - move).distance
                   for move in moves)

    def test_chooses_shortest_best_move(self):
        target = Vector(1, 0)
        strategy = MinimiseDistance(target)
        moves = [Vector.ZERO, Vector(1, 1)]

        assert strategy.best_move(moves) == Vector.ZERO
        # To make sure we're not lucking out based on the order
        assert strategy.best_move(reversed(moves)) == Vector.ZERO



class TestMaximiseShortestDistance:

    def test_fails_with_no_targets(self):
        with pytest.raises(ValueError):
            MaximiseShortestDistance(targets=[])

    @given(targets=st.lists(vectors(), min_size=1),
           moves=st.lists(vectors(), min_size=1))
    def test_picks_from_available_moves(self, targets, moves):
        strategy = MaximiseShortestDistance(targets)
        assert strategy.best_move(moves) in moves

    @given(targets=st.lists(vectors(), min_size=1),
           moves=st.lists(vectors(), min_size=1))
    def test_keeps_away_from_all_targets(self, targets, moves):
        strategy = MaximiseShortestDistance(targets)

        best_move = strategy.best_move(moves)

        def distance_after_move(move):
            return min((target - move).distance for target in targets)

        best_move_distance = distance_after_move(best_move)
        note(f'Best distance, after {best_move}: {best_move_distance}')

        for move in moves:
            move_distance = distance_after_move(move)
            note(f'Distance after {move}: {move_distance}')

        assert all(best_move_distance >= distance_after_move(move)
                   for move in moves)

    def test_chooses_shortest_best_move(self):
        targets = [Vector(1, 2)]
        strategy = MaximiseShortestDistance(targets)
        moves = [Vector.ZERO, Vector(1, 0), Vector(2, 0)]

        assert strategy.best_move(moves) == Vector.ZERO
        # To make sure we're not lucking out based on the order
        assert strategy.best_move(reversed(moves)) == Vector.ZERO


class TestMoveShortestDistance:

    def test_fails_with_no_moves(self):
        strategy = MoveShortestDistance()
        with pytest.raises(ValueError):
            strategy.best_move([])

    @given(st.lists(vectors(), min_size=1))
    def test_takes_shortest_move(self, moves):
        strategy = MoveShortestDistance()

        best_move = strategy.best_move(moves)

        assert all(best_move.distance <= m.distance for m in moves)


class TestNearest:

    def test_returns_none_with_no_vectors(self):
        assert nearest([]) is None

    @given(st.lists(vectors(), min_size=1))
    def test_returns_shortest_vector(self, targets):
        result = nearest(targets)

        assert all(result.distance <= t.distance for t in targets)


class TestZombie:

    @pytest.fixture
    def zombie(self):
        return default_zombie()

    def test_not_living(self, zombie):
        assert not zombie.living

    def test_undead(self, zombie):
        assert zombie.undead

    @given(environments())
    def test_move_returns_a_vector(self, zombie, environment):
        assert isinstance(zombie.move(environment), Vector)

    @given(environments(characters=humans, min_size=1, max_size=1))
    def test_never_moves_away_from_human(self, zombie, environment):
        move = zombie.move(environment)
        assert (environment[0][0] - move).distance <= environment[0][0].distance

    @given(environments(characters=humans, min_size=1, max_size=1))
    def test_move_approaches_single_human(self, zombie, environment):
        assume(environment[0][0].distance > 1)
        move = zombie.move(environment)
        assert (environment[0][0] - move).distance < environment[0][0].distance

    @given(environments())
    def test_does_not_move_onto_occupied_space(self, zombie, environment):
        move = zombie.move(environment)
        assert move not in [e[0] for e in environment]

    @given(environments())
    def test_moves_up_to_one_space(self, zombie, environment):
        move = zombie.move(environment)
        assert abs(move.dx) <= 1
        assert abs(move.dy) <= 1

    @given(environments(characters=zombies))
    def test_ignores_zombies(self, zombie, environment):
        assert zombie.move(environment) == Vector.ZERO

    @given(environment=environments(), limits=containing_boxes)
    def test_respects_limits(self, zombie, environment, limits):
        move = zombie.move(environment, limits)
        assert move in limits

    def test_nothing_nearby(self, zombie):
        assert zombie.move([]) == Vector.ZERO

    def test_nearest_human(self, zombie):
        environment = [(Vector(3, -3), default_human()),
                       (Vector(2, 2), default_human()),
                       (Vector(-3, 3), default_human())]

        assert zombie.move(environment) == Vector(1, 1)

    def test_close_human(self, zombie):
        """Check the zombie doesn't try to move onto or away from a human.

        In future versions, this test will be replaced by biting logic."""
        environment = [(Vector(1, 1), default_human())]

        expected_moves = [Vector(0, 0), Vector(0, 1), Vector(1, 0)]
        assert zombie.move(environment) in expected_moves

    def test_blocked_path(self, zombie):
        environment = [(Vector(2, 2), default_human()),
                       (Vector(1, 1), default_zombie()),
                       (Vector(1, 0), default_zombie()),
                       (Vector(0, 1), default_zombie())]
        assert zombie.move(environment) == Vector.ZERO

    def test_all_paths_blocked(self, zombie):
        """Test that zombies stay still when surrounded by other zombies.

        This effectively functions as a last check that zombies always have
        their own position as a fall-back, and don't register as blocking their
        own non-movement.
        """

        def env_contents(vector):
            return default_zombie() if vector else zombie

        vectors = [Vector(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]
        distant_human = [(Vector(2, 2), default_human())]
        zombies_all_around = [(v, env_contents(v)) for v in vectors]

        assert zombie.move(distant_human + zombies_all_around) == Vector.ZERO

    def test_alternate_path(self, zombie):
        environment = [(Vector(2, 2), default_human()),
                       (Vector(1, 1), default_zombie()),
                       (Vector(1, 0), default_zombie())]
        assert zombie.move(environment) == Vector(0, 1)

    @given(st.lists(st.tuples(vectors(max_offset=1), humans), min_size=1, max_size=1))
    def test_attack(self, zombie, environment):
        human = environment[0][1]

        assert zombie.attack(environment) == human

    @given(environments(characters=humans))
    @example([(Vector(2, 0), default_human())])
    def test_targets_out_of_range(self, zombie, environment):
        biting_range = BoundingBox(Vector(-1, -1), Vector(2, 2))
        assume(all(e[0] not in biting_range for e in environment))

        assert zombie.attack(environment) is None


class TestHuman:

    @pytest.fixture
    def human(self):
        return default_human()

    def test_living(self, human):
        assert human.living

    def test_not_undead(self, human):
        assert not human.undead

    @given(environments())
    def test_move_returns_vector(self, human, environment):
        assert isinstance(human.move(environment), Vector)

    @given(environments(characters=humans))
    def test_ignores_humans(self, human, environment):
        assert human.move(environment) == Vector.ZERO

    @given(environments())
    def test_does_not_move_into_occupied_space(self, human, environment):
        move = human.move(environment)
        assert not any(e[0] == move for e in environment)

    @given(environments(characters=zombies, min_size=1, max_size=1))
    def test_runs_away_from_zombie(self, human, environment):
        move = human.move(environment)
        zombie_vector = environment[0][0]
        assert (zombie_vector - move).distance > zombie_vector.distance

    @given(environments(characters=zombies, min_size=1))
    def test_runs_away_from_zombies(self, human, environment):
        move = human.move(environment)
        min_distance_before = min(e[0].distance for e in environment)
        min_distance_after = min((e[0] - move).distance for e in environment)
        assert min_distance_after >= min_distance_before

    @given(environments())
    def test_moves_up_to_two_spaces(self, human, environment):
        move = human.move(environment)
        assert abs(move.dx) <= 2
        assert abs(move.dy) <= 2

    @given(environment=environments(), limits=containing_boxes)
    def test_respects_limits(self, human, environment, limits):
        move = human.move(environment, limits)
        assert move in limits

    def test_does_not_move_in_empty_environment(self, human):
        assert human.move([]) == Vector.ZERO

    def test_does_not_obstruct_self(self, human):
        environment = [(Vector.ZERO, human)]
        assert human.move([]) == Vector.ZERO

    def test_attacked_human_is_dead(self, human):
        assert not human.attacked().living

    def test_attacked_human_is_not_undead(self, human):
        assert not human.attacked().undead

    @given(environments())
    def test_dead_humans_stay_still(self, environment):
        human = Character(state=CharacterState.DEAD)
        assert human.move(environment) == Vector.ZERO

    @given(environments())
    def test_never_attacks(self, human, environment):
        assert human.attack(environment) is None
