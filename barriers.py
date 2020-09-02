from typing import ClassVar, Generator, Set

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
