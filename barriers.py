import random
from typing import Any, ClassVar, Generator, Iterable, Set

import attr

from space import Area, Point


@attr.s(auto_attribs=True, frozen=True)
class Barriers:

    areas: Set[Area]
    NONE: ClassVar["Barriers"]

    @property
    def positions(self) -> Generator[Point, None, None]:
        for area in self.areas:
            for point in area:
                yield point

    def occupied(self, point: Point) -> bool:
        return any(point in area for area in self.areas)

    def occupied_points_in(self, area: Area) -> Set[Point]:
        barrier_points = set()
        for barrier in self.areas:
            barrier_points |= {point for point in barrier.intersect(area)}
        return barrier_points


Barriers.NONE = Barriers(set())


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

    return Barriers(barrier_areas)
