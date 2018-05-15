import math

import pytest

from vector import BoundingBox, Vector


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
        assert Vector(0, 0).distance == 0

    def test_zero_falsey(self):
        assert not Vector(0, 0)

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
        BoundingBox(Vector(0, 0), Vector(1, 1))

    def test_empty_box(self):
        box = BoundingBox(Vector(0, 0), Vector(0, 0))
        assert Vector(1, 1) not in box

    def test_negative_box(self):
        box = BoundingBox(Vector(0, 0), Vector(-1, -1))
        assert Vector(0, 0) not in box

    def test_vector_containment(self):
        box = BoundingBox(Vector(0, 0), Vector(1, 1))
        assert Vector(0, 0) in box

    def test_exclusive_upper_bound(self):
        box = BoundingBox(Vector(0, 0), Vector(1, 1))
        assert Vector(1, 1) not in box

    @pytest.mark.parametrize('coords', [(0, 1), (1, 0), (-1, 0), (0, -1)])
    def test_single_dimension_containment(self, coords):
        box = BoundingBox(Vector(0, 0), Vector(1, 1))
        assert Vector(*coords) not in box


class TestUnlimitedBoundingBox:
    @pytest.mark.parametrize('coords', [(0, 100), (100, 0), (-1000, 0), (10000, -1)])
    def test_contains_everything(self, coords):
        assert Vector(*coords) in BoundingBox.UNLIMITED
