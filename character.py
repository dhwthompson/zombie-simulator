from roster import Attack, Move, StateChange
from space import BoundingBox, UnlimitedBoundingBox, Vector


def shortest(vectors):
    return min(vectors, key=lambda v: v.distance)


class TargetVectors:

    def __init__(self, positions):
        self._positions = positions

    @property
    def humans(self):
        return [pos for pos, char in self._positions if char.living]

    @property
    def nearest_human(self):
        return min(self.humans, key=lambda v: v.distance, default=None)

    @property
    def zombies(self):
        return [pos for pos, char in self._positions if char.undead]


class Obstacles:

    def __init__(self, environment):
        self._obstacles = [pos for pos, char in environment if pos != Vector.ZERO]

    def __contains__(self, vector):
        return vector in self._obstacles


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

    def best_move(self, target_vectors, available_moves):
        zombies = target_vectors.zombies

        if zombies:
            max_range = max(m.distance for m in available_moves)
            min_distance = min(z.distance for z in zombies)

            interesting_targets = [z for z in zombies
                                   if z.distance - max_range <= min_distance + max_range]

            def move_rank(move):
                distances_after_move = [(t - move).distance for t in interesting_targets]
                return (-min(distances_after_move), move.distance)

            return min(available_moves, key=move_rank)
        else:
            return shortest(available_moves)


class Dead:

    def __init__(self, age=0):
        self._age = age

    living = False
    undead = False
    movement_range = [Vector.ZERO]
    attack_strategy = NeverAttack()

    _resurrection_age = 20

    def best_move(self, target_vectors, available_moves):
        if Vector.ZERO not in available_moves:
            raise ValueError('Zero move unavailable for dead character')
        return Vector.ZERO

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

    def best_move(self, target_vectors, available_moves):
        nearest_human = target_vectors.nearest_human
        if nearest_human:
            def move_rank(move):
                return ((nearest_human - move).distance, move.distance)

            return min(available_moves, key=move_rank)
        else:
            return shortest(available_moves)

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
        return self._state.best_move(target_vectors, moves)

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
