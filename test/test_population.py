from collections import Counter

from population import Population


def human():
    return "human"


def zombie():
    return "zombie"


class TestPopulation:

    def test_empty_population(self):
        population = Population()
        generated = [next(population) for _ in range(100)]

        assert all(g is None for g in generated)

    def test_human_population(self):
        population = Population((1.0, human))
        generated = [next(population) for _ in range(100)]

        assert all(g == "human" for g in generated)

    def test_zombie_population(self):
        population = Population((1.0, zombie))

        generated = [next(population) for _ in range(100)]

        assert all(g == "zombie" for g in generated)

    def test_random_source(self):
        uniform = [0.0, 0.2, 0.4, 0.6, 0.8]
        population = Population((0.4, human), (0.4, zombie),
                                random_source=uniform.pop)

        generated = [next(population) for _ in range(5)]
        population_counts = Counter(generated)

        assert population_counts == Counter({"human": 2, "zombie": 2, None: 1})
