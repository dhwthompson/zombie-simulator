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

    def __init__(self, environment, myself):
        self._obstacles = [e[0] for e in environment if e[1] != myself]

    def __contains__(self, vector):
        return vector in self._obstacles


def nearest(vectors):
    return min(vectors, key=lambda v: v.distance, default=None)


def combine(*functions):
    """Given two move-ranking functions, combine them to make a tuple function."""
    return lambda move: tuple(f(move) for f in functions)


class NullStrategy:

    def __call__(self, move):
        return 0


class MinimiseDistance:
    def __init__(self, target):
        self._target = target

    def __call__(self, move):
        return (self._target - move).distance


class MaximiseShortestDistance:
    def __init__(self, targets):
        if not targets:
            raise ValueError('Cannot maximise distance from no targets')
        self._targets = targets

    def __call__(self, move):
        distances_after_move = [(t - move).distance for t in self._targets]
        return -min(distances_after_move)


def move_shortest_distance(move):
    return move.distance


class CharacterState:

    def __init__(self, speed):
        self.movement_range = BoundingBox.range(speed)


CharacterState.LIVING = CharacterState(speed=2)
CharacterState.DEAD = CharacterState(speed=0)
CharacterState.UNDEAD = CharacterState(speed=1)


class Character:

    def __init__(self, state):
        self._state = state

    @property
    def living(self):
        return self._state == CharacterState.LIVING

    @property
    def undead(self):
        return self._state == CharacterState.UNDEAD

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
        obstacles = Obstacles(environment, myself=self)

        moves = self._available_moves(limits, obstacles)
        move_rank = self._move_rank_for(target_vectors)

        return min(moves, key=move_rank)

    def _available_moves(self, limits, obstacles):
        moves = [m for m in self._state.movement_range
                 if m in limits
                 and m not in obstacles]
        return moves

    def _move_rank_for(self, target_vectors):
        if self._state == CharacterState.LIVING:
            if target_vectors.zombies:
                main_strategy = MaximiseShortestDistance(target_vectors.zombies)
            else:
                main_strategy = NullStrategy()

            return combine(main_strategy, move_shortest_distance)

        if self._state == CharacterState.DEAD:
            return NullStrategy()

        if self._state == CharacterState.UNDEAD:
            target = nearest(target_vectors.humans)
            main_strategy = MinimiseDistance(target) if target else NullStrategy()
            return combine(main_strategy, move_shortest_distance)

        raise Exception('Character in unknown state {}'.format(self._state))

    def attack(self, environment):
        if self._state == CharacterState.LIVING:
            return None
        if self._state == CharacterState.DEAD:
            return None
        if self._state == CharacterState.UNDEAD:
            for offset, character in environment:
                if character.living and offset.distance < 4:
                    return character

    def attacked(self):
        return Character(state=CharacterState.DEAD)


def default_human():
    return Character(state=CharacterState.LIVING)


def default_zombie():
    return Character(state=CharacterState.UNDEAD)
