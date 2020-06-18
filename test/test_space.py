import math

from hypothesis import assume, example, given
from hypothesis import strategies as st
import pytest

from space import Area, BoundingBox, Point, UnlimitedBoundingBox, Vector


points = st.from_type(Point)
vectors = st.from_type(Vector)
non_huge_vectors = vectors.filter(lambda v: v.distance < 10000)


# Generates tuples of Points such that all the second Point's components are
# greater than the corresponding components of the first Point. When used as
# arguments for an Area, these generate non-empty Areas.
ordered_points = points.flatmap(
        lambda v: st.tuples(
            st.just(v),
            st.builds(Point, x=st.integers(min_value=v.x+1),y=st.integers(min_value=v.y+1))
        )
)


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


class TestArea:

    def test_no_arg_constructor(self):
        with pytest.raises(TypeError) as exc:
            Area()

    def test_single_arg_constructor(self):
        with pytest.raises(TypeError):
            Area(Point(1, 3))

    @given(points, points)
    def test_two_point_constructor(self, point_a, point_b):
        Area(point_a, point_b)

    @given(ordered_points)
    def test_contains_lower_bound(self, points):
        lower, upper = points
        assert lower in Area(lower, upper)

    @given(points, points)
    def test_excludes_upper_bound(self, lower, upper):
        assert upper not in Area(lower, upper)

    @given(ordered_points)
    def test_includes_midpoint(self, points):
        lower, upper = points
        midpoint = Point((lower.x + upper.x) // 2, (lower.y + upper.y) // 2)
        assert midpoint in Area(lower, upper)

    def test_excludes_on_x_coordinate(self):
        area = Area(Point(0, 0), Point(3, 3))
        assert Point(4, 1) not in area

    def test_excludes_on_y_coordinate(self):
        area = Area(Point(0, 0), Point(3, 3))
        assert Point(1, 4) not in area

    @given(points, points, points)
    def test_from_origin_type(self, lower, upper, origin):
        area = Area(lower, upper)
        assert isinstance(area.from_origin(origin), BoundingBox)

    @given(st.from_type(Area), points, points)
    @example(Area(Point(0, 0), Point(2, 2)), Point(0, 0), Point(1, 1))
    def test_from_origin_containment(self, area, origin, point):
        from_origin = area.from_origin(origin)

        assert (point in area) == ((point - origin) in from_origin)


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
        assert Vector(dx, dy).distance == math.sqrt(5)

    @given(non_huge_vectors, non_huge_vectors)
    def test_triangle_inequality(self, a, b):
        assert (a + b).distance <= a.distance + b.distance

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


# When tests iterate over bounding boxes, anything much larger than this will
# be too big to get through quickly
small_vectors = st.builds(Vector,
                          st.integers(min_value=-30, max_value=30),
                          st.integers(min_value=-30, max_value=30))


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

    @given(st.builds(BoundingBox, small_vectors, small_vectors))
    def test_iteration_covers_box(self, box):
        for vector in box:
            assert vector in box

    @given(box=st.builds(BoundingBox, small_vectors, small_vectors), vector=vectors)
    @example(BoundingBox(Vector(-2, -2), Vector(3, 3)), Vector(2, 3))
    def test_iteration_is_limited_to_box(self, box, vector):
        assume(vector not in box)
        assert vector not in list(box)

    @given(st.integers(min_value=0), vectors)
    @example(radius=10, vector=Vector(10, 10))
    @example(radius=0, vector=Vector(0, 0))
    def test_range(self, radius, vector):
        bounding_box = BoundingBox.range(radius)
        if abs(vector.dx) <= radius and abs(vector.dy) <= radius:
            assert vector in bounding_box
        else:
            assert vector not in bounding_box

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            BoundingBox.range(-1)


class TestUnlimitedBoundingBox:

    @given(vectors)
    def test_contains_everything(self, vector):
        assert vector in UnlimitedBoundingBox()
