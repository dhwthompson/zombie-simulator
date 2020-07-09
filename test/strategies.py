from hypothesis import strategies as st


def list_and_element(l):
    """Given a list, return a strategy of that list and one of its elements.

    This can be connected onto an existing list strategy using the `flatmap`
    method.
    """
    return st.tuples(st.just(l), st.sampled_from(l))


def dict_and_element(d):
    """Given an ordered dict-like object, return that dict and a (k, v) pair."""
    return st.tuples(st.just(d), st.sampled_from(d).map(lambda k: (k, d[k])))
