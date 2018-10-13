from roster import Attack, Move, StateChange
from space import BoundingBox, UnlimitedBoundingBox, Vector


class TargetVectors:

    def __init__(self, positions):
        self._positions = positions

    @property
    def humans(self):
        return [pos for pos, char in self._positions if char.living]

    @property
    def zombies(self):
        return [pos for pos, char in self._positions if char.undead]


class Obstacles:

    def __init__(self, environment):
        self._obstacles = [pos for pos, char in environment if pos != Vector.ZERO]

    def __contains__(self, vector):
        return vector in self._obstacles


class MinimiseDistance:
    def __init__(self, target):
        if target is None:
            raise ValueError('Cannot set up strategy with no target')
        self._target = target

    def best_move(self, moves):
        return min(moves, key=self._move_rank)

    def _move_rank(self, move):
        return ((self._target - move).distance, move.distance)

    def __eq__(self, other):
        return (isinstance(other, MinimiseDistance)
                and self._target == other._target)


class MaximiseShortestDistance:
    def __init__(self, targets):
        if not targets:
            raise ValueError('Cannot maximise distance from no targets')
        self._targets = targets

    def best_move(self, moves):
        max_range = max(m.distance for m in moves)
        min_distance = min(t.distance for t in self._targets)

        interesting_targets = [t for t in self._targets
                               if t.distance - max_range <= min_distance + max_range]

        def move_rank(move):
            distances_after_move = [(t - move).distance for t in interesting_targets]
            return (-min(distances_after_move), move.distance)

        return min(moves, key=move_rank)

    def __eq__(self, other):
        return (isinstance(other, MaximiseShortestDistance)
                and self._targets == other._targets)


class MoveShortestDistance:

    def best_move(self, moves):
        return min(moves, key=self._move_rank)

    def _move_rank(self, move):
        return move.distance

    def __eq__(self, other):
        return isinstance(other, MoveShortestDistance)


class NeverAttack:

    def attack(self, environment):
        return None


class AttackTheLiving:

    _attack_range = BoundingBox.range(1)

    def attack(self, environment):
        for offset, character in environment:
            if character.living and offset in self._attack_range:
                return character


class Living:

    living = True
    undead = False
    movement_range = BoundingBox.range(2)
    attack_strategy = NeverAttack()
    next_state = None

    def movement_strategy(self, target_vectors):
        zombies = target_vectors.zombies

        if zombies:
            return MaximiseShortestDistance(zombies)
        else:
            return MoveShortestDistance()


class Dead:

    def __init__(self, age=0):
        self._age = age

    living = False
    undead = False
    movement_range = [Vector.ZERO]
    attack_strategy = NeverAttack()

    _resurrection_age = 20

    def movement_strategy(self, target_vectors):
        # Assuming there will always be a zero move, this will take it
        return MoveShortestDistance()

    @property
    def next_state(self):
        if self._age >= self._resurrection_age:
            return Undead()
        else:
            return Dead(self._age + 1)

    def __eq__(self, other):
        return isinstance(other, Dead) and self._age == other._age


class Undead:

    living = False
    undead = True
    movement_range = BoundingBox.range(1)
    attack_strategy = AttackTheLiving()
    next_state = None

    def movement_strategy(self, target_vectors):
        humans = target_vectors.humans

        if humans:
            return MinimiseDistance(self._nearest(humans))
        else:
            return MoveShortestDistance()

    def _nearest(self, vectors):
        return min(vectors, key=lambda v: v.distance, default=None)

    def __eq__(self, other):
        return isinstance(other, Undead)


class Character:

    def __init__(self, state):
        self._state = state

    @property
    def living(self):
        return self._state.living

    @property
    def undead(self):
        return self._state.undead

    def next_action(self, environment, limits):
        new_state = self._state.next_state
        if new_state:
            return StateChange(self, new_state)
        target = self.attack(environment)
        if target:
            return Attack(self, target)
        move = self.move(environment, limits)
        return Move(self, move)

    def move(self, environment, limits=UnlimitedBoundingBox()):
        """Choose where to move next.

        Arguments:
            environment: the character's current environment. This is currently
                passed in as an iterable of (Vector, Character) pairs, which
                isn't entirely ideal, but works well enough for the moment.
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
        move_rank = self._state.movement_strategy(target_vectors)

        return move_rank.best_move(moves)

    def _available_moves(self, limits, obstacles):
        moves = [m for m in self._state.movement_range
                 if m in limits
                 and m not in obstacles]
        return moves

    def attack(self, environment):
        return self._state.attack_strategy.attack(environment)

    def with_state(self, new_state):
        return Character(state=new_state)

    def attacked(self):
        return self.with_state(Dead())


def default_human():
    return Character(state=Living())


def default_zombie():
    return Character(state=Undead())
