# Changelog

All notable changes to the code **and the data** are recorded here.
This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: a breaking API change, or a change to record identifiers.
- **MINOR**: a new function or dataset, or added records.
- **PATCH**: bug fixes and data corrections.

## [Unreleased]

### Added
- Electoral units from INEC's Result Viewing portal: 109 senatorial districts, 360 federal constituencies
  and 990 state constituencies (`data/senatorial_districts.csv`, `federal_constituencies.csv`,
  `state_constituencies.csv`), each with INEC's code and the LGAs it covers.
- Every ward now carries its `senatorial_district`, `federal_constituency` and `state_constituency` codes,
  and `unverified_fields` (14 ward links that look wrong in INEC's data are flagged).
- Functions in Python, JavaScript (`naija-data/constituencies`) and Go: `senatorial_districts`,
  `federal_constituencies`, `state_constituencies`, `constituencies`, `get_constituency`,
  `find_constituencies`, `lga_constituencies`, `constituency_lgas`, `constituency_wards`.
- REST API: `/v1/constituencies`, `/v1/senatorial-districts`, `/v1/federal-constituencies`,
  `/v1/state-constituencies`, `/v1/constituencies/{code}/lgas|wards`, `/v1/lgas/{lga}/constituencies`.
- Playground: Senate / House of Reps / House of Assembly picker; the ward picker shows each ward's
  senatorial district and constituencies; the NUBAN checker explains phone-number wallets (OPay, PalmPay).

### Changed (data)
- LGA `senatorial_district` now comes from INEC instead of UN COD-AB. 10 LGAs move: Osisioma Ngwa
  (Abia Central), Kaga (Borno North), Biase (Cross River South), Kajuru (Kaduna Central), Kauru (Kaduna South),
  Jega (Kebbi Central), Karaye (Kano South), Offa (Kwara South), Damaturu (Yobe East), Talata Mafara
  (Zamfara West). Nasarawa districts are spelled "Nasarawa" and the FCT district is "FCT".

## [0.1.1] - 2026-10-16

### Fixed
- npm package: the `naija` command is now kept by npm 11 (the built `dist/cli.js` is marked executable),
  and CI checks the package with npm 11 before every release.

### Notes
- 0.1.1 is the first version on npm. Version 0.1.0 was published to PyPI (`naija-data`, `django-naija`) and
  tagged for Go, but its npm publish was stopped by two-factor authentication before anything was uploaded.

## [0.1.0] - 2026-10-16

### Added
- Repository scaffold, licences (MIT code, CC BY 4.0 data), contribution guide, issue and PR templates.
- Source registry `data/sources.json` with schema and validation in CI.
- Data: 37 states + FCT, 774 LGAs, 8,809 wards (registration areas), 899 financial institutions,
  51 mobile number blocks (45 prefixes), each row linked to its sources.
- JSON Schemas for every data file and validation of cross-file rules (counts, codes, parents,
  aliases, overlapping phone ranges, bank mergers).
- Fetch, extract and import scripts that rebuild the dataset from upstream sources.
- Coverage, cross-check and known-gaps report (`docs/data/coverage-and-gaps.md`).
- Python package `naija-data`, JavaScript/TypeScript package `naija-data` (ESM + CJS, wards in a
  separate `naija-data/wards` entry point) and Go module `github.com/asgatcreation/naija-data/go`,
  all generated from `data/` with the same API: states, LGAs, wards, fuzzy search, banks, NUBAN
  validation and candidate banks, phone normalisation and network lookup.
- `naija` command-line tool (Python and npm).
- 6,431 shared parity test cases run against all three packages.
- Strict phone validation in all three languages: number type (mobile, landline, 0800 toll-free,
  0700 non-toll-free), landline area, network or allottee, and a reason code when invalid
  (`parse_phone`, `phone_error`, `is_valid_phone`). Replaces `lookup_phone`.
- Data: 56 NCC landline area codes and 305 allocated number blocks (NCC Numbering Plan 2022).
- Vehicle plate format validation for standard (`ABC-123DE`) and dealer (`DKN 135 3`) plates, and plate
  colours by category, from the National Road Traffic Regulations 2012. LGA plate codes are not
  included: FRSC does not publish them (request drafted in `docs/requests/`).
- `search_wards` in Python and Go (JS: `searchWards` from `naija-data/wards`).
- Zod schemas at `naija-data/zod` (zod is an optional peer dependency).
- Public REST API (Cloudflare Worker) at https://naija-data-api.asgatcreation.workers.dev/v1 with
  OpenAPI docs, CORS, caching and rate limiting.
- Documentation website with a live playground at https://naija-data.asgatcreation.workers.dev.
- `django-naija`: Django model and form fields, DRF serializer fields and validators, example
  project and tests.

### Fixed (data)
- Removed 4 LGA headquarters taken from OCHA COD-AB that were garbled ("Jamao?Çoare") or were
  rivers ("Moro, River" for Ilorin West, "Ofu, River" for Ibaji, "Etim Ekpo, River").
- Validation now rejects text decoded with the wrong encoding.
