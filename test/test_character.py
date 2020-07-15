from collections import namedtuple

from hypothesis import assume, example, given, note
from hypothesis import strategies as st

import pytest

from .strategies import list_and_element
from character import Character, default_human, default_zombie
from character import Dead, Living, Undead
from character import Obstacles, TargetVectors
from space import BoundingBox, Vector


class FakeViewpoint:
    def __init__(self, positions):
        self._positions = positions

    def nearest(self, **attributes):
        matches = [
            pos
            for pos, char in self._positions
            if all(getattr(char, a) == v for a, v in attributes.items())
        ]
        if matches:
            return min(matches, key=lambda pos: pos.distance)
        else:
            return None

    def character_at(self, position):
        for point, character in self._positions:
            if point == position:
                return character
        else:
            return None

    def from_offset(self, offset):
        return FakeViewpoint((v - offset, char) for v, char in self._positions)

    def __iter__(self):
        return iter(self._positions)


def vectors(max_offset=None):
    if max_offset is not None:
        coordinates = st.integers(min_value=-max_offset, max_value=max_offset)
    else:
        coordinates = st.integers()
    return st.builds(Vector, dx=coordinates, dy=coordinates)


humans = st.builds(default_human)
zombies = st.builds(default_zombie)
characters = st.one_of(humans, zombies)

containing_boxes = st.builds(
    BoundingBox,
    lower=st.builds(Vector, dx=st.integers(max_value=0), dy=st.integers(max_value=0)),
    upper=st.builds(Vector, dx=st.integers(min_value=1), dy=st.integers(min_value=1)),
)


def environments(characters=characters, min_size=0, max_size=None):
    all_envs = st.lists(
        st.tuples(vectors(1000), characters), min_size=min_size, max_size=max_size
    )
    return all_envs.filter(lambda e: not any(pos == Vector.ZERO for pos, _ in e))


class TestTargetVectors:
    @given(environments(characters=humans, min_size=1).flatmap(list_and_element))
    def test_nearest_human(self, env_and_entry):
        environment, (position, character) = env_and_entry

        nearest_human = TargetVectors(FakeViewpoint(environment)).nearest_human
        assert nearest_human.distance <= position.distance

    @given(environments(characters=zombies))
    def test_no_humans(self, environment):
        assert TargetVectors(FakeViewpoint(environment)).nearest_human is None


class TestObstacles:
    @given(environments())
    @example([])
    @example([(Vector.ZERO, object())])
    def test_never_includes_zero_vector(self, environment):
        assert Vector.ZERO not in Obstacles(FakeViewpoint(environment))

    @given(environments(min_size=1).flatmap(list_and_element))
    def test_includes_entry(self, env_and_entry):
        environment, (position, _) = env_and_entry
        assume(position != Vector.ZERO)

        assert position in Obstacles(FakeViewpoint(environment))


class TestLivingState:
    def test_is_living(self):
        assert Living().living

    def test_is_not_undead(self):
        assert not Living().undead

    @given(moves=st.lists(vectors(), min_size=1))
    def test_movement_without_zombies(self, moves):
        target_vectors = TargetVectors(FakeViewpoint([]))
        assert Living().best_move(target_vectors, moves) == min(
            moves, key=lambda v: v.distance
        )

    @given(
        zombie_vectors=st.lists(vectors(), min_size=1),
        moves=st.lists(vectors(), min_size=1),
    )
    def test_movement_with_zombies(self, zombie_vectors, moves):
        target_vectors = TargetVectors(
            FakeViewpoint([(v, default_zombie()) for v in zombie_vectors])
        )
        best_move = Living().best_move(target_vectors, moves)

        def distance_after_move(move):
            return min((zombie - move).distance for zombie in zombie_vectors)

        best_move_distance = distance_after_move(best_move)
        note(f"Best distance, after {best_move}: {best_move_distance}")

        for move in moves:
            move_distance = distance_after_move(move)
            note(f"Distance after {move}: {move_distance}")

        assert all(best_move_distance >= distance_after_move(move) for move in moves)

    def test_chooses_shortest_best_move(self):
        target_vectors = TargetVectors(
            FakeViewpoint([(Vector(1, 2), default_zombie())])
        )
        moves = [Vector.ZERO, Vector(1, 0), Vector(2, 0)]

        assert Living().best_move(target_vectors, moves) == Vector.ZERO
        # To make sure we're not lucking out based on the order
        assert Living().best_move(target_vectors, list(reversed(moves))) == Vector.ZERO

    @given(environments())
    def test_never_attacks(self, environment):
        assert Living().attack(environment) is None

    def test_no_next_state(self):
        assert Living().next_state is None


class TestDeadState:
    def test_is_not_living(self):
        assert not Dead().living

    def test_is_not_undead(self):
        assert not Dead().undead

    def test_cannot_move(self):
        assert list(Dead().movement_range) == [Vector.ZERO]

    @given(environments(), st.lists(vectors(), min_size=1))
    def test_never_moves(self, environment, moves):
        target_vectors = TargetVectors(environment)

        if Vector.ZERO not in moves:
            moves = moves + [Vector.ZERO]

        assert Dead().best_move(target_vectors, moves) == Vector.ZERO

    @given(environments())
    def test_never_attacks(self, environment):
        assert Dead().attack(environment) is None

    def test_next_state_ages(self):
        assert Dead(age=2).next_state == Dead(age=3)

    def test_next_state_reanimates(self):
        assert Dead(age=20).next_state == Undead()


class TestUndeadState:
    def test_is_not_living(self):
        assert not Undead().living

    def test_is_not_undead(self):
        assert Undead().undead

    @given(moves=st.lists(vectors(), min_size=1))
    def test_movement_without_humans(self, moves):
        target_vectors = namedtuple("Targets", ["nearest_human"])(None)
        assert Undead().best_move(target_vectors, moves) == min(
            moves, key=lambda v: v.distance
        )

    @given(human=vectors(), moves=st.lists(vectors(), min_size=1))
    def test_gets_as_close_to_target_as_possible(self, human, moves):
        target_vectors = namedtuple("Targets", ["nearest_human"])(human)
        best_move = Undead().best_move(target_vectors, moves)

        distance_after_move = (human - best_move).distance
        assert all(distance_after_move <= (human - move).distance for move in moves)

    @given(vectors(max_offset=1))
    def test_attacks_nearby_humans(self, vector):
        target_vectors = namedtuple("Targets", ["nearest_human"])(vector)
        assert Undead().attack(target_vectors) == vector

    @given(vectors().filter(lambda v: v.distance >= 2))
    def test_does_not_attack_distant_humans(self, vector):
        target_vectors = namedtuple("Targets", ["nearest_human"])(vector)
        assert Undead().attack(target_vectors) is None

    def test_no_next_state(self):
        assert Undead().next_state is None


Move = namedtuple("Move", ["vector"])
Attack = namedtuple("Attack", ["vector"])
StateChange = namedtuple("StateChange", ["new_state"])


class FakeActions:

    move = Move
    attack = Attack
    change_state = StateChange


class TestCharacter:
    def test_livingness(self):
        assert Character(state=Living()).living

    def test_undeath(self):
        assert Character(state=Undead()).undead

    def test_move_action(self):
        character = Character(state=Undead())
        environment = FakeViewpoint([(Vector(3, 3), default_human())])
        next_action = character.next_action(
            environment, BoundingBox.range(5), FakeActions
        )
        assert next_action == Move(Vector(1, 1))

    def test_attack_action(self):
        character = Character(state=Undead())
        target = default_human()
        next_action = character.next_action(
            FakeViewpoint([(Vector(1, 1), target)]), BoundingBox.range(5), FakeActions
        )
        assert next_action == Attack(Vector(1, 1))

    def test_state_change_action(self):
        character = Character(state=Dead(age=20))
        next_action = character.next_action([], BoundingBox.range(5), FakeActions)

        assert next_action == StateChange(Undead())

    def test_state_change(self):
        character = Character(state=Dead())
        assert not character.undead
        assert character.with_state(Undead()).undead


class TestZombie:
    @pytest.fixture(scope="session")
    def zombie(self):
        return default_zombie()

    @given(environments().map(FakeViewpoint))
    def test_move_returns_a_vector(self, zombie, environment):
        assert isinstance(zombie.move(environment), Vector)

    @given(environments(characters=humans, min_size=1, max_size=1))
    def test_never_moves_away_from_human(self, zombie, environment):
        viewpoint = FakeViewpoint(environment)
        move = zombie.move(viewpoint)
        assert (environment[0][0] - move).distance <= environment[0][0].distance

    @given(environments(characters=humans, min_size=1, max_size=1))
    def test_move_approaches_single_human(self, zombie, environment):
        assume(environment[0][0].distance > 1)
        move = zombie.move(FakeViewpoint(environment))
        assert (environment[0][0] - move).distance < environment[0][0].distance

    @given(environments())
    def test_does_not_move_onto_occupied_space(self, zombie, environment):
        move = zombie.move(FakeViewpoint(environment))
        assert move not in [e[0] for e in environment]

    @given(environments().map(FakeViewpoint))
    def test_moves_up_to_one_space(self, zombie, environment):
        move = zombie.move(environment)
        assert abs(move.dx) <= 1
        assert abs(move.dy) <= 1

    @given(environments(characters=zombies).map(FakeViewpoint))
    def test_ignores_zombies(self, zombie, environment):
        assert zombie.move(environment) == Vector.ZERO

    @given(environment=environments().map(FakeViewpoint), limits=containing_boxes)
    def test_respects_limits(self, zombie, environment, limits):
        move = zombie.move(environment, limits)
        assert move in limits

    def test_nothing_nearby(self, zombie):
        assert zombie.move(FakeViewpoint([])) == Vector.ZERO

    def test_nearest_human(self, zombie):
        environment = [
            (Vector(3, -3), default_human()),
            (Vector(2, 2), default_human()),
            (Vector(-3, 3), default_human()),
        ]

        assert zombie.move(FakeViewpoint(environment)) == Vector(1, 1)

    def test_close_human(self, zombie):
        """Check the zombie doesn't try to move onto or away from a human.

        In future versions, this test will be replaced by biting logic."""
        environment = [(Vector(1, 1), default_human())]

        expected_moves = [Vector(0, 0), Vector(0, 1), Vector(1, 0)]
        assert zombie.move(FakeViewpoint(environment)) in expected_moves

    def test_blocked_path(self, zombie):
        environment = [
            (Vector(2, 2), default_human()),
            (Vector(1, 1), default_zombie()),
            (Vector(1, 0), default_zombie()),
            (Vector(0, 1), default_zombie()),
        ]
        assert zombie.move(FakeViewpoint(environment)) == Vector.ZERO

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

        viewpoint = FakeViewpoint(distant_human + zombies_all_around)

        assert zombie.move(viewpoint) == Vector.ZERO

    def test_alternate_path(self, zombie):
        environment = [
            (Vector(2, 2), default_human()),
            (Vector(1, 1), default_zombie()),
            (Vector(1, 0), default_zombie()),
        ]
        assert zombie.move(FakeViewpoint(environment)) == Vector(0, 1)

    @given(st.lists(st.tuples(vectors(max_offset=1), humans), min_size=1, max_size=1))
    def test_attack(self, zombie, environment):
        vector = environment[0][0]

        assert zombie.attack(FakeViewpoint(environment)) == vector

    @given(environments(characters=humans))
    @example([(Vector(2, 0), default_human())])
    def test_targets_out_of_range(self, zombie, environment):
        biting_range = BoundingBox(Vector(-1, -1), Vector(2, 2))
        assume(all(e[0] not in biting_range for e in environment))

        assert zombie.attack(FakeViewpoint(environment)) is None


class TestHuman:
    @pytest.fixture(scope="session")
    def human(self):
        return default_human()

    def test_living(self, human):
        assert human.living

    def test_not_undead(self, human):
        assert not human.undead

    @given(environments().map(FakeViewpoint))
    def test_move_returns_vector(self, human, environment):
        assert isinstance(human.move(environment), Vector)

    @given(environments(characters=humans).map(FakeViewpoint))
    def test_ignores_humans(self, human, environment):
        assert human.move(environment) == Vector.ZERO

    @given(environments())
    def test_does_not_move_into_occupied_space(self, human, environment):
        move = human.move(FakeViewpoint(environment))
        assert not any(e[0] == move for e in environment)

    @given(environments(characters=zombies, min_size=1, max_size=1))
    def test_runs_away_from_zombie(self, human, environment):
        move = human.move(FakeViewpoint(environment))
        zombie_vector = environment[0][0]
        assert (zombie_vector - move).distance > zombie_vector.distance

    @given(environments(characters=zombies, min_size=1))
    def test_runs_away_from_zombies(self, human, environment):
        move = human.move(FakeViewpoint(environment))
        min_distance_before = min(e[0].distance for e in environment)
        min_distance_after = min((e[0] - move).distance for e in environment)
        assert min_distance_after >= min_distance_before

    @given(environments().map(FakeViewpoint))
    def test_moves_up_to_two_spaces(self, human, environment):
        move = human.move(environment)
        assert abs(move.dx) <= 2
        assert abs(move.dy) <= 2

    @given(environment=environments().map(FakeViewpoint), limits=containing_boxes)
    def test_respects_limits(self, human, environment, limits):
        move = human.move(environment, limits)
        assert move in limits

    def test_does_not_move_in_empty_environment(self, human):
        assert human.move(FakeViewpoint([])) == Vector.ZERO

    def test_does_not_obstruct_self(self, human):
        environment = FakeViewpoint([(Vector.ZERO, human)])
        assert human.move(environment) == Vector.ZERO

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
