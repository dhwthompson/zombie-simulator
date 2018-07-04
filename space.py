from collections import namedtuple
import math


class Point(namedtuple('Point', ['x', 'y'])):

    def __add__(self, vector):
        return Point(self.x + vector.dx, self.y + vector.dy)

    def __sub__(self, point):
        return Vector(self.x - point[0], self.y - point[1])


class Area:
    def __init__(self, lower, upper):
        self._lower = lower
        self._upper = upper

    def __contains__(self, point):
        x_contains = self._lower.x <= point.x < self._upper.x
        y_contains = self._lower.y <= point.y < self._upper.y
        return x_contains and y_contains

    def __repr__(self):
        return 'Area({}, {})'.format(self._lower, self._upper)

    def from_origin(self, origin):
        return BoundingBox(self._lower - origin, self._upper - origin)


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


Vector.ZERO = Vector(0, 0)


class BoundingBox:
    def __init__(self, lower, upper):
        self._lower = lower
        self._upper = upper

    def __contains__(self, vector):
        dx_contains = self._lower.dx <= vector.dx < self._upper.dx
        dy_contains = self._lower.dy <= vector.dy < self._upper.dy
        return dx_contains and dy_contains

    def __repr__(self):
        return 'BoundingBox({}, {})'.format(self._lower, self._upper)


class UnlimitedBoundingBox:

    def __contains__(self, vector):
        return True
