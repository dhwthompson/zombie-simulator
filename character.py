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
        target_vectors = [t[0] for t in environment if t[1].living]
        obstacles = [t[0] for t in environment if t[1] != self]

        best_vector = min(target_vectors,
                          key=lambda v: v.distance,
                          default=Vector.INFINITE)

        if best_vector.distance <= 2:
            return Vector.ZERO

        moves = [m for m in self._movement_range
                 if m in limits
                 and m not in obstacles]

        def move_rank(move):
            distance_after_move = (best_vector - move).distance
            return (distance_after_move, move.distance)

        return sorted(moves, key=move_rank)[0]


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
