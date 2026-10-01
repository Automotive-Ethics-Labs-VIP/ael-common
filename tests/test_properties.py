"""Property-based tests: rules that must hold for every input, not just the examples.

Skipped unless hypothesis is installed (pip install -e ".[dev]").
"""

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ael_common import DIM, Path, State, decode, encode, validate_vector  # noqa: E402
from ael_common.state_vector import DIRECTIONS, OBSTACLE_TYPES, VULNERABLE_GROUPS  # noqa: E402


@st.composite
def paths(draw):
    obstacles = set(draw(st.sets(st.sampled_from(OBSTACLE_TYPES))))
    vulnerable = draw(st.sets(st.sampled_from(VULNERABLE_GROUPS)))
    if vulnerable:
        obstacles.add("pedestrian")  # the spec requires it
    return Path(obstacles, vulnerable)


@st.composite
def states(draw):
    return State(
        num_passengers=draw(st.integers(0, 10)),
        casualties={d: draw(st.integers(0, 50)) for d in DIRECTIONS},
        paths={d: draw(paths()) for d in DIRECTIONS},
        velocity_ego=draw(st.floats(0, 100, allow_nan=False)),
        lane_position=draw(st.floats(-10, 10, allow_nan=False)),
        velocity_delta=draw(st.floats(-50, 50, allow_nan=False)),
    )


@settings(max_examples=300)
@given(states())
def test_any_valid_state_round_trips(state):
    vec = encode(state)
    assert len(vec) == DIM
    assert validate_vector(vec) == []
    assert decode(vec) == state


junk = st.one_of(
    st.none(), st.booleans(), st.integers(), st.floats(), st.text(max_size=3),
    st.binary(max_size=3), st.lists(st.integers(), max_size=2),
)


@settings(max_examples=300)
@given(st.one_of(junk, st.lists(junk, max_size=45), st.lists(st.one_of(junk, st.integers(0, 1)), min_size=40, max_size=40)))
def test_validator_never_crashes(value):
    # It must always answer with a list of problems, never raise.
    assert isinstance(validate_vector(value), list)


@settings(max_examples=300)
@given(st.lists(st.sampled_from([0, 1, 0.0, 1.0, 2, -1, 0.5]), min_size=40, max_size=40))
def test_whatever_validates_decodes_and_reencodes_identically(vec):
    if validate_vector(vec):
        return
    assert encode(decode(vec)) == [float(v) for v in vec]
