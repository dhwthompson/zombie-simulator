import attr
from enum import Enum
from itertools import chain
import math
from typing import (
    Callable,
    Dict,
    Generic,
    Hashable,
    Iterable,
    Optional,
    Set,
    TypeVar,
    Tuple,
    Union,
)

from space import Area, Point

ValueType = TypeVar("ValueType")
PartitionKeyType = TypeVar("PartitionKeyType", bound=Hashable)
LowerFunc = Callable[[Point], bool]


@attr.s(auto_attribs=True, frozen=True)
class Match(Generic[ValueType]):
    point: Point
    value: ValueType


@attr.s(auto_attribs=True, frozen=True)
class PartitionTree(Generic[PartitionKeyType, ValueType]):
    @classmethod
    def build(
        cls,
        area: Area,
        partition_func: Callable[[ValueType], PartitionKeyType],
        positions: Optional[Dict[Point, ValueType]] = None,
    ) -> "PartitionTree[PartitionKeyType, ValueType]":
        tree: "PartitionTree[PartitionKeyType, ValueType]" = PartitionTree(
            area, partition_func, {}
        )
        if positions:
            for point, value in positions.items():
                tree = tree.set(point, value)

        return tree

    _area: Area
    _partition_func: Callable[[ValueType], PartitionKeyType]
    _trees: Dict[PartitionKeyType, "SpaceTree[ValueType]"]

    def __len__(self) -> int:
        return sum(len(t) for t in self._trees.values())

    def __contains__(self, position: Point) -> bool:
        return any(position in tree for tree in self._trees.values())

    def __getitem__(self, position: Point) -> ValueType:
        if (value := self.get(position)) is not None:
            return value
        else:
            raise KeyError(position)

    def get(self, position: Point) -> Optional[ValueType]:
        for tree in self._trees.values():
            if (char := tree.get(position)) is not None:
                return char
        else:
            return None

    def items(self) -> Iterable[Tuple[Point, ValueType]]:
        return chain.from_iterable(t.items() for t in self._trees.values())

    def items_in(self, area: Area) -> Set[Match[ValueType]]:
        matches: Set[Match[ValueType]] = set()
        for tree in self._trees.values():
            matches |= tree.items_in(area)
        return matches

    def nearest_to(
        self,
        origin: Point,
        key: PartitionKeyType,
    ) -> Optional[Match[ValueType]]:
        try:
            tree = self._trees[key]
        except KeyError:
            return None

        return tree.nearest_to(origin)

    def set(
        self, position: Point, character: ValueType
    ) -> "PartitionTree[PartitionKeyType, ValueType]":
        char_key = self._partition_func(character)
        new_trees = self._trees.copy()
        key_tree = new_trees.get(char_key, SpaceTree.build(self._area))
        new_trees[char_key] = key_tree.set(position, character)

        return PartitionTree(self._area, self._partition_func, new_trees)

    def unset(self, position: Point) -> "PartitionTree[PartitionKeyType, ValueType]":
        for key, tree in self._trees.items():
            if position in tree:
                new_trees = self._trees.copy()
                new_trees[key] = tree.unset(position)
                return PartitionTree(self._area, self._partition_func, new_trees)
        else:
            raise KeyError(position)


class SpaceTree(Generic[ValueType]):
    """A dict-like structure that maps 2-dimensional positions to values.

    The best way to build one of these trees is with the `build` class method:

        >>> tree = SpaceTree.build(
        ...     Area.from_zero(10, 10),
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

    def nearest_to(self, origin: Point) -> Optional[Match[ValueType]]:
        """Return the nearest entry to a given point, not including the point itself."""
        return self._root.nearest_to(origin)

    def items_in(self, area: Area) -> Set[Match[ValueType]]:
        return set(self._root.items_in(area))


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

    def items_in(self, area: Area) -> Iterable[Match[ValueType]]:
        if not self._area.intersects_with(area):
            return []
        return (
            Match(pos, item) for pos, item in self._positions.items() if pos in area
        )

    def _split(self) -> Tuple[Area, Area, LowerFunc]:
        if self._area.width >= self._area.height:
            # Split horizontally
            midpoint_x = (self._area._lower.x + self._area._upper.x) // 2
            lower_area = Area(self._area._lower, Point(midpoint_x, self._area._upper.y))
            upper_area = Area(Point(midpoint_x, self._area._lower.y), self._area._upper)
            lower_func = lambda point: point.x < midpoint_x

            return (lower_area, upper_area, lower_func)
        else:
            # Split vertically
            midpoint_y = (self._area._lower.y + self._area._upper.y) // 2
            lower_area = Area(self._area._lower, Point(self._area._upper.x, midpoint_y))
            upper_area = Area(Point(self._area._lower.x, midpoint_y), self._area._upper)
            lower_func = lambda point: point.y < midpoint_y

            return (lower_area, upper_area, lower_func)

    def set(self, point: Point, value: ValueType) -> "Node[ValueType]":
        if point not in self._positions and len(self._positions) >= self.LEAF_MAX:
            lower_area, upper_area, lower_func = self._split()

            lower_child = Leaf(
                lower_area, {p: v for p, v in self.items() if lower_func(p)}
            )

            upper_child = Leaf(
                upper_area,
                {p: v for p, v in self.items() if not lower_func(p)},
            )

            split_node = SplitNode(self._area, lower_func, lower_child, upper_child)
            return split_node.set(point, value)
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
        threshold: float = math.inf,
    ) -> Optional[Match[ValueType]]:

        if self._area.distance_from(origin) > threshold:
            return None

        best_match = None
        for pos, value in self._positions.items():
            if pos == origin:
                continue
            distance = (pos - origin).distance
            if distance < threshold:
                threshold = distance
                best_match = Match(pos, value)
        return best_match


class SplitNode(Generic[ValueType]):
    """Helper class for SpaceTree, representing a node that has been split into two."""

    def __init__(
        self,
        area: Area,
        lower_func: LowerFunc,
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

    def items_in(self, area: Area) -> Iterable[Match[ValueType]]:
        if not self._area.intersects_with(area):
            return []
        return chain(self._lower_child.items_in(area), self._upper_child.items_in(area))

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
        threshold: float = math.inf,
    ) -> Optional[Match[ValueType]]:

        if self._area.distance_from(origin) > threshold:
            return None

        if self._lower_func(origin):
            children = [self._lower_child, self._upper_child]
        else:
            children = [self._upper_child, self._lower_child]

        best_match = None
        for child in children:
            child_match = child.nearest_to(origin, threshold)
            if child_match is not None:
                best_match = child_match
                threshold = (child_match.point - origin).distance

        return best_match


Node = Union[Leaf[ValueType], SplitNode[ValueType]]
