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
python scripts/fetch/inec_irev.py        # INEC IReV: senatorial districts, constituencies, ward links (~150 requests)
python scripts/extract/inec_2015_pdf.py  # needs the archived PDFs in .cache/raw/wayback-inec/
python scripts/extract/constitution.py   # needs .cache/raw/constitution/constitution.pdf
python scripts/build/import_admin.py     # -> data/states.csv, lgas.csv, wards.csv
python scripts/build/import_electoral.py # -> data/senatorial_districts.csv, federal_ and state_constituencies.csv;
                                         #    adds the electoral links to wards.csv and lgas.csv (run after import_admin)
python scripts/build/import_banks.py     # -> data/banks.csv
python scripts/build/import_phone.py     # -> data/phone_prefixes.csv
python scripts/build/import_numbering.py # -> data/phone_area_codes.csv, data/phone_number_blocks.csv
python scripts/validate.py
```

Some inputs are fetched by hand because the publisher blocks scripts or the file only survives in
the Internet Archive: the INEC 2015 PDFs, the Constitution PDF, the CBN NUBAN standard, CLDR
`subdivisions/en.xml`, and the Paystack and Monnify bank lists. Their URLs are in
`data/sources.json`.

## Generate the packages' data and the parity fixtures

```bash
python scripts/build/generate.py        # data/*.csv -> JSON inside the Python, JS and Go packages
python scripts/build/make_fixtures.py   # fixtures/parity.json (shared cross-language test cases)
python scripts/build/gen_go_fold.py     # go/fold_table.go (accent folding for Go)
```

CI runs `generate.py --check` and `make_fixtures.py --check` and fails if either is out of date.
