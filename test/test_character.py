from hypothesis import assume, given
from hypothesis import strategies as st

from character import Human, Zombie
from space import BoundingBox, Vector

vectors = st.builds(Vector, st.integers(), st.integers())
humans = st.builds(Human)
zombies = st.builds(Zombie)
characters = st.one_of(humans, zombies)

# Bounding boxes that contain the vector (0, 0)
containing_boxes = st.builds(BoundingBox,
                             st.builds(Vector,
                                       st.integers(max_value=0),
                                       st.integers(max_value=0)),
                             st.builds(Vector,
                                       st.integers(min_value=1),
                                       st.integers(min_value=1)))


class TestZombie:

    @given(st.lists(st.tuples(vectors, characters)))
    def test_move_returns_a_vector(self, environment):
        zombie = Zombie()

        assert isinstance(zombie.move(environment), Vector)

    @given(st.lists(st.tuples(vectors, humans), min_size=1, max_size=1))
    def test_never_moves_away_from_human(self, environment):
        assume(environment[0][0] != Vector.ZERO)
        move = Zombie().move(environment)
        assert (environment[0][0] - move).distance <= environment[0][0].distance

    @given(st.lists(st.tuples(vectors, humans), min_size=1, max_size=1))
    def test_move_approaches_single_human(self, environment):
        assume(environment[0][0].distance > 1)
        move = Zombie().move(environment)
        assert (environment[0][0] - move).distance < environment[0][0].distance

    @given(st.lists(st.tuples(vectors, characters)))
    def test_does_not_move_onto_occupied_space(self, environment):
        move = Zombie().move(environment)
        assert move not in [e[0] for e in environment]

    @given(st.lists(st.tuples(vectors, characters)))
    def test_moves_up_to_one_space(self, environment):
        zombie = Zombie()
        move = zombie.move(environment)
        assert abs(move.dx) <= zombie.speed
        assert abs(move.dy) <= zombie.speed

    @given(st.lists(st.tuples(vectors, zombies)))
    def test_ignores_zombies(self, environment):
        assume(not any(e[0] == Vector.ZERO for e in environment))
        assert Zombie().move(environment) == Vector.ZERO

    @given(environment=st.lists(st.tuples(vectors, characters)),
           limits=containing_boxes)
    def test_respects_limits(self, environment, limits):
        assume(not any(e[0] == Vector.ZERO for e in environment))
        move = Zombie().move(environment, limits)
        assert move in limits

    def test_nothing_nearby(self):
        zombie = Zombie()
        assert zombie.move([]) == Vector.ZERO

    def test_nearest_human(self):
        zombie = Zombie()
        environment = [(Vector(3, -3), Human()),
                       (Vector(2, 2), Human()),
                       (Vector(-3, 3), Human())]

        assert zombie.move(environment) == Vector(1, 1)

    def test_close_human(self):
        """Check the zombie doesn't try to move onto or away from a human.

        In future versions, this test will be replaced by biting logic."""
        zombie = Zombie()
        environment = [(Vector(1, 1), Human())]

        expected_moves = [Vector(0, 0), Vector(0, 1), Vector(1, 0)]
        assert zombie.move(environment) in expected_moves

    def test_blocked_path(self):
        zombie = Zombie()
        environment = [(Vector(2, 2), Human()),
                       (Vector(1, 1), Zombie()),
                       (Vector(1, 0), Zombie()),
                       (Vector(0, 1), Zombie())]
        assert zombie.move(environment) == Vector.ZERO

    def test_all_paths_blocked(self):
        """Test that zombies stay still when surrounded by other zombies.

        This effectively functions as a last check that zombies always have
        their own position as a fall-back, and don't register as blocking their
        own non-movement.
        """
        zombie = Zombie()

        def env_contents(vector):
            return Zombie() if vector else zombie

        vectors = [Vector(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]
        distant_human = [(Vector(2, 2), Human())]
        zombies_all_around = [(v, env_contents(v)) for v in vectors]

        assert zombie.move(distant_human + zombies_all_around) == Vector.ZERO

    def test_alternate_path(self):
        zombie = Zombie()
        environment = [(Vector(2, 2), Human()),
                       (Vector(1, 1), Zombie()),
                       (Vector(1, 0), Zombie())]
        assert zombie.move(environment) == Vector(0, 1)


class TestHuman:

    @given(st.lists(st.tuples(vectors, characters)))
    def test_move_returns_vector(self, environment):
        assert isinstance(Human().move(environment), Vector)

    @given(st.lists(st.tuples(vectors, humans)))
    def test_ignores_humans(self, environment):
        assume(not any(e[0] == Vector.ZERO for e in environment))
        assert Human().move(environment) == Vector.ZERO

    @given(st.lists(st.tuples(vectors, characters)))
    def test_does_not_move_into_occupied_space(self, environment):
        assume(not any(e[0] == Vector.ZERO for e in environment))
        move = Human().move(environment)
        assert not any(e[0] == move for e in environment)

    @given(st.lists(st.tuples(vectors, zombies), min_size=1, max_size=1))
    def test_runs_away_from_zombie(self, environment):
        move = Human().move(environment)
        zombie_vector = environment[0][0]
        assert (zombie_vector - move).distance > zombie_vector.distance

    @given(st.lists(st.tuples(vectors, characters)))
    def test_moves_up_to_speed(self, environment):
        human = Human()
        move = human.move(environment)
        assert abs(move.dx) <= human.speed
        assert abs(move.dy) <= human.speed

    @given(environment=st.lists(st.tuples(vectors, characters)),
           limits=containing_boxes)
    def test_respects_limits(self, environment, limits):
        assume(not any(e[0] == Vector.ZERO for e in environment))
        move = Human().move(environment, limits)
        assert move in limits

    def test_does_not_move_in_empty_environment(self):
        human = Human()
        assert human.move([]) == Vector.ZERO

    def test_does_not_obstruct_self(self):
        human = Human()
        environment = [(Vector.ZERO, human)]
        assert human.move([]) == Vector.ZERO
