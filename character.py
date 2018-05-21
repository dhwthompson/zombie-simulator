from functools import partial
from random import random

from space import BoundingBox, Vector


class Human:

    living = True

    def move(self, environment, limits=None):
        return Vector.ZERO


class Zombie:

    living = False

    @property
    def _movement_range(self):
        return [Vector(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]

    def move(self, environment, limits=BoundingBox.UNLIMITED):
        target_vector = self._target_vector(environment)

        if target_vector.distance <= 2:
            return Vector.ZERO

        moves = self._available_moves(limits, environment)

        move_rank = partial(self._move_rank, target_vector)

        return sorted(moves, key=move_rank)[0]

    def _available_moves(self, limits, environment):
        moves = [m for m in self._movement_range
                 if m in limits
                 and m not in self._obstacles(environment)]
        return moves

    def _obstacles(self, environment):
        return [t[0] for t in environment if t[1] != self]

    def _targets(self, environment):
        return [t[0] for t in environment if t[1].living]

    def _target_vector(self, environment):
        return min(self._targets(environment),
                   key=lambda v: v.distance,
                   default=Vector.INFINITE)

    def _move_rank(self, target_vector, move):
        distance_after_move = (target_vector - move).distance
        return (distance_after_move, move.distance)

class Population:

    def __init__(self, density, zombie_chance):
        self._density = density
        self._zombie_chance = zombie_chance

    def __iter__(self):
        return self

    def __next__(self):
        if random() <= self._density:
            return Zombie() if random() <= self._zombie_chance else Human()
        return None
