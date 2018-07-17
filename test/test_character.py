from collections import namedtuple

from hypothesis import assume, example, given, note
from hypothesis import strategies as st

import pytest

from .strategies import list_and_element
from character import Character, default_human, default_zombie
from character import Dead, Living, Undead
from character import (MaximiseShortestDistance, MinimiseDistance,
                       MoveShortestDistance, Obstacles)
from character import AttackTheLiving, NeverAttack
from roster import Attack, Move, StateChange
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


class TestLivingState:

    def test_is_living(self):
        assert Living().living

    def test_is_not_undead(self):
        assert not Living().undead

    def test_movement_strategy_without_zombies(self):
        target_vectors = namedtuple('Targets', ['zombies'])([])
        assert (Living().movement_strategy(target_vectors) ==
                MoveShortestDistance())

    @given(st.lists(vectors(), min_size=1))
    def test_movement_strategy_with_zombies(self, zombie_vectors):
        target_vectors = namedtuple('Targets', ['zombies'])(zombie_vectors)
        assert (Living().movement_strategy(target_vectors) ==
                MaximiseShortestDistance(zombie_vectors))

    @given(environments())
    def test_never_attacks(self, environment):
        assert Living().attack_strategy.attack(environment) is None

    def test_no_next_state(self):
        assert Living().next_state is None


class TestDeadState:

    def test_is_not_living(self):
        assert not Dead().living

    def test_is_not_undead(self):
        assert not Dead().undead

    def test_cannot_move(self):
        assert list(Dead().movement_range) == [Vector.ZERO]

    def test_movement_strategy_exists(self):
        # There's only ever one move, so we don't care *what* this is
        strategy = Dead().movement_strategy(None)
        assert strategy.best_move([Vector.ZERO]) == Vector.ZERO

    @given(environments())
    def test_never_attacks(self, environment):
        assert Living().attack_strategy.attack(environment) is None

    def test_next_state_ages(self):
        assert Dead(age=2).next_state == Dead(age=3)

    def test_next_state_reanimates(self):
        assert Dead(age=20).next_state == Undead()


class TestUndeadState:

    def test_is_not_living(self):
        assert not Undead().living

    def test_is_not_undead(self):
        assert Undead().undead

    def test_movement_strategy_without_humans(self):
        target_vectors = namedtuple('Targets', ['humans'])([])
        assert (Undead().movement_strategy(target_vectors) ==
                MoveShortestDistance())

    @given(st.lists(vectors(), min_size=1))
    @example([Vector(1, 1), Vector(-1, -1)])
    @example([Vector(-1, -1), Vector(1, 1)])
    def test_movement_strategy_with_humans(self, human_vectors):
        # This test passes as a by-product of using the same `min` function,
        # which will pick the same one of n equidistant targets. Not ideal,
        # but good enough for now. There are explicit examples to catch this
        # if and when it breaks.
        closest_human = min(human_vectors, key=lambda v: v.distance)
        target_vectors = namedtuple('Targets', ['humans'])(human_vectors)
        assert (Undead().movement_strategy(target_vectors) ==
                MinimiseDistance(closest_human))

    def test_attacks_nearby_humans(self):
        victim = default_human()
        environment = [(Vector(1, 1), victim)]
        assert Undead().attack_strategy.attack(environment) == victim

    @given(environments(characters=humans))
    def test_does_not_attack_distant_humans(self, environment):
        assume(not any(pos.distance < 4 for pos, char in environment))
        assert Undead().attack_strategy.attack(environment) is None

    def test_no_next_state(self):
        assert Undead().next_state is None


class TestCharacter:

    def test_livingness(self):
        assert Character(state=Living()).living

    def test_undeath(self):
        assert Character(state=Undead()).undead

    def test_move_action(self):
        character = Character(state=Undead())
        environment = [(Vector(3, 3), default_human())]
        next_action = character.next_action(environment, BoundingBox.range(5))
        assert next_action == Move(character, Vector(1, 1))

    def test_attack_action(self):
        character = Character(state=Undead())
        target = default_human()
        next_action = character.next_action([(Vector(1, 1), target)],
                                            BoundingBox.range(5))
        assert next_action == Attack(character, target)

    def test_state_change_action(self):
        character = Character(state=Dead(age=20))
        next_action = character.next_action([], BoundingBox.range(5))

        assert next_action == StateChange(character, Undead())

    def test_state_change(self):
        character = Character(state=Dead())
        assert not character.undead
        assert character.with_state(Undead()).undead


class TestZombie:

    @pytest.fixture
    def zombie(self):
        return default_zombie()

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
        human = Character(state=Dead())
        assert human.move(environment) == Vector.ZERO

    @given(environments())
    def test_never_attacks(self, human, environment):
        assert human.attack(environment) is None
