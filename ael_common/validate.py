"""Check vectors and data files against the ael-v1 agreement.

validate_* functions return a list of problems (empty means valid).
check_* functions raise ValidationError instead.
"""

import json
import math
from typing import Any, Dict, List, Sequence

from .actions import to_action
from .state_vector import (
    BINARY_INDICES,
    BLOCK_START,
    COUNT_INDICES,
    DIM,
    DIRECTIONS,
    FIELD_NAMES,
    OBSTACLE_TYPES,
    SPEC,
)


class ValidationError(ValueError):
    pass


def validate_vector(vec: Sequence[Any]) -> List[str]:
    problems = []  # type: List[str]
    try:
        n = len(vec)
    except TypeError:
        return ["vector must be a sequence, got {}".format(type(vec).__name__)]
    if n != DIM:
        return ["vector has {} values, expected {}".format(n, DIM)]

    for i, v in enumerate(vec):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            problems.append("[{}] {} is not a number: {!r}".format(i, FIELD_NAMES[i], v))
        elif not math.isfinite(v):
            problems.append("[{}] {} is not finite: {!r}".format(i, FIELD_NAMES[i], v))
    if problems:
        return problems

    for i in sorted(BINARY_INDICES):
        if vec[i] not in (0, 1):
            problems.append("[{}] {} must be 0 or 1, got {!r}".format(i, FIELD_NAMES[i], vec[i]))
    for i in sorted(COUNT_INDICES):
        if vec[i] < 0 or vec[i] != int(vec[i]):
            problems.append(
                "[{}] {} must be a non-negative whole number, got {!r}".format(i, FIELD_NAMES[i], vec[i])
            )
    if vec[0] < 0:
        problems.append("[0] velocity_ego must be >= 0, got {!r}".format(vec[0]))

    n_types = len(OBSTACLE_TYPES)
    for direction in DIRECTIONS:
        start = BLOCK_START[direction]
        has_pedestrian = vec[start] == 1
        has_vulnerable = any(vec[start + n_types + k] == 1 for k in range(4))
        if has_vulnerable and not has_pedestrian:
            problems.append(
                "{} path flags a vulnerable group but has no pedestrian".format(direction)
            )
    return problems


def check_vector(vec: Sequence[Any]) -> None:
    problems = validate_vector(vec)
    if problems:
        raise ValidationError("Invalid ael-v1 state vector:\n  " + "\n  ".join(problems))


def _check_spec(doc: Dict[str, Any], kind: str) -> List[str]:
    if not isinstance(doc, dict):
        return ["file must contain a JSON object"]
    problems = []
    if doc.get("spec") != SPEC:
        problems.append("spec is {!r}, expected {!r}".format(doc.get("spec"), SPEC))
    if doc.get("kind") != kind:
        problems.append("kind is {!r}, expected {!r}".format(doc.get("kind"), kind))
    return problems


def validate_scenarios_doc(doc: Dict[str, Any]) -> List[str]:
    problems = _check_spec(doc, "scenarios")
    scenarios = doc.get("scenarios") if isinstance(doc, dict) else None
    if not isinstance(scenarios, dict) or not scenarios:
        return problems + ["'scenarios' must be a non-empty object of id -> vector"]
    for sid, vec in scenarios.items():
        problems += ["{}: {}".format(sid, p) for p in validate_vector(vec)]
    return problems


def validate_decisions_doc(doc: Dict[str, Any]) -> List[str]:
    problems = _check_spec(doc, "decisions")
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


_VALIDATORS = {"scenarios": validate_scenarios_doc, "decisions": validate_decisions_doc}


def validate_file(path: str) -> List[str]:
    """Validate a JSON data file; its "kind" field picks the format."""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    kind = doc.get("kind") if isinstance(doc, dict) else None
    if kind not in _VALIDATORS:
        return ["unknown kind {!r}; expected one of {}".format(kind, sorted(_VALIDATORS))]
    return _VALIDATORS[kind](doc)


def check_file(path: str) -> None:
    problems = validate_file(path)
    if problems:
        raise ValidationError("{} is not valid ael-v1 data:\n  ".format(path) + "\n  ".join(problems))
