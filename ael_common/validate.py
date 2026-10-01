"""Check vectors and data files against the ael-v1 agreement.

validate_* functions return a list of problems (empty means valid).
check_* functions raise ValidationError instead.
"""

import json
import math
from typing import Any, Dict, List, Sequence

from .actions import is_bool, to_action
from .state_vector import (
    BINARY_INDICES,
    BLOCK_START,
    COUNT_INDICES,
    DIM,
    DIRECTIONS,
    FIELD_NAMES,
    OBSTACLE_TYPES,
    SPEC,
    VULNERABLE_GROUPS,
)


class ValidationError(ValueError):
    pass


def _as_number(v: Any) -> float:
    """float(v) for real numbers, including numpy/torch scalars; TypeError otherwise."""
    if isinstance(v, (str, bytes)) or is_bool(v):
        raise TypeError
    return float(v)


def validate_vector(vec: Sequence[Any]) -> List[str]:
    """Problems with a 40-D vector. Accepts lists, tuples, numpy arrays and torch tensors."""
    try:
        n = len(vec)
    except TypeError:
        return ["vector must be a sequence, got {}".format(type(vec).__name__)]
    if n != DIM:
        return ["vector has {} values, expected {}".format(n, DIM)]

    problems = []  # type: List[str]
    values = []  # type: List[float]
    for i, v in enumerate(vec):
        try:
            x = _as_number(v)
        except (TypeError, ValueError):
            problems.append("[{}] {} is not a number: {!r}".format(i, FIELD_NAMES[i], v))
            continue
        if not math.isfinite(x):
            problems.append("[{}] {} is not finite: {!r}".format(i, FIELD_NAMES[i], v))
        values.append(x)
    if problems:
        return problems

    for i in sorted(BINARY_INDICES):
        if values[i] not in (0.0, 1.0):
            problems.append("[{}] {} must be 0 or 1, got {!r}".format(i, FIELD_NAMES[i], values[i]))
    for i in sorted(COUNT_INDICES):
        if values[i] < 0 or values[i] != int(values[i]):
            problems.append(
                "[{}] {} must be a non-negative whole number, got {!r}".format(i, FIELD_NAMES[i], values[i])
            )
    if values[0] < 0:
        problems.append("[0] velocity_ego must be >= 0, got {!r}".format(values[0]))

    first_flag = len(OBSTACLE_TYPES)
    for direction in DIRECTIONS:
        start = BLOCK_START[direction]
        has_pedestrian = values[start] == 1
        has_vulnerable = any(values[start + first_flag + k] == 1 for k in range(len(VULNERABLE_GROUPS)))
        if has_vulnerable and not has_pedestrian:
            problems.append("{} path flags a vulnerable group but has no pedestrian".format(direction))
    return problems


def check_vector(vec: Sequence[Any]) -> None:
    problems = validate_vector(vec)
    if problems:
        raise ValidationError("Invalid ael-v1 state vector:\n  " + "\n  ".join(problems))


def _check_header(doc: Any, kind: str) -> List[str]:
    if not isinstance(doc, dict):
        return ["file must contain a JSON object"]
    problems = []
    if doc.get("spec") != SPEC:
        problems.append("spec is {!r}, expected {!r}".format(doc.get("spec"), SPEC))
    if doc.get("kind") != kind:
        problems.append("kind is {!r}, expected {!r}".format(doc.get("kind"), kind))
    return problems


def validate_scenarios_doc(doc: Any) -> List[str]:
    problems = _check_header(doc, "scenarios")
    scenarios = doc.get("scenarios") if isinstance(doc, dict) else None
    if not isinstance(scenarios, dict) or not scenarios:
        return problems + ["'scenarios' must be a non-empty object of id -> vector"]
    for sid, vec in scenarios.items():
        problems += ["{}: {}".format(sid, p) for p in validate_vector(vec)]
    return problems


def validate_decisions_doc(doc: Any) -> List[str]:
    problems = _check_header(doc, "decisions")
    decisions = doc.get("decisions") if isinstance(doc, dict) else None
    if not isinstance(decisions, dict) or not decisions:
        return problems + ["'decisions' must be a non-empty object of id -> {framework: action}"]
    for sid, labels in decisions.items():
        if not isinstance(labels, dict) or not labels:
            problems.append("{}: labels must be a non-empty object".format(sid))
            continue
        for framework, action in labels.items():
            try:
                to_action(action)
            except ValueError as e:
                problems.append("{} [{}]: {}".format(sid, framework, e))
    return problems


def validate_split_doc(doc: Any) -> List[str]:
    problems = _check_header(doc, "split")
    if not isinstance(doc, dict):
        return problems
    for part in ("train", "test"):
        ids = doc.get(part)
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            problems.append("'{}' must be a list of scenario ids".format(part))
        elif len(set(ids)) != len(ids):
            problems.append("'{}' contains duplicate ids".format(part))
    if not problems:
        overlap = set(doc["train"]) & set(doc["test"])
        if overlap:
            problems.append("train and test share ids: {}".format(sorted(overlap)))
    return problems


_VALIDATORS = {
    "scenarios": validate_scenarios_doc,
    "decisions": validate_decisions_doc,
    "split": validate_split_doc,
}


def validate_doc(doc: Any) -> List[str]:
    """Validate a parsed data file; its "kind" field picks the format."""
    kind = doc.get("kind") if isinstance(doc, dict) else None
    if not isinstance(kind, str) or kind not in _VALIDATORS:
        return ["unknown kind {!r}; expected one of {}".format(kind, sorted(_VALIDATORS))]
    return _VALIDATORS[kind](doc)


def check_doc(doc: Any, name: str = "data") -> None:
    problems = validate_doc(doc)
    if problems:
        raise ValidationError("{} is not valid ael-v1 data:\n  ".format(name) + "\n  ".join(problems))


def validate_ids_match(scenario_ids: Any, other_ids: Any, what: str) -> List[str]:
    """Problems when a decisions/split file's ids don't line up with the scenarios."""
    scenario_ids, other_ids = set(scenario_ids), set(other_ids)
    problems = []
    if other_ids - scenario_ids:
        problems.append("{} has ids not in scenarios: {}".format(what, sorted(other_ids - scenario_ids)))
    if scenario_ids - other_ids:
        problems.append("{} is missing scenario ids: {}".format(what, sorted(scenario_ids - other_ids)))
    return problems


def load_file(path: str) -> Dict[str, Any]:
    """Read and validate a JSON data file; raises ValidationError on any problem."""
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (ValueError, UnicodeDecodeError) as e:  # JSONDecodeError is a ValueError
        raise ValidationError("{} is not valid JSON: {}".format(path, e)) from None
    check_doc(doc, path)
    return doc


def validate_file(path: str) -> List[str]:
    try:
        load_file(path)
    except ValidationError as e:
        return [str(e)]
    return []


def check_file(path: str) -> None:
    load_file(path)
