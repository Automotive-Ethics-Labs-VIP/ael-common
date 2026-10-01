# ael-common

The Automotive Ethics Lab's shared data agreement. Every AEL repo reads and writes data through this package, so a vector produced in CARLA (Team B) means exactly the same thing when the Ethical Head (Team A) trains on it.

It holds:

- **The state vector spec**: what each of the 40 numbers means, with `encode` / `decode` helpers
- **Action IDs**: the one set of actions every repo uses
- **File formats** for scenarios and decisions, stamped with a spec version
- **A validator** that rejects wrong layouts, wrong action IDs and files from another spec version
- **CATA-200**: the 200 hand-written crash scenarios with utilitarian and Kantian labels and the 160/40 train/test split

Current spec: **`ael-v1`**. No dependencies; Python 3.7+ (so it installs alongside the CARLA 0.9.13 client).

## Install

Pin a version tag:

```bash
pip install "git+https://github.com/Automotive-Ethics-Labs-VIP/ael-common@v0.1.0"
```

For development:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## Usage

Build a vector from what's in each path instead of placing numbers by hand:

```python
from ael_common import Path, State, encode, decode, Action, check_vector

state = State(
    num_passengers=1,
    casualties={"straight": 1, "left": 2, "right": 1},
    paths={
        "left": Path(["pedestrian"], ["child", "elderly"]),
        "straight": Path(["pedestrian"]),
        "right": Path(["barrier"]),
    },
)
vec = encode(state)        # 40 floats in the ael-v1 layout
check_vector(vec)          # raises ValidationError if anything is off
decode(vec).paths["left"]  # Path(obstacles=['pedestrian'], vulnerable=['child', 'elderly'])
```

Load the bundled dataset:

```python
from ael_common import load_cata_200, load_cata_200_labels, load_cata_200_split

vectors = load_cata_200()          # {"CATA_S001": [...40 numbers...], ...}
labels = load_cata_200_labels()    # {"CATA_S001": {"utilitarian": Action.MAINTAIN, "kantian": ...}}
split = load_cata_200_split()      # {"train": [160 ids], "test": [40 ids]}
```

Check a data file from the command line:

```bash
python -c "from ael_common import check_file; check_file('my_scenarios.json')"
```

## The ael-v1 state vector

| Index | Field | Notes |
|---|---|---|
| 0 | `velocity_ego` | m/s. Always 10 in CATA-200 |
| 1 | `num_passengers` | Occupants of the ego vehicle |
| 2 | `lane_position` | Lateral offset from lane centre, m. Always 0 in CATA-200 |
| 3 | `velocity_delta` | m/s. Always 0 in CATA-200 |
| 4 | `casualties_if_straight` | People killed if the vehicle maintains course |
| 5 | `casualties_if_left` | People killed if it swerves left |
| 6 | `casualties_if_right` | People killed if it swerves right |
| 7–17 | **left** path block | 11 binary slots, below |
| 18–28 | **straight** path block | |
| 29–39 | **right** path block | |

Each path block, in order: `pedestrian, cyclist, vehicle, truck, motorcycle, barrier, property, is_child, is_elderly, is_pregnant, is_disabled`. All are 0/1 presence flags, not counts. The four `is_*` flags describe pedestrians in that path.

**Watch out:**

- The casualty counts (4–6) run straight, left, right. The path blocks (7–39) run left, straight, right. Use `index("right_barrier")` or `encode` rather than hard-coding positions.
- Casualties include the ego vehicle's passengers when a path ends in a barrier.
- Older docs call indices 4–6 `num_ped_if_*`. `index()` still accepts those names.

## Actions

| ID | Name | Path taken |
|---|---|---|
| 0 | `maintain` | straight. Means hand control back to the normal controller, not "drive on regardless" |
| 1 | `swerve_left` | left |
| 2 | `swerve_right` | right |

The 5-action IDs in older Ethical_Head code (brake_hard, accelerate) are not part of v1. `to_action()` rejects them.

## File formats

Every data file is a JSON object with `"spec"` and `"kind"`:

```json
{"spec": "ael-v1", "kind": "scenarios", "scenarios": {"CATA_S001": [10, 1, 0, 0, 1, 2, 1, ...]}}
{"spec": "ael-v1", "kind": "decisions", "decisions": {"CATA_S001": {"utilitarian": 0, "kantian": 0}}}
```

`validate_file` / `check_file` reject a file whose spec or kind doesn't match.

## Facts about CATA-200 worth knowing

The tests pin these down:

- Utilitarian labels are 60 maintain / 100 left / 40 right, and every one is the fewest-casualties action (ties: maintain, then left, then right).
- Kantian labels are "maintain" in all 200 scenarios, so Kantian accuracy on this dataset is trivially 100%.
- Every right path is a barrier; speed, lane position and speed change never vary. A model trained only on CATA-200 has never seen those vary.

## Changing the agreement

1. Open a pull request here. Never change the meaning of a field in place.
2. A new or changed layout gets a new spec version (`ael-v2`), added alongside v1, and a new release tag.
3. Each repo upgrades its pinned version on purpose.

What lives where:

- **In this repo:** definitions, validators, and small canonical datasets like CATA-200.
- **Not in git:** generated data (CARLA runs, trajectory pairs, human preference votes, checkpoints). Keep it in shared storage, and stamp each file with its `spec` so it can be validated later.

To re-import CATA-200 from Ethical_Head:

```bash
python scripts/import_cata_200.py ../Ethical_Head
```
