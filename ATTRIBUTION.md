# Attribution and licensing

## Two licences

| What | Licence | File |
|---|---|---|
| Source code (packages, scripts, API, docs site) | MIT | [LICENSE](LICENSE) |
| The compiled dataset (everything in `data/` and the data files generated from it) | CC BY 4.0 | [LICENSE-DATA](LICENSE-DATA) |

Copyright (c) 2026 Akanji Oluwaseun Gabriel.

## How to credit the dataset

> Nigerian reference data from naija-data by Akanji Oluwaseun Gabriel
> (https://github.com/asgatcreation/naija-data), licensed CC BY 4.0,
> compiled from INEC, OCHA/OSGOF, geoBoundaries/GRID3, CBN and NCC sources.

## Upstream sources

The machine-readable list, including the date each source was retrieved, is
[`data/sources.json`](data/sources.json). Every data row says which sources it came from.

| Source | Publisher | Licence / terms | Used for |
|---|---|---|---|
| Constitution of the Federal Republic of Nigeria 1999, First Schedule | Federal Government of Nigeria | Public law | Canonical state and LGA names |
| Nigeria Subnational Administrative Boundaries (COD-AB) | OCHA, from OSGOF, eHealth Africa, UN Cartographic Section | CC BY-IGO 3.0 | P-codes, cross-checks |
| geoBoundaries gbOpen NGA ADM1/ADM2 | William & Mary geoLab, from GRID3 (2022) | CC BY 4.0 | Boundaries, centroid coordinates |
| Polling Unit Directories and polling unit statistics | Independent National Electoral Commission (INEC) | Public government publications (factual data only) | Wards / registration areas |
| INEC LGA and Wards | OCHA Nigeria / INEC | CC0 | Ward cross-check |
| Lists of licensed financial institutions | Central Bank of Nigeria (CBN) | Public regulatory information (factual data only) | Bank names, types, status |
| Revised Standards on NUBAN (2020) | Central Bank of Nigeria | Public standard | NUBAN algorithm |
| Mobile Number Allocation Table | Nigerian Communications Commission (NCC) | Public regulatory information (factual data only) | Phone prefixes |
| National Digital Alphanumeric Postcode System | NIPOST | Not redistributable; only the published format is described | Postcode format check |

Where a source publishes no open licence, naija-data only uses plain facts from it, such as names,
codes and prefixes, and never copies its documents or text. If you are a rights holder and object
to how your data is used, please open an issue or email the maintainer.

## Deliberately not used

- **GRID3 Operational Wards** (CC BY-SA). The share-alike licence would pass on to our files, and
  the boundaries cover only 24 states.
- **OpenStreetMap** (ODbL) and **Wikipedia** (CC BY-SA). Both have share-alike terms.
- **NIPOST postcode records.** They are only available through a gated API with no open licence.
