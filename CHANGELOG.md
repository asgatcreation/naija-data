# Changelog

All notable changes to the code **and the data** are recorded here.
This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: a breaking API change, or a change to record identifiers.
- **MINOR**: a new function or dataset, or added records.
- **PATCH**: bug fixes and data corrections.

## [Unreleased]

### Added
- Repository scaffold, licences (MIT code, CC BY 4.0 data), contribution guide, issue and PR templates.
- Source registry `data/sources.json` with schema and validation in CI.
- Data: 37 states + FCT, 774 LGAs, 8,809 wards (registration areas), 899 financial institutions,
  51 mobile number blocks (45 prefixes), each row linked to its sources.
- JSON Schemas for every data file and validation of cross-file rules (counts, codes, parents,
  aliases, overlapping phone ranges, bank mergers).
- Fetch, extract and import scripts that rebuild the dataset from upstream sources.
- Coverage, cross-check and known-gaps report (`docs/data/coverage-and-gaps.md`).
