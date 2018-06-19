import random


class Population:

    def __init__(self, *probabilities, random_source=random.random):
        self._random = random_source

        self._cumulative_probabilities = []
        cumulative_prob = 0.0
        for (prob, factory) in probabilities:
            cumulative_prob += prob
            self._cumulative_probabilities.append((cumulative_prob, factory))

    def __iter__(self):
        return self

    def _factory_for(self, random_value):
        for (prob, factory) in self._cumulative_probabilities:
            if prob > random_value:
                return factory
        else:
            return lambda: None

    def __next__(self):
        factory = self._factory_for(self._random())
        return factory()
