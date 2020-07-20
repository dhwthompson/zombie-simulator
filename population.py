import random
from typing import Callable, Generic, Iterable, Iterator, Optional, Tuple, TypeVar

CharacterType = TypeVar("CharacterType")
Factory = Callable[[], Optional[CharacterType]]


class Population(Generic[CharacterType]):
    def __init__(
        self,
        *probabilities: Tuple[float, Factory[CharacterType]],
        random_source: Callable[[], float] = random.random
    ):
        self._random = random_source

        self._cumulative_probabilities = []
        cumulative_prob = 0.0
        for (prob, factory) in probabilities:
            cumulative_prob += prob
            self._cumulative_probabilities.append((cumulative_prob, factory))

    def __iter__(self) -> Iterator[Optional[CharacterType]]:
        return self

    def _factory_for(self, random_value: float) -> Factory[CharacterType]:
        for (prob, factory) in self._cumulative_probabilities:
            if prob > random_value:
                return factory
        else:
            return lambda: None

    def __next__(self) -> Optional[CharacterType]:
        factory = self._factory_for(self._random())
        return factory()
