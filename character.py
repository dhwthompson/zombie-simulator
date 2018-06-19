from space import BoundingBox, Vector


class TargetVectors:

    def __init__(self, environment):
        self._environment = environment

    @property
    def humans(self):
        return [e[0] for e in self._environment if e[1].living]

    @property
    def zombies(self):
        return [e[0] for e in self._environment if not e[1].living]


class Obstacles:

    def __init__(self, environment, myself):
        self._obstacles = [e[0] for e in environment if e[1] != myself]

    def __contains__(self, vector):
        return vector in self._obstacles


def nearest(vectors):
    return min(vectors, key=lambda v: v.distance, default=Vector.INFINITE)


def combine(*functions):
    """Given two move-ranking functions, combine them to make a tuple function."""
    return lambda move: tuple(f(move) for f in functions)


class MinimiseDistance:
    def __init__(self, target):
        self._target = target

    def __call__(self, move):
        return (self._target - move).distance


class MaximiseDistance:
    def __init__(self, target):
        self._target = target

    def __call__(self, move):
        return -(self._target - move).distance


def move_shortest_distance(move):
    return move.distance


class Character:

    def move(self, environment, limits=BoundingBox.UNLIMITED):
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
        moves = [m for m in self._movement_range
                 if m in limits
                 and m not in obstacles]
        return moves

    @property
    def _movement_range(self):
        coord_range = range(-self.speed, self.speed + 1)
        return [Vector(dx, dy) for dx in coord_range for dy in coord_range]

    def _move_rank_for(self, target_vectors):
        raise NotImplementedError


class Human(Character):

    living = True
    speed = 2

    def _move_rank_for(self, target_vectors):
        nearest_zombie = nearest(target_vectors.zombies)
        return combine(MaximiseDistance(nearest_zombie),
                       move_shortest_distance)


class Zombie(Character):

    living = False
    speed = 1

    def _move_rank_for(self, target_vectors):
        nearest_human = nearest(target_vectors.humans)
        return combine(MinimiseDistance(nearest_human),
                       move_shortest_distance)
