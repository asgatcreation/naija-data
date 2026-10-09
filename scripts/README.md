# Scripts

`data/` is the source of truth. These scripts built it from upstream sources and can rebuild it
to audit against fresh downloads. Corrections should normally be made directly in `data/*.csv`
with a source (see CONTRIBUTING.md). Re-running an import overwrites manual edits, so compare
with `git diff` afterwards.

## Validate (what CI runs)

```bash
pip install -r requirements-dev.txt
python scripts/validate.py
python -m pytest -q
```

## Rebuild from sources

```bash
pip install -r requirements-import.txt
python scripts/fetch/sources.py          # COD-AB, geoBoundaries, NCC, CBN (+ manifest with SHA-256)
python scripts/fetch/inec_cvr.py         # INEC live state/LGA/ward lists (~811 requests, ~15 min)
python scripts/extract/inec_2015_pdf.py  # needs the archived PDFs in .cache/raw/wayback-inec/
python scripts/extract/constitution.py   # needs .cache/raw/constitution/constitution.pdf
python scripts/build/import_admin.py     # -> data/states.csv, lgas.csv, wards.csv
python scripts/build/import_banks.py     # -> data/banks.csv
python scripts/build/import_phone.py     # -> data/phone_prefixes.csv
python scripts/validate.py
```

Some inputs are fetched by hand because the publisher blocks scripts or the file only survives in
the Internet Archive: the INEC 2015 PDFs, the Constitution PDF, the CBN NUBAN standard, CLDR
`subdivisions/en.xml`, and the Paystack and Monnify bank lists. Their URLs are in
`data/sources.json`.
