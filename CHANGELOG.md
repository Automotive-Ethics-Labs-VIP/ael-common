# Changelog

## v0.1.0 (2026-10-01)

First release of the `ael-v1` agreement.

- 40-D state vector spec in Team C's layout (the one CATA-200 and the trained Ethical Head use), with `encode`, `decode` and named indices. Indices 4–6 are named `casualties_if_*`; `num_ped_if_*` still works as an alias.
- Three actions: 0 maintain, 1 swerve_left, 2 swerve_right.
- Speed and lane position in metres per second and metres.
- Spec-stamped JSON formats for scenarios and decisions, plus a validator.
- CATA-200 dataset, labels and 160/40 split, imported from Ethical_Head.
