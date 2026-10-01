"""Every rejection path in the validator and constructors."""

import json
import os

import pytest

import ael_common.datasets as datasets
from ael_common import (
    Action,
    Path,
    State,
    ValidationError,
    to_action,
    validate_doc,
    validate_file,
    validate_vector,
)
from ael_common.state_vector import SPEC

from .test_state_vector import CATA_S001

PATHS = {"left": Path(["pedestrian"]), "straight": Path(["pedestrian"]), "right": Path(["barrier"])}


def test_vector_must_be_a_sequence():
    assert "must be a sequence" in validate_vector(5)[0]
    assert "must be a sequence" in validate_vector(x for x in CATA_S001)[0]


def test_negative_speed_rejected():
    vec = list(CATA_S001)
    vec[0] = -1
    assert any("velocity_ego" in p for p in validate_vector(vec))


def test_bool_and_string_values_rejected():
    for bad in (True, "1", b"1", None):
        vec = list(CATA_S001)
        vec[7] = bad
        assert validate_vector(vec), bad


@pytest.mark.parametrize("doc, expected", [
    ([], "unknown kind"),
    ("text", "unknown kind"),
    ({"spec": SPEC, "kind": "scenarios"}, "non-empty object"),
    ({"spec": SPEC, "kind": "scenarios", "scenarios": {}}, "non-empty object"),
    ({"spec": SPEC, "kind": "scenarios", "scenarios": {"S1": [1, 2]}}, "S1: vector has 2 values"),
    ({"spec": SPEC, "kind": "decisions", "decisions": []}, "non-empty object"),
    ({"spec": SPEC, "kind": "decisions", "decisions": {"S1": 0}}, "labels must be a non-empty object"),
    ({"spec": SPEC, "kind": "decisions", "decisions": {"S1": {}}}, "labels must be a non-empty object"),
    ({"spec": SPEC, "kind": "split", "train": "S1", "test": []}, "list of scenario ids"),
    ({"spec": SPEC, "kind": "split", "train": [1], "test": []}, "list of scenario ids"),
])
def test_doc_rejections(doc, expected):
    problems = validate_doc(doc)
    assert any(expected in p for p in problems), problems


def test_kind_validators_reject_non_objects():
    from ael_common.validate import validate_decisions_doc, validate_scenarios_doc, validate_split_doc

    for validator in (validate_scenarios_doc, validate_decisions_doc, validate_split_doc):
        assert any("JSON object" in p for p in validator([]))


def test_ids_match_reports_extra_and_missing():
    from ael_common.validate import validate_ids_match

    problems = validate_ids_match(["A", "B"], ["B", "C"], "x")
    assert any("not in scenarios" in p and "'C'" in p for p in problems)
    assert any("missing scenario ids" in p and "'A'" in p for p in problems)


def test_import_script_prints_usage_without_args():
    import subprocess
    import sys

    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "import_cata_200.py")
    result = subprocess.run([sys.executable, script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    assert result.returncode != 0
    assert "Usage" in result.stderr


def test_kind_mismatch_reported():
    from ael_common.validate import validate_scenarios_doc

    problems = validate_scenarios_doc({"spec": SPEC, "kind": "decisions", "scenarios": {"S1": CATA_S001}})
    assert any("kind is" in p for p in problems)


def test_valid_file_returns_no_problems(tmp_path):
    path = tmp_path / "ok.json"
    path.write_text(json.dumps({"spec": SPEC, "kind": "scenarios", "scenarios": {"S1": CATA_S001}}), encoding="utf-8")
    assert validate_file(str(path)) == []


def test_non_utf8_file_is_a_problem(tmp_path):
    path = tmp_path / "bad.json"
    path.write_bytes(b"\xff\xfe\x00garbage")
    assert validate_file(str(path))


def test_missing_file_raises_os_error(tmp_path):
    # A missing file is a caller mistake, not a data problem: it should not be
    # reported as "invalid data".
    with pytest.raises(OSError):
        validate_file(str(tmp_path / "nope.json"))


def test_state_requires_all_path_keys():
    with pytest.raises(ValueError):
        State(num_passengers=1, casualties={"left": 1, "straight": 1, "right": 1}, paths={"left": Path()})


def test_reprs_are_readable():
    assert repr(Path(["barrier"])) == "Path(obstacles=['barrier'], vulnerable=[])"
    assert "passengers=1" in repr(State(num_passengers=1, casualties={"left": 1, "straight": 1, "right": 1}, paths=PATHS))


def test_to_action_passes_action_through():
    assert to_action(Action.SWERVE_LEFT) is Action.SWERVE_LEFT


def test_cata_loader_rejects_mismatched_ids(tmp_path, monkeypatch):
    for name in ("scenarios.json", "decisions.json", "split.json"):
        src = os.path.join(datasets._DIR, name)
        with open(src, encoding="utf-8") as f:
            doc = json.load(f)
        if name == "decisions.json":
            del doc["decisions"]["CATA_S001"]
        (tmp_path / name).write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(datasets, "_DIR", str(tmp_path))
    datasets._cata_200.cache_clear()
    try:
        with pytest.raises(ValidationError, match="missing scenario ids"):
            datasets.load_cata_200()
    finally:
        datasets._cata_200.cache_clear()
