from hypothesis import strategies as st


def list_and_element(l):
    """Given a list, return a strategy of that list and one of its elements.

    This can be connected onto an existing list strategy using the `flatmap`
    method.
    """
    return st.tuples(st.just(l), st.sampled_from(l))
