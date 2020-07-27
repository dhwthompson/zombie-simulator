import attr
from enum import Enum
from itertools import chain
import math
from typing import Callable, Dict, Generic, Iterable, Optional, TypeVar, Tuple, Union

from space import Area, Point

ValueType = TypeVar("ValueType")


ANYTHING = lambda v: True


@attr.s(auto_attribs=True, frozen=True)
class Match(Generic[ValueType]):
    point: Point
    value: ValueType


class SpaceTree(Generic[ValueType]):
    """A dict-like structure that maps 2-dimensional positions to values.

    The best way to build one of these trees is with the `build` class method:

        >>> tree = SpaceTree.build(
        ...     Area(Point(0, 0), Point(10, 10)),
        ...     {Point(2, 2): "a thing", Point(5, 5): "another thing"}
        ... )

    This data structure is roughly based on a `k-d tree`_, with a couple of fudges along
    the way. For instance, it currently bisects nodes straight down the middle along
    their longest axis, rather than finding a median point. This isn't likely to be
    optimal, especially given that characters are likely to "clump" together, but it'll
    do for the moment.

    .. _k-d tree: https://en.wikipedia.org/wiki/K-d_tree

    """

    @classmethod
    def build(
        self, area: Area, positions: Optional[Dict[Point, ValueType]] = None
    ) -> "SpaceTree[ValueType]":
        """Build and return a new SpaceTree with the given area and entries."""
        tree: "SpaceTree[ValueType]" = SpaceTree(area, Leaf(area))
        if positions:
            for point, value in positions.items():
                tree = tree.set(point, value)

        return tree

    def __init__(self, area: Area, root: "Node[ValueType]"):
        self._area = area
        self._root = root

    def __repr__(self) -> str:
        return f"SpaceTree({self._area}, {self._root})"

    def __contains__(self, point: Point) -> bool:
        try:
            self._root[point]
            return True
        except KeyError:
            return False

    def __getitem__(self, point: Point) -> ValueType:
        return self._root[point]

    def __len__(self) -> int:
        return len(self._root)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpaceTree):
            return False
        return self._area == other._area and self._root == other._root

    def items(self) -> Iterable[Tuple[Point, ValueType]]:
        return self._root.items()

    def get(self, point: Point) -> Optional[ValueType]:
        try:
            return self._root[point]
        except KeyError:
            return None

    def set(self, point: Point, value: ValueType) -> "SpaceTree[ValueType]":
        """Return a new SpaceTree, with a value added at the given point.

        If there is already a value at the given point, replace it.
        """
        return SpaceTree(self._area, self._root.set(point, value))

    def unset(self, point: Point) -> "SpaceTree[ValueType]":
        """Return a new SpaceTree, with the given point unset.

        If there is no value at the given point, raise a KeyError.
        """
        return SpaceTree(self._area, self._root.unset(point))

    def nearest_to(
        self, origin: Point, predicate: Optional[Callable[[ValueType], bool]] = None
    ) -> Optional[Match[ValueType]]:
        """Return the nearest entry to a given point, not including the point itself.

        Optionally, accept a predicate to return the nearest entry for which calling the
        predicate on its value returns True.
        """
        return self._root.nearest_to(origin, predicate)


class Leaf(Generic[ValueType]):
    """Helper class for SpaceTree, representing a node that hasn't been split."""

    LEAF_MAX = 10

    def __init__(self, area: Area, positions: Optional[Dict[Point, ValueType]] = None):
        self._area = area
        self._positions = positions or {}

    def __getitem__(self, point: Point) -> ValueType:
        if point not in self._area:
            raise ValueError(f"{point} not in tree area")
        return self._positions[point]

    def __len__(self) -> int:
        return len(self._positions)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Leaf):
            return False

        return self._area == other._area and self._positions == other._positions

    def items(self) -> Iterable[Tuple[Point, ValueType]]:
        return self._positions.items()

    def set(self, point: Point, value: ValueType) -> "Node[ValueType]":
        if point not in self._positions and len(self._positions) >= self.LEAF_MAX:
            result: SplitNode[ValueType]

            if self._area.width >= self._area.height:
                # Split horizontally
                midpoint_x = (self._area._lower.x + self._area._upper.x) // 2
                lower_func = horizontal_midpoint(midpoint_x)

                lower_child = Leaf(
                    Area(self._area._lower, Point(midpoint_x, self._area._upper.y)),
                    {p: v for p, v in self.items() if lower_func(p)},
                )

                upper_child = Leaf(
                    Area(Point(midpoint_x, self._area._lower.y), self._area._upper),
                    {p: v for p, v in self.items() if not lower_func(p)},
                )

                result = SplitNode(self._area, lower_func, lower_child, upper_child)
            else:
                # Split vertically
                midpoint_y = (self._area._lower.y + self._area._upper.y) // 2
                lower_func = vertical_midpoint(midpoint_y)

                lower_child = Leaf(
                    Area(self._area._lower, Point(self._area._upper.x, midpoint_y)),
                    {p: v for p, v in self.items() if lower_func(p)},
                )

                upper_child = Leaf(
                    Area(Point(self._area._lower.x, midpoint_y), self._area._upper),
                    {p: v for p, v in self.items() if not lower_func(p)},
                )

                result = SplitNode(self._area, lower_func, lower_child, upper_child)

            return result.set(point, value)
        else:
            new_positions = self._positions.copy()
            new_positions[point] = value
            return Leaf(self._area, new_positions)

    def unset(self, point: Point) -> "Leaf[ValueType]":
        new_positions = self._positions.copy()
        del new_positions[point]
        return Leaf(self._area, new_positions)

    def nearest_to(
        self,
        origin: Point,
        predicate: Optional[Callable[[ValueType], bool]] = None,
        threshold: float = math.inf,
    ) -> Optional[Match[ValueType]]:

        if self._area.distance_from(origin) > threshold:
            return None

        if predicate is None:
            predicate = ANYTHING

        best_match = None
        for pos, value in self._positions.items():
            if pos == origin or not predicate(value):
                continue
            distance = (pos - origin).distance
            if distance < threshold:
                threshold = distance
                best_match = Match(pos, value)
        return best_match


def horizontal_midpoint(x: int) -> Callable[[Point], bool]:
    return lambda p: p.x < x


def vertical_midpoint(y: int) -> Callable[[Point], bool]:
    return lambda p: p.y < y


class SplitNode(Generic[ValueType]):
    """Helper class for SpaceTree, representing a node that has been split into two."""

    def __init__(
        self,
        area: Area,
        lower_func: Callable[[Point], bool],
        lower_child: "Node[ValueType]",
        upper_child: "Node[ValueType]",
    ):
        self._area = area
        self._lower_func = lower_func
        self._lower_child = lower_child
        self._upper_child = upper_child

    def __getitem__(self, point: Point) -> ValueType:
        if self._lower_func(point):
            return self._lower_child[point]
        else:
            return self._upper_child[point]

    def __len__(self) -> int:
        return len(self._lower_child) + len(self._upper_child)

    def __hash__(self) -> int:
        return hash((self._lower_child, self._upper_child))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SplitNode):
            return False

        return (
            self._lower_child == other._lower_child
            and self._upper_child == other._upper_child
        )

    def items(self) -> Iterable[Tuple[Point, ValueType]]:
        return chain(self._lower_child.items(), self._upper_child.items())

    def set(self, point: Point, value: ValueType) -> "SplitNode[ValueType]":
        if self._lower_func(point):
            return SplitNode(
                self._area,
                self._lower_func,
                self._lower_child.set(point, value),
                self._upper_child,
            )
        else:
            return SplitNode(
                self._area,
                self._lower_func,
                self._lower_child,
                self._upper_child.set(point, value),
            )

    def unset(self, point: Point) -> "Node[ValueType]":
        if self._lower_func(point):
            lower_child = self._lower_child.unset(point)
            upper_child = self._upper_child
        else:
            lower_child = self._lower_child
            upper_child = self._upper_child.unset(point)

        if len(lower_child) + len(upper_child) <= Leaf.LEAF_MAX:
            positions = {p: v for p, v in lower_child.items()}
            for p, v in upper_child.items():
                positions[p] = v
            return Leaf(self._area, positions)
        else:
            return SplitNode(self._area, self._lower_func, lower_child, upper_child)

    def nearest_to(
        self,
        origin: Point,
        predicate: Optional[Callable[[ValueType], bool]] = None,
        threshold: float = math.inf,
    ) -> Optional[Match[ValueType]]:

        if self._area.distance_from(origin) > threshold:
            return None

        if predicate is None:
            predicate = ANYTHING

        if self._lower_func(origin):
            children = [self._lower_child, self._upper_child]
        else:
            children = [self._upper_child, self._lower_child]

        best_match = None
        for child in children:
            child_match = child.nearest_to(origin, predicate, threshold)
            if child_match is not None:
                best_match = child_match
                threshold = (child_match.point - origin).distance

        return best_match


Node = Union[Leaf[ValueType], SplitNode[ValueType]]
