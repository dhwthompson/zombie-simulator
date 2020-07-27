from typing import ClassVar, Generic, Iterable, Optional, Tuple, TypeVar, Union

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore

from space import BoundingBox, UnlimitedBoundingBox, Vector

State = Union["Living", "Dead", "Undead"]

ActionType = TypeVar("ActionType", covariant=True)


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
    def character_at(self, offset: Vector) -> object:
        ...

    def nearest(self, **attributes: bool) -> Optional[Vector]:
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
        return self._viewpoint.nearest(undead=False, living=True)

    @property
    def nearest_zombie(self) -> Optional[Vector]:
        return self._viewpoint.nearest(undead=True)

    def from_offset(self, offset: Vector) -> "TargetVectors":
        return TargetVectors(self._viewpoint.from_offset(offset))


class VectorContainer(Protocol):

    # For reasons I don't fully understand, typing.Container[T] doesn't
    # actually seem to respect the [T] part

    def __contains__(self, vector: Vector) -> bool:
        ...


class Obstacles:
    def __init__(self, viewpoint: Viewpoint):
        self._viewpoint = viewpoint

    def __contains__(self, vector: Vector) -> bool:
        if vector == Vector.ZERO:
            return False
        return self._viewpoint.character_at(vector) is not None


class Living:

    living = True
    undead = False
    movement_range = BoundingBox.range(2)
    next_state = None

    def attack(self, target_vectors: TargetVectors) -> Optional[Vector]:
        return None

    def best_move(
        self, target_vectors: TargetVectors, available_moves: Iterable[Vector]
    ) -> Vector:
        nearest_zombie = target_vectors.nearest_zombie
        if nearest_zombie is None:
            return shortest(available_moves)

        def move_rank(move: Vector) -> Tuple[float, float]:
            viewpoint_after_move = target_vectors.from_offset(move)
            nearest_zombie_after_move = viewpoint_after_move.nearest_zombie
            assert nearest_zombie_after_move is not None
            return (
                -nearest_zombie_after_move.distance,
                move.distance,
            )

        return min(available_moves, key=move_rank)


class Dead:
    def __init__(self, age: int = 0):
        self._age = age

    living: bool = False
    undead: bool = False
    movement_range: Iterable[Vector] = [Vector.ZERO]

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

    living = False
    undead = True
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
    def living(self) -> bool:
        return self._state.living

    @property
    def undead(self) -> bool:
        return self._state.undead

    def next_action(
        self,
        environment: Viewpoint,
        limits: VectorContainer,
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

    def move(
        self, environment: Viewpoint, limits: VectorContainer = UnlimitedBoundingBox()
    ) -> Vector:
        """Choose where to move next.

        Arguments:
            environment: the character's current environment. This is currently
                passed in as a Viewpoint instance, supporting the
                `character_at`, `nearest` and `from_offset` methods.
            limits: any limits on the character's movement provided by the
                edges of the world. This can be anything that reponds to the
                `in` operator.

        Return a Vector object representing this character's intended move. If
        the character does not intend to (or cannot) move, return a zero
        vector.
        """
        target_vectors = TargetVectors(environment)
        obstacles = Obstacles(environment)

        moves = self._available_moves(limits, obstacles)
        return self._state.best_move(target_vectors, moves)

    def _available_moves(
        self, limits: VectorContainer, obstacles: VectorContainer
    ) -> Iterable[Vector]:
        moves = [
            m for m in self._state.movement_range if m in limits and m not in obstacles
        ]
        return moves

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
