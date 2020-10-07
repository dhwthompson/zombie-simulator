from collections import defaultdict
from enum import Enum
import math
from typing import (
    Callable,
    ClassVar,
    Generic,
    Iterable,
    Optional,
    Mapping,
    Protocol,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import attr

from space import BoundingBox, Vector

State = Union["Living", "Dead", "Undead"]

ActionType = TypeVar("ActionType", covariant=True)


class LifeState(Enum):
    LIVING = 1
    DEAD = 2
    UNDEAD = 3

    @classmethod
    def for_character(cls, character: "Character") -> "LifeState":
        return character.life_state


def shortest(vectors: Iterable[Vector]) -> Vector:
    return min(vectors, key=lambda v: v.distance)


class Actions(Protocol[ActionType]):
    def move(self, vector: Vector) -> ActionType:
        ...

    def attack(self, vector: Vector) -> ActionType:
        ...

    def change_state(self, new_state: State) -> ActionType:
        ...


class Viewpoint(Protocol):
    def occupied_points_in(self, box: BoundingBox) -> Set[Vector]:
        ...

    def nearest(self, key: LifeState) -> Optional[Vector]:
        ...

    def from_offset(self, offset: Vector) -> "Viewpoint":
        ...


class SupportsNearestHuman(Protocol):
    @property
    def nearest_human(self) -> Optional[Vector]:
        ...


class TargetVectors:
    def __init__(self, viewpoint: Viewpoint):
        self._viewpoint = viewpoint

    @property
    def nearest_human(self) -> Optional[Vector]:
        return self._viewpoint.nearest(LifeState.LIVING)

    @property
    def nearest_zombie(self) -> Optional[Vector]:
        return self._viewpoint.nearest(LifeState.UNDEAD)

    def from_offset(self, offset: Vector) -> "TargetVectors":
        return TargetVectors(self._viewpoint.from_offset(offset))


@attr.s(auto_attribs=True)
class MoveOption:
    move: Vector
    upper_bound: float


def best_move_upper_bound(
    moves: Iterable[Vector], nearest_func: Callable[[Vector], Optional[Vector]]
) -> Vector:
    """Pick a move that maximises the distance from the nearest enemy.

    This function takes a slightly more considered approach than its
    predecessor, based on the idea that we don't want to call the "find my
    nearest enemy" function more often than we have to.

    As such, the algorithm is:

        - Start out every available move with an unlimited potential distance
        - Pick an arbitrary move and set it as our best option
        - Find out where the nearest enemy would be after that move
        - Use that information to limit the maximum possible distances for
          every other move we know about. For instance, if not moving at all
          would leave us with an enemy at (-10, 0), we know that moving 2 cells
          to the right could only ever increase that to a maximum of 12.
        - Trim out any moves where we know that move could never outmatch the
          best move we know about
        - If there are still moves available that might be better, repeat using
          the move with the most potential

    In the best case, this algorithm works out as follows:

        - Work out where the nearest enemy is
        - Guess that our best move is to run directly away from it
        - Check our closest enemy after that, find that it's better than we
          could get from any other move, and pick that one

    This only leaves us running the nearest-enemy function twice, rather than
    25 times for a 5-by-5 square.
    """
    # Moves that take us further away are good; shorter moves break ties
    move_key = lambda option: (-option.upper_bound, option.move.distance)

    options = sorted([MoveOption(move, math.inf) for move in moves], key=move_key)
    if not options:
        raise ValueError("Attempting to choose from no available moves")

    best_option: Optional[MoveOption] = None

    while options:
        # Either we'll set this as our new best candidate, or we'll discard it. Either
        # way, it's no longer needed in our options to explore
        candidate = options.pop(0)
        nearest = nearest_func(candidate.move)
        if nearest is None:
            return candidate.move
        candidate.upper_bound = nearest.distance
        if best_option is None or candidate.upper_bound > best_option.upper_bound:
            best_option = candidate

        for option in options:
            option.upper_bound = min(
                option.upper_bound, (nearest + (candidate.move - option.move)).distance
            )

        options = sorted(
            [o for o in options if o.upper_bound > best_option.upper_bound],
            key=move_key,
        )

    # We have an earlier check that there are options available, so we've gone
    # around the loop at least once, so we have either broken out and returned,
    # or we've assigned something to `best_option`.
    assert best_option is not None

    return best_option.move


class Living:

    life_state = LifeState.LIVING
    movement_range = BoundingBox.range(2)
    next_state = None

    def attack(self, target_vectors: TargetVectors) -> Optional[Vector]:
        return None

    def best_move(
        self, target_vectors: TargetVectors, available_moves: Iterable[Vector]
    ) -> Vector:
        def nearest_zombie(move: Vector) -> Optional[Vector]:
            return target_vectors.from_offset(move).nearest_zombie

        return best_move_upper_bound(available_moves, nearest_zombie)


class Dead:
    def __init__(self, age: int = 0):
        self._age = age

    life_state = LifeState.DEAD
    movement_range = BoundingBox.range(0)

    _resurrection_age: ClassVar[int] = 20

    def attack(self, target_vectors: TargetVectors) -> Optional[Vector]:
        return None

    def best_move(
        self, target_vectors: TargetVectors, available_moves: Iterable[Vector]
    ) -> Vector:
        if Vector.ZERO not in available_moves:
            raise ValueError("Zero move unavailable for dead character")
        return Vector.ZERO

    @property
    def next_state(self) -> State:
        if self._age >= self._resurrection_age:
            return Undead()
        else:
            return Dead(self._age + 1)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Dead) and self._age == other._age


class Undead:

    life_state = LifeState.UNDEAD
    movement_range = BoundingBox.range(1)
    attack_range = BoundingBox.range(1)
    next_state = None

    def attack(self, target_vectors: SupportsNearestHuman) -> Optional[Vector]:
        nearest_human = target_vectors.nearest_human
        if nearest_human is not None and nearest_human in self.attack_range:
            return nearest_human
        else:
            return None

    def best_move(
        self, target_vectors: SupportsNearestHuman, available_moves: Iterable[Vector]
    ) -> Vector:
        nearest_human = target_vectors.nearest_human
        if nearest_human:

            def move_rank(move: Vector) -> Tuple[float, float]:
                assert nearest_human is not None
                return ((nearest_human - move).distance, move.distance)

            return min(available_moves, key=move_rank)
        else:
            return shortest(available_moves)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Undead)


class Character:
    def __init__(self, state: State):
        self._state = state

    @property
    def life_state(self) -> LifeState:
        return self._state.life_state

    def next_action(
        self,
        environment: Viewpoint,
        limits: BoundingBox,
        actions: Actions[ActionType],
    ) -> ActionType:
        new_state = self._state.next_state
        if new_state:
            return actions.change_state(new_state)
        target_vector = self.attack(environment)
        if target_vector:
            return actions.attack(target_vector)
        move = self.move(environment, limits)
        return actions.move(move)

    def move(self, environment: Viewpoint, limits: BoundingBox) -> Vector:
        """Choose where to move next.

        Arguments:
            environment: the character's current environment. This is currently
                passed in as a Viewpoint instance, supporting the
                `occupied_points_in`, `nearest` and `from_offset` methods.
            limits: any limits on the character's movement provided by the
                edges of the world. This can be anything that reponds to the
                `in` operator.

        Return a Vector object representing this character's intended move. If
        the character does not intend to (or cannot) move, return a zero
        vector.
        """
        target_vectors = TargetVectors(environment)

        moves = self._available_moves(limits, environment)
        return self._state.best_move(target_vectors, moves)

    def _available_moves(
        self, limits: BoundingBox, environment: Viewpoint
    ) -> Iterable[Vector]:
        character_range = self._state.movement_range.intersect(limits)
        obstacles = environment.occupied_points_in(character_range) - {Vector.ZERO}
        return available_moves(character_range, obstacles)

    def attack(self, environment: Viewpoint) -> Optional[Vector]:
        return self._state.attack(TargetVectors(environment))

    def with_state(self, new_state: State) -> "Character":
        return Character(state=new_state)

    def attacked(self) -> "Character":
        return self.with_state(Dead())


def default_human() -> Character:
    return Character(state=Living())


def default_zombie() -> Character:
    return Character(state=Undead())


def available_moves(
    character_range: Iterable[Vector],
    obstacles: Set[Vector],
) -> Set[Vector]:
    """Determine available moves for a character.

    This function checks not only that the target spaces are empty, but that there's a
    path that allows the character to reach them by passing only through empty spaces.
    """
    if Vector.ZERO not in character_range or Vector.ZERO in obstacles:
        raise ValueError("Zero movement unavailable for character")

    def max_offset(move: Vector) -> int:
        return max(abs(move.dx), abs(move.dy))

    def reachable(a: Vector, b: Vector) -> bool:
        return abs(a.dx - b.dx) <= 1 and abs(a.dy - b.dy) <= 1

    moves_by_offset: Mapping[int, Set[Vector]] = defaultdict(set)
    for move in character_range:
        moves_by_offset[max_offset(move)].add(move)

    available_moves = {Vector.ZERO}
    for offset in range(1, max(moves_by_offset.keys()) + 1):
        available_moves |= {
            outer_move
            for outer_move in moves_by_offset[offset]
            if outer_move not in obstacles
            and any(reachable(outer_move, inner_move) for inner_move in available_moves)
        }

    return available_moves
