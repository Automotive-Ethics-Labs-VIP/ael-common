import pytest

from ael_common import DIM, FIELD_NAMES, Path, State, decode, encode, index, load_cata_200

# CATA_S001 as written in Team C's corrected vectors.
CATA_S001 = [10, 1, 0, 0, 1, 2, 1,
             1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0,
             1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]


def test_layout_has_40_unique_fields():
    assert DIM == 40
    assert len(set(FIELD_NAMES)) == 40


def test_golden_indices():
    assert index("velocity_ego") == 0
    assert index("casualties_if_straight") == 4
    assert index("casualties_if_left") == 5
    assert index("casualties_if_right") == 6
    assert index("left_pedestrian") == 7
    assert index("left_is_disabled") == 17
    assert index("straight_pedestrian") == 18
    assert index("right_barrier") == 34
    assert index("right_is_disabled") == 39


def test_old_names_alias_to_casualties():
    assert index("num_ped_if_straight") == 4
    assert index("num_ped_if_right") == 6


def test_unknown_field_raises():
    with pytest.raises(KeyError):
        index("left_dog")


def test_golden_decode_cata_s001():
    state = decode(CATA_S001)
    assert state.velocity_ego == 10
    assert state.num_passengers == 1
    assert state.casualties == {"straight": 1, "left": 2, "right": 1}
    assert state.paths["left"] == Path(["pedestrian"], ["child", "elderly"])
    assert state.paths["straight"] == Path(["pedestrian"])
    assert state.paths["right"] == Path(["barrier"])


def test_encode_builds_cata_s001():
    state = State(
        num_passengers=1,
        casualties={"straight": 1, "left": 2, "right": 1},
        paths={
            "left": Path(["pedestrian"], ["child", "elderly"]),
            "straight": Path(["pedestrian"]),
            "right": Path(["barrier"]),
        },
    )
    assert encode(state) == CATA_S001


def test_all_200_round_trip():
    for sid, vec in load_cata_200().items():
        assert encode(decode(vec)) == vec, sid


def test_path_rejects_unknown_types():
    with pytest.raises(ValueError):
        Path(["dog"])
    with pytest.raises(ValueError):
        Path(["pedestrian"], ["teenager"])


def test_state_requires_all_directions():
    with pytest.raises(ValueError):
        State(num_passengers=1, casualties={"left": 1}, paths={"left": Path()})
