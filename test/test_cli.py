from collections import namedtuple

import pytest

from cli import get_world_size

TerminalSize = namedtuple('TerminalSize', ['columns', 'lines'])


def test_auto_world_size():
    def get_terminal_size():
        return TerminalSize(80, 25)

    world_size = get_world_size('auto', get_terminal_size, default=None)

    assert world_size == (40, 24)


def test_defined_world_size():
    world_size = get_world_size('40x30', get_terminal_size=None, default=None)

    assert world_size == (40, 30)


def test_default_world_size():
    world_size = get_world_size(None, get_terminal_size=None, default=(40, 20))
    assert world_size == (40, 20)


@pytest.mark.parametrize('bad_size', ['12', 'really big', 'infxinf', '10.x6'])
def test_malformed_size(bad_size):
    with pytest.raises(ValueError):
        get_world_size(bad_size, get_terminal_size=None, default=(5, 3))
