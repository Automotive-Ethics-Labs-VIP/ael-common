# Changelog

## v0.1.1 (2026-10-01)

Bug fixes from code review. The `ael-v1` layout and data are unchanged.

- Vectors and actions from numpy and torch are accepted (e.g. `check_vector(np_array)`, `to_action(np.argmax(logits))`). Before, they were rejected as "not a number".
- `split.json` is a validated file kind (`"kind": "split"`): no duplicate ids, no train/test overlap. The loaders cross-check that decision and split ids match the scenarios.
- `encode()` validates its output, so a `State` that breaks the spec can't produce a vector.
- `validate_file` returns problems for malformed JSON instead of crashing. New `validate_doc`, `check_doc` and `load_file` helpers.
- The import script validates everything before writing, so a bad source never overwrites the bundled data.
- `Path` is hashable. Datasets are parsed once per process, and the loaders return copies.

## v0.1.0 (2026-10-01)

First release of the `ael-v1` agreement.

- 40-D state vector spec in Team C's layout (the one CATA-200 and the trained Ethical Head use), with `encode`, `decode` and named indices. Indices 4–6 are named `casualties_if_*`; `num_ped_if_*` still works as an alias.
- Three actions: 0 maintain, 1 swerve_left, 2 swerve_right.
- Speed and lane position in metres per second and metres.
- Spec-stamped JSON formats for scenarios and decisions, plus a validator.
- CATA-200 dataset, labels and 160/40 split, imported from Ethical_Head.
