"""Regressions for the v0.1.0 code review."""

import json
import os
import sys

import pytest

from ael_common import (
    Action,
    Path,
    State,
    ValidationError,
    check_file,
    check_vector,
    decode,
    load_cata_200,
    to_action,
    validate_file,
)
from ael_common.state_vector import SPEC

from .test_state_vector import CATA_S001

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "ael_common", "data", "cata_200")


# numpy / torch inputs ---------------------------------------------------------

def test_numpy_vectors_are_accepted():
    np = pytest.importorskip("numpy")
    for dtype in (np.float32, np.float64, np.int64):
        vec = np.array(CATA_S001, dtype=dtype)
        check_vector(vec)
        assert decode(vec) == decode(CATA_S001)


def test_torch_vectors_are_accepted():
    torch = pytest.importorskip("torch")
    vec = torch.tensor(CATA_S001, dtype=torch.float32)
    check_vector(vec)
    assert decode(vec) == decode(CATA_S001)


def test_numpy_still_rejects_bad_values():
    np = pytest.importorskip("numpy")
    vec = np.array(CATA_S001, dtype=np.float32)
    vec[7] = 0.2
    with pytest.raises(ValidationError):
        check_vector(vec)


def test_to_action_accepts_argmax_results():
    np = pytest.importorskip("numpy")
    assert to_action(np.int64(1)) is Action.SWERVE_LEFT
    assert to_action(np.argmax([0.1, 0.2, 0.7])) is Action.SWERVE_RIGHT
    with pytest.raises(ValueError):
        to_action(np.float64(1.0))
    with pytest.raises(ValueError):
        to_action(np.bool_(True))


def test_to_action_accepts_torch_argmax():
    torch = pytest.importorskip("torch")
    assert to_action(torch.argmax(torch.tensor([0.9, 0.05, 0.05]))) is Action.MAINTAIN


# files ------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["scenarios.json", "decisions.json", "split.json"])
def test_every_bundled_file_validates(name):
    check_file(os.path.join(DATA, name))


def _write(tmp_path, text):
    path = tmp_path / "data.json"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_malformed_json_returns_problem_not_crash(tmp_path):
    path = _write(tmp_path, '{"spec": "ael-v1", "kind": "scen')
    assert validate_file(path)
    with pytest.raises(ValidationError):
        check_file(path)


def test_unhashable_kind_returns_problem(tmp_path):
    path = _write(tmp_path, json.dumps({"spec": SPEC, "kind": []}))
    assert validate_file(path)


def test_split_rejects_overlap_and_duplicates(tmp_path):
    overlap = _write(tmp_path, json.dumps({"spec": SPEC, "kind": "split", "train": ["A", "B"], "test": ["B"]}))
    assert any("share ids" in p for p in validate_file(overlap))
    dupes = _write(tmp_path, json.dumps({"spec": SPEC, "kind": "split", "train": ["A", "A"], "test": ["B"]}))
    assert any("duplicate" in p for p in validate_file(dupes))


# encode / Path ------------------------------------------------------------------

def test_encode_rejects_invalid_state():
    paths = {"left": Path([], ["child"]), "straight": Path(["pedestrian"]), "right": Path(["barrier"])}
    with pytest.raises(ValidationError):
        State(num_passengers=1, casualties={"straight": 1, "left": 1, "right": 1}, paths=paths).encode()
    ok_paths = {"left": Path(["pedestrian"]), "straight": Path(["pedestrian"]), "right": Path(["barrier"])}
    with pytest.raises(ValidationError):
        State(num_passengers=1, casualties={"straight": -1, "left": 1, "right": 1}, paths=ok_paths).encode()


def test_path_is_hashable():
    distinct = {decode(v).paths["right"] for v in load_cata_200().values()}
    assert distinct == {Path(["barrier"])}


def test_loaders_return_copies():
    load_cata_200()["CATA_S001"][0] = 999
    assert load_cata_200()["CATA_S001"][0] == 10


# import script ------------------------------------------------------------------

def _fake_ethical_head(tmp_path, decisions_override=None):
    src = tmp_path / "Ethical_Head" / "data"
    (src / "splits").mkdir(parents=True)
    scenarios = {"S1": CATA_S001, "S2": CATA_S001}
    decisions = decisions_override or {"S1": {"utilitarian": 0, "kantian": 0}, "S2": {"utilitarian": 1, "kantian": 0}}
    split = {"train": {"scenarios": {"S1": CATA_S001}}, "test": {"scenarios": {"S2": CATA_S001}}}
    (src / "scenarios_200.json").write_text(json.dumps(scenarios), encoding="utf-8")
    (src / "decisions_200.json").write_text(json.dumps(decisions), encoding="utf-8")
    (src / "splits" / "train_test_split.json").write_text(json.dumps(split), encoding="utf-8")
    return str(tmp_path / "Ethical_Head")


@pytest.fixture
def importer():
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    try:
        import import_cata_200
        yield import_cata_200
    finally:
        sys.path.pop(0)


def test_import_writes_valid_files(tmp_path, importer):
    out = tmp_path / "out"
    importer.main(_fake_ethical_head(tmp_path), out=str(out))
    for name in ("scenarios.json", "decisions.json", "split.json"):
        check_file(str(out / name))


@pytest.mark.parametrize("bad_decisions", [
    {"S1": {"utilitarian": 4, "kantian": 0}, "S2": {"utilitarian": 1, "kantian": 0}},  # 5-action ID
    {"S1": {"utilitarian": 0, "kantian": 0}},  # missing S2
])
def test_import_writes_nothing_on_bad_source(tmp_path, importer, bad_decisions):
    out = tmp_path / "out"
    with pytest.raises(ValidationError):
        importer.main(_fake_ethical_head(tmp_path, bad_decisions), out=str(out))
    assert not out.exists()
