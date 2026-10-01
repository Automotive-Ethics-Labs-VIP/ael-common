import json

import pytest

from ael_common import ValidationError, check_file, check_vector, validate_file, validate_vector
from ael_common.state_vector import SPEC

from .test_state_vector import CATA_S001


def test_valid_vector_has_no_problems():
    assert validate_vector(CATA_S001) == []


def test_wrong_length():
    assert "expected 40" in validate_vector(CATA_S001[:39])[0]


def test_non_numeric_and_nan():
    vec = list(CATA_S001)
    vec[0] = "fast"
    assert validate_vector(vec)
    vec[0] = float("nan")
    assert validate_vector(vec)


def test_flag_must_be_binary():
    vec = list(CATA_S001)
    vec[7] = 0.2
    assert any("must be 0 or 1" in p for p in validate_vector(vec))


def test_counts_must_be_whole():
    vec = list(CATA_S001)
    vec[4] = 1.5
    assert any("whole number" in p for p in validate_vector(vec))


def test_vulnerable_needs_pedestrian():
    vec = list(CATA_S001)
    vec[18] = 0  # straight_pedestrian
    vec[25] = 1  # straight_is_child
    assert any("no pedestrian" in p for p in validate_vector(vec))


def test_team_b_extractor_style_vector_is_rejected():
    # Team B's pre-v1 extractor puts normalised counts and 0-1 vulnerability
    # scores in the path blocks; the validator must not accept that silently.
    vec = [8.3, 1, 2.1, 0.4, 1, 0, 2] + [0.2, 1, 0, 0, 0, 0, 0, 0, 0, 0.9, 0.9] * 3
    with pytest.raises(ValidationError):
        check_vector(vec)


def _write(tmp_path, doc):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def test_scenarios_file_ok(tmp_path):
    path = _write(tmp_path, {"spec": SPEC, "kind": "scenarios", "scenarios": {"S1": CATA_S001}})
    check_file(path)


def test_file_with_other_spec_is_rejected(tmp_path):
    path = _write(tmp_path, {"spec": "ael-v0", "kind": "scenarios", "scenarios": {"S1": CATA_S001}})
    assert any("spec" in p for p in validate_file(path))


def test_file_with_unknown_kind_is_rejected(tmp_path):
    path = _write(tmp_path, {"spec": SPEC, "kind": "vectors", "scenarios": {}})
    assert validate_file(path)


def test_decisions_reject_five_action_ids(tmp_path):
    path = _write(tmp_path, {"spec": SPEC, "kind": "decisions", "decisions": {"S1": {"utilitarian": 4}}})
    assert any("not in the v1 set" in p for p in validate_file(path))
