import math

from hypothesis import assume, example, given
from hypothesis import strategies as st
import pytest

from space import BoundingBox, Point, Vector


points = st.builds(Point, st.integers(), st.integers())
vectors = st.builds(Vector, st.integers(), st.integers())


class TestPoint:
    def test_no_arg_constructor(self):
        with pytest.raises(TypeError) as exc:
            Point()

    def test_single_arg_constructor(self):
        with pytest.raises(TypeError):
            Point(3)

    @given(st.integers(), st.integers())
    def test_accepts_two_coordinates(self, x, y):
        point = Point(x, y)
        assert point.x == x
        assert point.y == y

    @given(points, vectors)
    def test_vector_addition(self, point, vector):
        point_sum = point + vector
        assert isinstance(point_sum, Point)
        assert point_sum.x == point.x + vector.dx
        assert point_sum.y == point.y + vector.dy

    @given(points)
    def test_point_equality(self, point):
        assert point == point

    @given(points, vectors)
    def test_addition_then_subtraction(self, point, vector):
        assert point + vector - point == vector

    def test_point_addition_fails(self):
        # Adding a point to a point doesn't make sense
        with pytest.raises(AttributeError):
            Point(2, 5) + Point(3, 2)


class TestVector:
    def test_no_arg_constructor(self):
        with pytest.raises(TypeError) as exc:
            Vector()

    def test_single_arg_constructor(self):
        with pytest.raises(TypeError):
            Vector(3)

    @given(st.integers(), st.integers())
    def test_accepts_two_coordinates(self, dx, dy):
        vector = Vector(dx, dy)
        assert vector.dx == dx
        assert vector.dy == dy

    def test_zero_distance(self):
        assert Vector.ZERO.distance == 0

    @given(vectors)
    def test_vector_distance(self, vector):
        assert vector.distance >= 0

    @given(vectors)
    @example(Vector.ZERO)
    def test_truthiness(self, vector):
        assert bool(vector) == (vector.distance > 0)

    @pytest.mark.parametrize('dx,dy', [(2, 1), (-2, 1), (2, -1), (-2, -1)])
    def test_non_zero_distance(self, dx, dy):
        assert Vector(dx, dy).distance == 5

    def test_value_equality(self):
        assert Vector(2, 5) == Vector(2, 5)

    def test_value_inequality(self):
        assert Vector(2, 5) != Vector(2, 3)

    @given(vectors, vectors)
    def test_addition(self, vector_a, vector_b):
        vector_sum = vector_a + vector_b
        assert vector_sum.dx == vector_a.dx + vector_b.dx
        assert vector_sum.dy == vector_a.dy + vector_b.dy

    @given(vectors, vectors)
    def test_addition_then_subtraction(self, vector_a, vector_b):
        assert vector_a + vector_b - vector_b == vector_a
        assert vector_a + vector_b - vector_a == vector_b

    def test_infinite_dimensions(self):
        v = Vector.INFINITE
        assert (v.dx, v.dy) == (math.inf, math.inf)

    def test_infinite_distance(self):
        v = Vector.INFINITE
        assert v.distance == math.inf

    @given(vectors)
    def test_infinite_addition(self, vector):
        assert Vector.INFINITE + vector == Vector.INFINITE

    @given(vectors)
    def test_infinite_subtraction(self, vector):
        assert Vector.INFINITE - vector == Vector.INFINITE


class TestBoundingBox:

    def test_takes_two_vectors(self):
        BoundingBox(Vector.ZERO, Vector(1, 1))

    def test_empty_box(self):
        box = BoundingBox(Vector.ZERO, Vector.ZERO)
        assert Vector(1, 1) not in box

    def test_negative_box(self):
        box = BoundingBox(Vector.ZERO, Vector(-1, -1))
        assert Vector.ZERO not in box

    @given(vectors)
    def test_vector_containment(self, vector):
        box = BoundingBox(Vector.ZERO, Vector(1, 1))
        assert (vector in box) == (vector == vector.ZERO)


class TestUnlimitedBoundingBox:

    @given(vectors)
    def test_contains_everything(self, vector):
        assert vector in BoundingBox.UNLIMITED
