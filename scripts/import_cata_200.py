"""Import CATA-200 from an Ethical_Head checkout into ael_common/data/cata_200/.

Usage:
    python scripts/import_cata_200.py ../Ethical_Head

Reads data/scenarios_200.json, data/decisions_200.json and
data/splits/train_test_split.json, wraps them in the ael-v1 file format,
and validates the result. Re-run only if the source data changes.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from ael_common.state_vector import SPEC  # noqa: E402
from ael_common.validate import check_file  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "ael_common", "data", "cata_200")
SOURCE_NOTE = "Team C CATA scenarios (corrected vectors), imported from Ethical_Head/data"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(name, doc):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    return path


def main(ethical_head):
    data = os.path.join(ethical_head, "data")
    scenarios = _read(os.path.join(data, "scenarios_200.json"))
    decisions = _read(os.path.join(data, "decisions_200.json"))
    split = _read(os.path.join(data, "splits", "train_test_split.json"))

    ids = sorted(scenarios)
    os.makedirs(OUT, exist_ok=True)
    written = [
        _write("scenarios.json", {
            "spec": SPEC,
            "kind": "scenarios",
            "source": SOURCE_NOTE,
            "scenarios": {sid: scenarios[sid] for sid in ids},
        }),
        _write("decisions.json", {
            "spec": SPEC,
            "kind": "decisions",
            "source": SOURCE_NOTE,
            "decisions": {sid: decisions[sid] for sid in ids},
        }),
    ]
    _write("split.json", {
        "spec": SPEC,
        "kind": "split",
        "train": sorted(split["train"]["scenarios"]),
        "test": sorted(split["test"]["scenarios"]),
    })
    for path in written:
        check_file(path)
    print("Wrote {} scenarios to {}".format(len(ids), OUT))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
