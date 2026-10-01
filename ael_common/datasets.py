"""Bundled datasets.

CATA-200: the 200 hand-written Category A crash scenarios (Team C), their
utilitarian and Kantian labels, and the 160/40 train/test split used for the
Spring 2026 paper. Imported from Ethical_Head/data by scripts/import_cata_200.py.
"""

import copy
import functools
import os
from typing import Any, Dict, List

from .actions import Action, to_action
from .validate import ValidationError, load_file, validate_ids_match

_DIR = os.path.join(os.path.dirname(__file__), "data", "cata_200")


@functools.lru_cache(maxsize=None)
def _cata_200() -> Dict[str, Any]:
    """Load, validate and cross-check all three files once per process."""
    scenarios = load_file(os.path.join(_DIR, "scenarios.json"))["scenarios"]
    decisions = load_file(os.path.join(_DIR, "decisions.json"))["decisions"]
    split = load_file(os.path.join(_DIR, "split.json"))
    problems = validate_ids_match(scenarios, decisions, "decisions.json")
    problems += validate_ids_match(scenarios, split["train"] + split["test"], "split.json")
    if problems:
        raise ValidationError("CATA-200 files disagree:\n  " + "\n  ".join(problems))
    return {"scenarios": scenarios, "decisions": decisions, "split": split}


def load_cata_200() -> Dict[str, List[float]]:
    """Scenario id -> 40-D ael-v1 vector."""
    return copy.deepcopy(_cata_200()["scenarios"])


def load_cata_200_labels() -> Dict[str, Dict[str, Action]]:
    """Scenario id -> {"utilitarian": Action, "kantian": Action}."""
    decisions = _cata_200()["decisions"]
    return {sid: {fw: to_action(a) for fw, a in labels.items()} for sid, labels in decisions.items()}


def load_cata_200_split() -> Dict[str, List[str]]:
    """{"train": [ids...], "test": [ids...]}."""
    split = _cata_200()["split"]
    return {"train": list(split["train"]), "test": list(split["test"])}
