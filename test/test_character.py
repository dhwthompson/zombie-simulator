import pytest

from character import Human, Population, Zombie
from space import Vector


class TestZombie:

    def test_nothing_nearby(self):
        zombie = Zombie()
        assert zombie.move([]) == Vector.ZERO

    @pytest.mark.parametrize('offset,expected',
            [[(2, 0), (1, 0)],
             [(-2, 0), (-1, 0)],
             [(0, 2), (0, 1)],
             [(0, -2), (0, -1)],
             [(-2, 2), (-1, 1)],
             [(2, 2), (1, 1)],
             [(-2, -2), (-1, -1)],
             [(2, -2), (1, -1)]])
    def test_single_move(self, offset, expected):
        environment = [(Vector(*offset), Human())]
        zombie = Zombie()
        assert zombie.move(environment) == Vector(*expected)

    def test_nearest_human(self):
        zombie = Zombie()
        environment = [(Vector(3, -3), Human()),
                       (Vector(2, 2), Human()),
                       (Vector(-3, 3), Human())]

        assert zombie.move(environment) == Vector(1, 1)

    def test_nearby_zombie(self):
        zombie = Zombie()
        environment = [(Vector(2, 2), Zombie())]
        assert zombie.move(environment) == Vector.ZERO

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

    def test_map_limits(self):
        zombie = Zombie()
        environment = [(Vector(0, 1), Zombie()),
                       (Vector(0, 2), Human())]
        limits = [Vector(dx, dy) for (dx, dy) in
                  [(0, 0), (0, 1), (0, 2)]]
        assert zombie.move(environment, limits) == Vector.ZERO


class TestHuman:
    def test_immobile(self):
        human = Human()
        assert human.move([]) == Vector.ZERO


class TestPopulation:

    def test_empty_population(self):
        population = Population(0, 0)
        generated = [p for p, _ in zip(population, range(100))]

        assert all(g is None for g in generated)

    def test_empty_zombie_population(self):
        population = Population(0, 1)
        generated = [p for p, _ in zip(population, range(100))]

        assert all(g is None for g in generated)

    def test_human_population(self):
        population = Population(1, 0)
        generated = [p for p, _ in zip(population, range(100))]

        assert all(isinstance(g, Human) for g in generated)

    def test_zombie_population(self):
        population = Population(1, 1)

        generated = [p for p, _ in zip(population, range(100))]

        assert all(isinstance(g, Zombie) for g in generated)
