import random
from typing import Any, ClassVar, FrozenSet, Generator, Iterable, Set, Tuple

import attr

from space import Area, Point


@attr.s(auto_attribs=True, frozen=True)
class BarrierPoint:
    """BarrierPoint is a data structure representing a single unit of a barrier.

    It has a Boolean attribute for each of the four directions. In the co-ordinate
    system of the world, "left" and "up" are assumed to correspond to lower x and y
    co-ordinates, respectively.
    """

    above: bool = False
    below: bool = False
    left: bool = False
    right: bool = False


@attr.s(auto_attribs=True, frozen=True)
class Barriers:

    areas: FrozenSet[Area]

    NONE: ClassVar["Barriers"]

    @classmethod
    def for_areas(cls, areas: Iterable[Area]) -> "Barriers":
        return Barriers(areas=frozenset(areas))

    @property
    def positions(self) -> Generator[Tuple[Point, BarrierPoint], None, None]:
        for area in self.areas:
            for point in area:
                bp = BarrierPoint(
                    above=self.occupied(Point(point.x, point.y - 1)),
                    below=self.occupied(Point(point.x, point.y + 1)),
                    left=self.occupied(Point(point.x - 1, point.y)),
                    right=self.occupied(Point(point.x + 1, point.y)),
                )
                yield (point, bp)

    def __bool__(self) -> bool:
        return bool(self.areas)

    def occupied(self, point: Point) -> bool:
        return any(point in area for area in self.areas)

    def occupied_points_in(self, area: Area) -> Set[Point]:
        barrier_points = set()
        for barrier in self.areas:
            barrier_points |= {point for point in barrier.intersect(area)}
        return barrier_points


Barriers.NONE = Barriers.for_areas([])


def random_barriers(counter: Iterable[Any], area: Area) -> Barriers:
    def x_coord() -> int:
        return random.randint(area._lower.x, area._upper.x - 1)

    def y_coord() -> int:
        return random.randint(area._lower.y, area._upper.y - 1)

    barrier_areas = set()
    for _ in counter:
        if random.choice([True, False]):
            # Vertical barrier
            x1 = x_coord()
            x2 = x1 + 1
            y1, y2 = sorted([y_coord(), y_coord()])
        else:
            # Horizontal barrier
            x1, x2 = sorted([x_coord(), x_coord()])
            y1 = y_coord()
            y2 = y1 + 1

        barrier_areas.add(Area(Point(x1, y1), Point(x2, y2)))

    return Barriers.for_areas(barrier_areas)
