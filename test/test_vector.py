import math

import pytest

from vector import Vector

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
