from collections import Counter

import pytest

from ael_common import Action, decode, load_cata_200, load_cata_200_labels, load_cata_200_split, to_action


def test_cata_200_size():
    assert len(load_cata_200()) == 200
    assert set(load_cata_200()) == set(load_cata_200_labels())


def test_label_distribution_matches_paper():
    labels = load_cata_200_labels()
    util = Counter(l["utilitarian"] for l in labels.values())
    assert util == {Action.MAINTAIN: 60, Action.SWERVE_LEFT: 100, Action.SWERVE_RIGHT: 40}


def test_kantian_is_always_maintain():
    # Known property of CATA-200: Kantian accuracy on it is trivially 100%.
    labels = load_cata_200_labels()
    assert {l["kantian"] for l in labels.values()} == {Action.MAINTAIN}


def test_utilitarian_is_fewest_casualties():
    # Ties broken maintain, then left, then right.
    order = [(Action.MAINTAIN, "straight"), (Action.SWERVE_LEFT, "left"), (Action.SWERVE_RIGHT, "right")]
    labels = load_cata_200_labels()
    for sid, vec in load_cata_200().items():
        casualties = decode(vec).casualties
        best = min(order, key=lambda ad: casualties[ad[1]])[0]
        assert labels[sid]["utilitarian"] == best, sid


def test_split_is_160_40_and_disjoint():
    split = load_cata_200_split()
    assert len(split["train"]) == 160
    assert len(split["test"]) == 40
    assert not set(split["train"]) & set(split["test"])
    assert set(split["train"]) | set(split["test"]) == set(load_cata_200())


def test_to_action():
    assert to_action(1) is Action.SWERVE_LEFT
    assert to_action("swerve_right") is Action.SWERVE_RIGHT
    for bad in (3, 4, -1, True, "brake_hard", 1.0):
        with pytest.raises(ValueError):
            to_action(bad)
