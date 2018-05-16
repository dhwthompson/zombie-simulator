import math

import pytest

from space import BoundingBox, Point, Vector


class TestPoint:
    def test_no_arg_constructor(self):
        with pytest.raises(TypeError) as exc:
            Point()

    def test_single_arg_constructor(self):
        with pytest.raises(TypeError):
            Point(3)

    def test_double_argument_constructor(self):
        assert Point(2, 5) is not None

    def test_x_coordinate(self):
        assert Point(2, 5).x == 2

    def test_y_coordinate(self):
        assert Point(2, 5).y == 5

    def test_vector_addition(self):
        p = Point(2, 5) + Vector(1, 1)
        assert (p.x, p.y) == (3, 6)

    def test_point_addition_fails(self):
        # Adding a point to a point doesn't make sense
        with pytest.raises(AttributeError):
            Point(2, 5) + Point(3, 2)

    def test_point_subtraction(self):
        v = Point(2, 5) - Point(3, 2)
        assert (v.dx, v.dy) == Vector(-1, 3)

    def test_point_equality(self):
        assert Point(2, 3) == Point(2, 3)


class TestVector:
    def test_no_arg_constructor(self):
        with pytest.raises(TypeError) as exc:
            Vector()

    def test_single_arg_constructor(self):
        with pytest.raises(TypeError):
            Vector(3)

    def test_double_argument_constructor(self):
        assert Vector(2, 5) is not None

    def test_dx(self):
        assert Vector(2, 6).dx == 2

    def test_dy(self):
        assert Vector(2, 6).dy == 6

    def test_zero_distance(self):
        assert Vector.ZERO.distance == 0

    def test_zero_falsey(self):
        assert not Vector.ZERO

    def test_non_zero_truthy(self):
        assert Vector(1, 1)

    @pytest.mark.parametrize('dx,dy', [(2, 1), (-2, 1), (2, -1), (-2, -1)])
    def test_non_zero_distance(self, dx, dy):
        assert Vector(dx, dy).distance == 5

    def test_value_equality(self):
        assert Vector(2, 5) == Vector(2, 5)

    def test_value_inequality(self):
        assert Vector(2, 5) != Vector(2, 3)

    def test_addition(self):
        v = Vector(2, 5) + Vector(1, 3)
        assert (v.dx, v.dy) == (3, 8)

    def test_subtraction(self):
        v = Vector(2, 5) - Vector(1, 3)
        assert (v.dx, v.dy) == (1, 2)

    def test_infinite_dimensions(self):
        v = Vector.INFINITE
        assert (v.dx, v.dy) == (math.inf, math.inf)

    def test_infinite_distance(self):
        v = Vector.INFINITE
        assert v.distance == math.inf

    def test_infinite_addition(self):
        assert Vector.INFINITE + Vector(1, 2) == Vector.INFINITE

    def test_infinite_subtraction(self):
        assert Vector.INFINITE - Vector(1, 2) == Vector.INFINITE


class TestBoundingBox:

    def test_takes_two_vectors(self):
        BoundingBox(Vector.ZERO, Vector(1, 1))

    def test_empty_box(self):
        box = BoundingBox(Vector.ZERO, Vector.ZERO)
        assert Vector(1, 1) not in box

    def test_negative_box(self):
        box = BoundingBox(Vector.ZERO, Vector(-1, -1))
        assert Vector.ZERO not in box

    def test_vector_containment(self):
        box = BoundingBox(Vector.ZERO, Vector(1, 1))
        assert Vector.ZERO in box

    def test_exclusive_upper_bound(self):
        box = BoundingBox(Vector.ZERO, Vector(1, 1))
        assert Vector(1, 1) not in box

    @pytest.mark.parametrize('coords', [(0, 1), (1, 0), (-1, 0), (0, -1)])
    def test_single_dimension_containment(self, coords):
        box = BoundingBox(Vector.ZERO, Vector(1, 1))
        assert Vector(*coords) not in box


class TestUnlimitedBoundingBox:
    @pytest.mark.parametrize('coords', [(0, 100), (100, 0), (-1000, 0), (10000, -1)])
    def test_contains_everything(self, coords):
        assert Vector(*coords) in BoundingBox.UNLIMITED
