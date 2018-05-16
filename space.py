from collections import namedtuple
import math


class Vector(namedtuple('Vector', ['dx', 'dy'])):

    @property
    def distance(self):
        return self.dx**2 + self.dy**2

    def __bool__(self):
        return bool(self.distance)

    def __add__(self, other):
        return Vector(self.dx + other.dx, self.dy + other.dy)

    def __sub__(self, other):
        return Vector(self.dx - other.dx, self.dy - other.dy)


Vector.INFINITE = Vector(math.inf, math.inf)
Vector.ZERO = Vector(0, 0)


class BoundingBox:
    def __init__(self, lower, upper):
        self._lower = lower
        self._upper = upper

    def __contains__(self, vector):
        dx_contains = self._lower.dx <= vector.dx < self._upper.dx
        dy_contains = self._lower.dy <= vector.dy < self._upper.dy
        return dx_contains and dy_contains


BoundingBox.UNLIMITED = BoundingBox(Vector(-math.inf, -math.inf),
                                    Vector.INFINITE)
