# Working in ael-common

Instructions for AI coding agents (and people) changing this repo. Read README.md first for what the package is.

## What this repo is

The lab's data contract. Other repos (AEL_CARLA, Ethical_Head) pin a tagged version and trust it. A mistake here spreads silently into training data, so correctness beats speed and scope stays small.

## Hard rules

1. **Never change the meaning of an existing spec in place.** The field order, field meanings, units and action IDs of `ael-v1` are frozen. A change to any of them is a new spec (`ael-v2`), added alongside v1 with its own tests. If a task seems to need a v1 change, stop and ask the maintainer.
2. **Don't hand-edit `ael_common/data/`.** Regenerate it with `python scripts/import_cata_200.py ../Ethical_Head`, then confirm `git diff` shows only the changes you expect.
3. **No runtime dependencies.** The package uses the standard library only. numpy, torch and hypothesis may appear in tests, guarded with `pytest.importorskip`.
4. **Stay Python 3.8-compatible** (it has to install next to the CARLA 0.9.13 client): no walrus operator, no `match`, no `list[int]`-style annotations at runtime, no `str.removeprefix`.
5. **Every behaviour change ships with a test**, including the rejection path. Keep `ael_common/` at 100% line and branch coverage.
6. **Don't add AI attribution** (Co-Authored-By trailers, "Generated with" lines) to commits or PRs.

## Before you finish

```bash
python -m pytest -q
```

All tests must pass. If you touched `ael_common/`, also check coverage and the 3.8 floor:

```bash
coverage run --branch --source=ael_common -m pytest -q && coverage report -m
uv venv --python 3.8 .venv38 && uv pip install --python .venv38 pytest . && .venv38/Scripts/python -m pytest -q
```

## Releasing

- **Bug fixes and docs** that don't change what data means: commit to `main`, bump the patch version (`0.1.x`) in `pyproject.toml` and `ael_common/__init__.py`, add a CHANGELOG entry, tag `v0.1.x`.
- **Anything that changes the agreement** (new spec version, new file kind, new action, new dataset): open a PR so the other teams see it, bump the minor version, and update the README tables.
- Never move or delete a tag. Other repos pin them.

## Layout

| Path | What it is |
|---|---|
| `ael_common/state_vector.py` | The ael-v1 layout, `State` / `Path`, `encode` / `decode` |
| `ael_common/actions.py` | Action IDs, `to_action` |
| `ael_common/validate.py` | Vector and file validators |
| `ael_common/datasets.py` | Loaders for bundled data |
| `ael_common/data/cata_200/` | Generated. Don't hand-edit |
| `scripts/import_cata_200.py` | Rebuilds the bundled CATA-200 files |
| `tests/` | Unit, error-path and property-based tests |
