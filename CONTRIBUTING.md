# Contributing to naija-data

Thank you for helping. Accuracy is the whole point of this project, so every data change needs a
source. A correction with a link to INEC, CBN, NCC or another official publication can be merged
quickly. A change with no source can't be accepted, even if it is right.

## Reporting wrong data (the most useful contribution)

Open a **Data correction** issue: <https://github.com/asgatcreation/naija-data/issues/new/choose>

Please include:
1. **What is wrong.** For example: "Ikeja LGA headquarters is listed as X".
2. **What it should be.**
3. **Your source.** A link to an official publication (INEC, CBN, NCC, NIPOST, a state government
   website, the Official Gazette...), and the page or section if it is a PDF. News reports are
   fine as supporting evidence but not as the only source.

Bank codes: say where you saw the code (CBN circular, NIBSS document, your bank's official site, or
a payment provider's documentation). We mark codes as `verified` only when two independent
sources agree.

## Changing the data yourself

1. Fork the repo and create a branch.
2. Edit the CSV/JSON files in `data/`. **Never edit generated files** in `packages/`, `go/` or `api/`.
   Those are rebuilt from `data/`.
3. If you used a new source, add it to `data/sources.json` with its URL, the date you retrieved it,
   and its licence. We can only use sources whose licence allows redistribution.
4. Run the checks:

   ```bash
   pip install -r requirements-dev.txt
   python scripts/validate.py
   python -m pytest -q
   ```

5. Open a pull request and fill in the checklist. CI rejects data that fails validation.

## Code contributions

- Bug reports: use the **Bug** issue template, with the package and version, a minimal example,
  and what you expected.
- Every package (Python, JS, Go) must keep the same API and return the same results. The shared
  tests in `fixtures/` check this. If you change behaviour in one language, change it in all three.
- Keep runtime dependencies at zero.

## Licensing of contributions

By contributing you agree that code is licensed under MIT and data under CC BY 4.0, as described
in [ATTRIBUTION.md](ATTRIBUTION.md). Please don't submit data copied from sources with share-alike
or non-commercial terms, such as Wikipedia or OpenStreetMap.

## Contact

Questions: [GitHub Discussions](https://github.com/asgatcreation/naija-data/discussions).
Email: asgatcreation@gmail.com. GitHub: [@asgatcreation](https://github.com/asgatcreation).

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
