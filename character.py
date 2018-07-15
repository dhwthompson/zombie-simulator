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


class MaximiseShortestDistance:
    def __init__(self, targets):
        if not targets:
            raise ValueError('Cannot maximise distance from no targets')
        self._targets = targets

    def best_move(self, moves):
        return min(moves, key=self._move_rank)

    def _move_rank(self, move):
        distances_after_move = [(t - move).distance for t in self._targets]
        return (-min(distances_after_move), move.distance)


class MoveShortestDistance:

    def best_move(self, moves):
        return min(moves, key=self._move_rank)

    def _move_rank(self, move):
        return move.distance


def nearest(vectors):
    return min(vectors, key=lambda v: v.distance, default=None)


def keep_away_from_zombies(target_vectors):
    zombies = target_vectors.zombies

    if zombies:
        return MaximiseShortestDistance(zombies)
    else:
        return MoveShortestDistance()


def stay_still(target_vectors):
    # Assuming there will always be a zero move, this will take it
    return MoveShortestDistance()


def approach_closest_human(target_vectors):
    humans = target_vectors.humans

    if humans:
        return MinimiseDistance(nearest(humans))
    else:
        return MoveShortestDistance()


class CharacterState:

    def __init__(self, speed, movement_strategy):
        self.movement_range = BoundingBox.range(speed)
        self.movement_strategy = movement_strategy


CharacterState.LIVING = CharacterState(
        speed=2,
        movement_strategy=keep_away_from_zombies)

CharacterState.DEAD = CharacterState(
        speed=0,
        movement_strategy=stay_still)

CharacterState.UNDEAD = CharacterState(
        speed=1,
        movement_strategy=approach_closest_human)


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
