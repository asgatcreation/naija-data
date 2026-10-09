## What this changes

<!-- One or two sentences. Link the issue it fixes, e.g. "Fixes #12". -->

## Type

- [ ] Data correction
- [ ] New data
- [ ] Bug fix
- [ ] Feature / docs / tooling

## Checklist

- [ ] Data changes are only in `data/`. No generated files were edited by hand.
- [ ] Every new or changed data row has a source in `data/sources.json` (URL, retrieved date, licence).
- [ ] The source's licence allows redistribution (no share-alike or non-commercial terms).
- [ ] `python scripts/validate.py` passes.
- [ ] Tests pass (`python -m pytest -q`, plus the package tests if code changed).
- [ ] If behaviour changed, it changed in Python, JS **and** Go, and the shared fixtures were updated.
- [ ] `CHANGELOG.md` has an entry under "Unreleased".

## Sources

<!-- Links to the official documents that back this change. -->
