from functools import partial
from random import random

from space import BoundingBox, Vector


class Character:

    def move(self, environment, limits=BoundingBox.UNLIMITED):
        """Choose where to move next.

        Arguments:
            environment: the character's current environment. This is currently
                passed in as an iterable of (Vector, Character) pairs, which
                isn't entirely ideal, but works well enough for the moment.
            limits: any limits on the character's movement provided by the
                edges of the world. This can be anything that reponds to the
                `in` operator.

        Return a Vector object representing this character's intended move. If
        the character does not intend to (or cannot) move, return a zero
        vector.
        """
        target_vector = self._target_vector(environment)
        moves = self._available_moves(limits, environment)
        move_rank = partial(self._move_rank, target_vector)

        return sorted(moves, key=move_rank)[0]

    def _available_moves(self, limits, environment):
        moves = [m for m in self._movement_range
                 if m in limits
                 and m not in self._obstacles(environment)]
        return moves

    @property
    def _movement_range(self):
        coord_range = range(-self.speed, self.speed + 1)
        return [Vector(dx, dy) for dx in coord_range for dy in coord_range]

    def _obstacles(self, environment):
        return [t[0] for t in environment if t[1] != self]

    def _target_vector(self, environment):
        return min(self._targets(environment),
                   key=lambda v: v.distance,
                   default=Vector.INFINITE)

    def _targets(self, environment):
        raise NotImplementedError

    def _move_rank(self, target_vector, move):
        raise NotImplementedError


class Human(Character):

    living = True
    speed = 0

    def _targets(self, environment):
        return []

    def _move_rank(self, target_vector, move):
        return None


class Zombie(Character):

    living = False
    speed = 1

    def _targets(self, environment):
        return [t[0] for t in environment if t[1].living]

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
