import attr
import math
from typing import ClassVar


@attr.s(auto_attribs=True, frozen=True)
class Point:

    x: int
    y: int

    def __add__(self, vector):
        return Point(self.x + vector.dx, self.y + vector.dy)

    def __sub__(self, point):
        return Vector(self.x - point.x, self.y - point.y)


@attr.s(auto_attribs=True, frozen=True)
class Area:
    _lower: Point
    _upper: Point

    def __contains__(self, point):
        x_contains = self._lower.x <= point.x < self._upper.x
        y_contains = self._lower.y <= point.y < self._upper.y
        return x_contains and y_contains

    @property
    def width(self):
        return self._upper.x - self._lower.x

    @property
    def height(self):
        return self._upper.y - self._lower.y

    def distance_from(self, point):
        x = min(point.x, self._upper.x)
        x = max(x, self._lower.x)
        y = min(point.y, self._upper.y)
        y = max(y, self._lower.y)
        best_point = Point(x, y)
        return (best_point - point).distance

    def from_origin(self, origin):
        return BoundingBox(self._lower - origin, self._upper - origin)


@attr.s(frozen=True)
class Vector:

    dx: int = attr.ib()
    dy: int = attr.ib()

    ZERO: ClassVar["Vector"]

    @property
    def distance(self):
        return math.sqrt(self.dx ** 2 + self.dy ** 2)

    def __bool__(self):
        return bool(self.distance)

    def __add__(self, other):
        return Vector(self.dx + other.dx, self.dy + other.dy)

    def __sub__(self, other):
        return Vector(self.dx - other.dx, self.dy - other.dy)


Vector.ZERO = Vector(0, 0)


class BoundingBox:
    def __init__(self, lower: Vector, upper: Vector):
        self._lower = lower
        self._upper = upper

    @classmethod
    def range(cls, radius):
        if radius < 0:
            raise ValueError(f"Cannot have a negative range {radius}")
        return cls(Vector(-radius, -radius), Vector(radius + 1, radius + 1))

    def __contains__(self, vector):
        dx_contains = self._lower.dx <= vector.dx < self._upper.dx
        dy_contains = self._lower.dy <= vector.dy < self._upper.dy
        return dx_contains and dy_contains

    def __iter__(self):
        for dy in range(self._lower.dy, self._upper.dy):
            for dx in range(self._lower.dx, self._upper.dx):
                yield Vector(dx, dy)

    def __repr__(self):
        return f"BoundingBox({self._lower}, {self._upper})"


class UnlimitedBoundingBox:
    def __contains__(self, vector):
        return True
