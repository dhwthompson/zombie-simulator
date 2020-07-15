from collections import namedtuple
from unittest import mock

import pytest

from cli import each_interval, get_world_size

TerminalSize = namedtuple("TerminalSize", ["columns", "lines"])


def test_auto_world_size():
    def get_terminal_size():
        return TerminalSize(80, 25)

    world_size = get_world_size("auto", get_terminal_size, default=None)

    assert world_size == (40, 24)


def test_defined_world_size():
    world_size = get_world_size("40x30", get_terminal_size=None, default=None)

    assert world_size == (40, 30)


def test_default_world_size():
    world_size = get_world_size(None, get_terminal_size=None, default=(40, 20))
    assert world_size == (40, 20)


@pytest.mark.parametrize("bad_size", ["12", "really big", "infxinf", "10.x6"])
def test_malformed_size(bad_size):
    with pytest.raises(ValueError):
        get_world_size(bad_size, get_terminal_size=None, default=(5, 3))


class TestEachInterval:
    def test_yields_none_values(self, sleep_mock):
        gen = each_interval(1, sleep=sleep_mock)
        assert [next(gen), next(gen), next(gen)] == [None, None, None]

    def test_does_not_sleep_for_first_value(self, sleep_mock):
        gen = each_interval(1, sleep=sleep_mock)

        next(gen)

        sleep_mock.assert_not_called()

    def test_sleeps_for_second_value(self, sleep_mock):
        gen = each_interval(5, sleep=sleep_mock)

        next(gen)
        next(gen)

        sleep_mock.assert_called_once()

    def tests_sleeps_until_next_interval(self, sleep_mock):
        current_time = FakeTime(1)

        gen = each_interval(1, current_time=current_time, sleep=sleep_mock)

        next(gen)
        next(gen)

        sleep_mock.assert_called_once_with(1)

    def tests_sleeps_after_delay(self, sleep_mock):
        current_time = FakeTime(1)

        gen = each_interval(1, current_time=current_time, sleep=sleep_mock)

        next(gen)
        current_time.set(1.5)
        next(gen)

        sleep_mock.assert_called_once_with(0.5)

    def tests_zero_sleep_if_late(self, sleep_mock):
        current_time = FakeTime(1)

        gen = each_interval(1, current_time=current_time, sleep=sleep_mock)

        next(gen)
        current_time.set(3)
        next(gen)

        sleep_mock.assert_called_once_with(0)

    def test_does_not_race_to_catch_up(self, sleep_mock):
        current_time = FakeTime(1)

        gen = each_interval(1, current_time=current_time, sleep=sleep_mock)

        next(gen)
        current_time.set(3)
        next(gen)
        next(gen)

        sleep_mock.assert_has_calls([mock.call(0), mock.call(1)])

    @pytest.fixture
    def sleep_mock(self):
        return mock.Mock(spec_set=[])


class FakeTime:
    def __init__(self, value):
        self.set(value)

    def __call__(self):
        return self._value

    def set(self, value):
        self._value = value
