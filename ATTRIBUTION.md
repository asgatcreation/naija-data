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
| CVR polling unit locator (live lists) | Independent National Electoral Commission (INEC) | Public government information (factual data only) | State/LGA/ward codes and names |
| Directory of Polling Units, Jan 2015 (Internet Archive copies) | INEC | Public government publication (factual data only) | Ward cross-check, aliases |
| Constitution of the Federal Republic of Nigeria 1999, First Schedule | Federal Republic of Nigeria | Public law | Capitals, FCT council HQs, legal totals, aliases |
| Nigeria Subnational Administrative Boundaries (COD-AB) | OCHA, from OSGOF, eHealth Africa, UN Cartographic Section | CC BY-IGO 3.0 | P-codes, centroids, senatorial districts, LGA HQs |
| geoBoundaries gbOpen NGA ADM1/ADM2 | William & Mary geoLab, from GRID3 (2022) | CC BY 4.0 | Optional boundaries package |
| CLDR subdivisions | Unicode Consortium | Unicode License v3 | ISO 3166-2 state codes |
| Country Guidance: Nigeria (2021) | European Union Agency for Asylum | Reuse authorised with acknowledgement (factual data only) | Geopolitical zones |
| State creation dates article | BusinessDay Nigeria | Factual data only | State creation dates (unverified) |
| Lists of licensed financial institutions | Central Bank of Nigeria (CBN) | Public regulatory information (factual data only) | Bank names, types, status |
| Revised Standards on NUBAN | Central Bank of Nigeria | Public standard | NUBAN algorithm |
| Public bank lists | Paystack, Monnify | Public API responses (factual data only) | Bank codes, USSD codes |
| Heritage Bank revocation press release | CBN | Public | Bank status history |
| Access–Diamond merger reports | Nairametrics, TheCable | Factual data only | Bank status history |
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
