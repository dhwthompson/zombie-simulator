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
