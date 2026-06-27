# DEPENDENCIES Fix Plan

## Changes

- `requirements.txt` — Pin all packages to exact versions matching the current installed environment.

## New files

None.

## Verification goals

- [ ] Every line in `requirements.txt` has `==X.Y.Z` (no bare package names, no `>=`, no `~=`)
- [ ] `pip install -r requirements.txt` on a clean venv installs exactly the pinned versions with no resolver conflicts
- [ ] `pip check` reports no dependency conflicts

## Manual verification (for the human)

- Create a fresh venv, run `pip install -r requirements.txt`, confirm all packages install cleanly at the pinned versions
- Run `python main.py` and verify the app works normally after the pinned install
