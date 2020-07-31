import attr
import math
from typing import ClassVar, Iterator


@attr.s(auto_attribs=True, frozen=True)
class Point:

    x: int
    y: int

    def __add__(self, vector: "Vector") -> "Point":
        return Point(self.x + vector.dx, self.y + vector.dy)

    def __sub__(self, point: "Point") -> "Vector":
        return Vector(self.x - point.x, self.y - point.y)


@attr.s(auto_attribs=True, frozen=True)
class Area:
    _lower: Point
    _upper: Point

    def __contains__(self, point: Point) -> bool:
        x_contains = self._lower.x <= point.x < self._upper.x
        y_contains = self._lower.y <= point.y < self._upper.y
        return x_contains and y_contains

    @property
    def width(self) -> int:
        return self._upper.x - self._lower.x

    @property
    def height(self) -> int:
        return self._upper.y - self._lower.y

    def distance_from(self, point: Point) -> float:
        x = min(point.x, self._upper.x)
        x = max(x, self._lower.x)
        y = min(point.y, self._upper.y)
        y = max(y, self._lower.y)
        best_point = Point(x, y)
        return (best_point - point).distance

    def from_origin(self, origin: Point) -> "BoundingBox":
        return BoundingBox(self._lower - origin, self._upper - origin)


@attr.s(auto_attribs=True, frozen=True)
class Vector:

    dx: int
    dy: int

    ZERO: ClassVar["Vector"]

    @property
    def distance(self) -> float:
        return math.sqrt(self.dx ** 2 + self.dy ** 2)

    def __bool__(self) -> bool:
        return bool(self.distance)

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.dx + other.dx, self.dy + other.dy)

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(self.dx - other.dx, self.dy - other.dy)


Vector.ZERO = Vector(0, 0)


@attr.s(auto_attribs=True, frozen=True)
class BoundingBox:
    _lower: Vector
    _upper: Vector

    @classmethod
    def range(cls, radius: int) -> "BoundingBox":
        if radius < 0:
            raise ValueError(f"Cannot have a negative range {radius}")
        return cls(Vector(-radius, -radius), Vector(radius + 1, radius + 1))

    def __contains__(self, vector: Vector) -> bool:
        dx_contains = self._lower.dx <= vector.dx < self._upper.dx
        dy_contains = self._lower.dy <= vector.dy < self._upper.dy
        return dx_contains and dy_contains

    def __iter__(self) -> Iterator[Vector]:
        for dy in range(self._lower.dy, self._upper.dy):
            for dx in range(self._lower.dx, self._upper.dx):
                yield Vector(dx, dy)

    def intersect(self, other: "BoundingBox") -> "BoundingBox":
        return BoundingBox(
            Vector(
                max(self._lower.dx, other._lower.dx),
                max(self._lower.dy, other._lower.dy),
            ),
            Vector(
                min(self._upper.dx, other._upper.dx),
                min(self._upper.dy, other._upper.dy),
            ),
        )
