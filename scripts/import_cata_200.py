"""Import CATA-200 from an Ethical_Head checkout into ael_common/data/cata_200/.

Usage:
    python scripts/import_cata_200.py ../Ethical_Head

Reads data/scenarios_200.json, data/decisions_200.json and
data/splits/train_test_split.json, wraps them in the ael-v1 file format, and
validates everything before writing. If anything is wrong, nothing is written.
Re-run only if the source data changes.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from ael_common.state_vector import SPEC  # noqa: E402
from ael_common.validate import ValidationError, validate_doc, validate_ids_match  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "ael_common", "data", "cata_200")
SOURCE_NOTE = "Team C CATA scenarios (corrected vectors), imported from Ethical_Head/data"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_docs(ethical_head):
    """Read the source files and return {filename: doc}. Raises ValidationError."""
    data = os.path.join(ethical_head, "data")
    scenarios = _read(os.path.join(data, "scenarios_200.json"))
    decisions = _read(os.path.join(data, "decisions_200.json"))
    split = _read(os.path.join(data, "splits", "train_test_split.json"))
    train = sorted(split["train"]["scenarios"])
    test = sorted(split["test"]["scenarios"])

    problems = validate_ids_match(scenarios, decisions, "decisions_200.json")
    problems += validate_ids_match(scenarios, train + test, "train_test_split.json")
    if problems:
        raise ValidationError("Source files disagree:\n  " + "\n  ".join(problems))

    ids = sorted(scenarios)
    docs = {
        "scenarios.json": {
            "spec": SPEC,
            "kind": "scenarios",
            "source": SOURCE_NOTE,
            "scenarios": {sid: scenarios[sid] for sid in ids},
        },
        "decisions.json": {
            "spec": SPEC,
            "kind": "decisions",
            "source": SOURCE_NOTE,
            "decisions": {sid: decisions[sid] for sid in ids},
        },
        "split.json": {"spec": SPEC, "kind": "split", "train": train, "test": test},
    }
    for name, doc in docs.items():
        problems += ["{}: {}".format(name, p) for p in validate_doc(doc)]
    if problems:
        raise ValidationError("Source data is not valid ael-v1:\n  " + "\n  ".join(problems))
    return docs


def main(ethical_head, out=OUT):
    docs = build_docs(ethical_head)  # validates everything before touching disk
    os.makedirs(out, exist_ok=True)
    for name, doc in docs.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
            f.write("\n")
    print("Wrote {} scenarios to {}".format(len(docs["scenarios.json"]["scenarios"]), out))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
