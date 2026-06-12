# AGENTS.md

## Cursor Cloud specific instructions

This is a pure Python 3.10+ project (verified on Python 3.12) with **no third-party
dependencies** — standard library only. There is nothing to `pip install`, and there
is no virtualenv, lockfile, or build step.

Services / entry points (run from the repo root):

- Run the app (one full journey through both engines + firewall + ceremony):
  - `python3 -m recovering_player` (default seed)
  - `python3 -m recovering_player 99` (alternate seed; governance is identical)
- Run the test suite (26 doctrine tests):
  - `python3 -m unittest discover -s tests`

Notes:

- There is no configured linter (no `pyproject.toml`, `.flake8`, `ruff`, etc.). Lint
  is effectively N/A; rely on the `unittest` suite for verification.
- The progression track (`progression_track.py`) is intentionally pure: it imports no
  randomness, clocks, or I/O, and an AST test in `tests/test_governance.py` enforces
  this. Adding such imports there will fail tests by design.
