"""Bundled datasets.

CATA-200: the 200 hand-written Category A crash scenarios (Team C), their
utilitarian and Kantian labels, and the 160/40 train/test split used for the
Spring 2026 paper. Imported from Ethical_Head/data by scripts/import_cata_200.py.
"""

import json
import os
from typing import Dict, List

from .actions import Action, to_action
from .validate import check_file

_DIR = os.path.join(os.path.dirname(__file__), "data", "cata_200")


def _load(name: str) -> dict:
    path = os.path.join(_DIR, name)
    check_file(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_cata_200() -> Dict[str, List[float]]:
    """Scenario id -> 40-D ael-v1 vector."""
    return _load("scenarios.json")["scenarios"]


def load_cata_200_labels() -> Dict[str, Dict[str, Action]]:
    """Scenario id -> {"utilitarian": Action, "kantian": Action}."""
    decisions = _load("decisions.json")["decisions"]
    return {sid: {fw: to_action(a) for fw, a in labels.items()} for sid, labels in decisions.items()}


def load_cata_200_split() -> Dict[str, List[str]]:
    """{"train": [ids...], "test": [ids...]}."""
    with open(os.path.join(_DIR, "split.json"), encoding="utf-8") as f:
        doc = json.load(f)
    return {"train": doc["train"], "test": doc["test"]}
