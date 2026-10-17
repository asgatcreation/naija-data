# naija-data

**Accurate, sourced, open Nigerian reference data (states, LGAs, wards, senatorial districts and
constituencies, banks, phone numbers, plates) for
Python, JavaScript/TypeScript and Go, plus a free REST API.**

[![CI](https://github.com/asgatcreation/naija-data/actions/workflows/ci.yml/badge.svg)](https://github.com/asgatcreation/naija-data/actions/workflows/ci.yml)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)

> 🚧 **Pre-release (0.x).** The packages are on PyPI, npm and the Go proxy and are fully tested; the API
> may still change before v1.0.0.

**Website and playground:** https://naija-data.asgatcreation.workers.dev ·
**REST API:** https://naija-data-api.asgatcreation.workers.dev/v1 ([interactive docs](https://naija-data-api.asgatcreation.workers.dev/v1/docs))

```bash
curl https://naija-data-api.asgatcreation.workers.dev/v1/states/lagos/lgas
```

## Install and use

**Python** (3.9+, no dependencies)

```bash
pip install naija-data
```

```python
import naija_data as ng

ng.get_state("lagos").capital           # 'Ikeja'
ng.search("lagso")[0].name              # 'Lagos'  (typos, aliases, accents: "Ọ̀yọ́")
ng.is_valid_nuban("0000014579", "011")  # True
ng.parse_phone("01 269 1531").area      # 'Lagos' (strict NCC rules: mobile, landline, toll-free)
ng.phone_error("0900 123 4567")         # 'reserved'
[u.name for u in ng.lga_constituencies("Ikeja", "Lagos")]  # ['Lagos West', 'Ikeja', 'Ikeja I', 'Ikeja II']
```

**JavaScript / TypeScript** (ESM + CommonJS, full types, no dependencies)

```bash
npm install naija-data
```

```ts
import { getState, search, isValidNuban } from "naija-data";
import { wards } from "naija-data/wards";
import { federalConstituencies } from "naija-data/constituencies";

getState("lagos")?.capital;             // "Ikeja"
wards("Ikeja", "Lagos").length;         // 10
federalConstituencies("Lagos").length;  // 24
```

**Go** (no dependencies, data embedded)

```bash
go get github.com/asgatcreation/naija-data/go
```

```go
naija.GetState("lagos").Capital                 // "Ikeja"
ok, _ := naija.IsValidNUBAN("0000014579", "011") // true
```

**Command line**: `naija lga lagos`, `naija constituencies ikeja --state lagos`, `naija bank 058`, `naija nuban 0000014579`, `naija phone 08031234567`,
`naija plate KJA 123 AB`.

**Django / DRF**: [`django-naija`](packages/django/) adds model, form and serializer fields
(`NigerianPhoneField`, `NUBANField`, `PlateNumberField`, `StateField`, `LGAField`) with clear error messages.
**Zod**: `import { phoneSchema, nubanSchema, plateSchema } from "naija-data/zod"`.

### What's included

| | Python | JavaScript | Go |
|---|---|---|---|
| States, LGAs, wards: list and look up by code, slug, name or alias | `get_state`, `lgas`, `get_lga`, `wards` | `getState`, `lgas`, `getLga`, `wards` | `GetState`, `LGAs`, `GetLGA`, `Wards` |
| Senatorial districts, federal and state constituencies (INEC), the units of an LGA or ward, and the wards of a unit | `senatorial_districts`, `federal_constituencies`, `state_constituencies`, `lga_constituencies`, `constituency_wards` | same names in camelCase, from `naija-data/constituencies` | `SenatorialDistricts`, `FederalConstituencies`, `StateConstituencies`, `LGAConstituencies`, `ConstituencyWards` |
| Fuzzy search (typos, aliases, accents) | `search` | `search`, `searchWards` | `Search`, `SearchWards` |
| Banks by code, name or type; active only by default | `get_bank`, `banks`, `find_banks` | `getBank`, `banks`, `findBanks` | `GetBank`, `Banks`, `FindBanks` |
| NUBAN check digit (CBN algorithm) and candidate banks | `is_valid_nuban`, `banks_for_nuban` | `isValidNuban`, `banksForNuban` | `IsValidNUBAN`, `BanksForNUBAN` |
| Strict phone validation: type (mobile, landline, toll-free), area, network, reason when invalid | `parse_phone`, `phone_error`, `is_valid_phone` | `parsePhone`, `phoneError`, `isValidPhone` | `ParsePhone`, `PhoneError`, `IsValidPhone` |
| Vehicle plate format validation (standard and dealer plates) | `parse_plate`, `plate_error` | `parsePlate`, `plateError` | `ParsePlate`, `PlateError` |

Record fields keep the dataset's names in every language (`state.iso_code`, `bank.cbn_code`).
JavaScript bundle cost (gzipped): states 2.3 KB, plates 2.4 KB, phone validation 4.9 KB, banks + NUBAN 15 KB,
states + LGAs + search 30 KB; wards (148 KB) and constituencies (66 KB, including LGAs) only load if you import
`naija-data/wards` or `naija-data/constituencies`.

**Same answers in every language.** 13,392 shared test cases ([fixtures/](fixtures/)) run against the
Python, JavaScript and Go packages in CI, down to the fuzzy-search scores.

## Why

Nigerian developers often copy state and LGA lists from old gists that are outdated, have typos
and give no source. naija-data aims to be the trusted alternative:

- **Every record has a source.** The publisher, URL, retrieval date and licence are recorded in
  [`data/sources.json`](data/sources.json).
- **Nothing is guessed.** Anything we can't verify is marked `unverified` or left out, and the gaps
  are listed publicly.
- **Validated in CI.** Schema checks, unique codes, expected counts (36 states + FCT, 774 LGAs,
  8,809 registration areas, 109 senatorial districts, 360 federal constituencies).
- **One dataset, three languages.** The Python, JS and Go packages are generated from the same data,
  and shared tests check that they return identical results.

## Coverage

| Dataset | Rows | Main sources | Status |
|---|---|---|---|
| States + FCT | 37 | INEC, Constitution, OCHA COD-AB, Unicode CLDR | ✅ data ready |
| LGAs (incl. 6 FCT area councils) | 774 | INEC, Constitution, OCHA COD-AB | ✅ data ready |
| Wards / registration areas | 8,809 | INEC (live list + 2015 directory) | ✅ data ready |
| Senatorial districts / federal constituencies / state constituencies | 109 / 360 / 990 | INEC Result Viewing portal (IReV) | ✅ every ward linked; INEC lists 990 state constituencies, not the often-quoted 993 |
| Banks and licensed financial institutions | 899 | CBN register; codes from Paystack + Monnify | ✅ data ready, codes partial |
| Mobile number prefixes | 45 | NCC Mobile Number Allocation Table | ✅ |
| Landline area codes and allocated number blocks | 56 codes, 305 blocks | NCC Numbering Plan 2022 | ✅ |
| Vehicle plate formats and colours | 13 categories | National Road Traffic Regulations 2012 | ✅ format only; LGA codes not published by FRSC |
| Postcode format check | – | NIPOST (records are not redistributable) | planned |

The cross-checks between sources, the upstream errors they caught, and the known gaps are documented in
[docs/data/coverage-and-gaps.md](docs/data/coverage-and-gaps.md).

## Contributing

Found a wrong LGA or bank code? Please [open a data correction](https://github.com/asgatcreation/naija-data/issues/new/choose)
with a source. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Contact

- Data corrections, new data, bugs: [GitHub issues](https://github.com/asgatcreation/naija-data/issues/new/choose)
- Questions and ideas: [GitHub Discussions](https://github.com/asgatcreation/naija-data/discussions)
- Security issues: [report privately](https://github.com/asgatcreation/naija-data/security/advisories/new) (see [SECURITY.md](SECURITY.md))
- Email: asgatcreation@gmail.com
- GitHub: [@asgatcreation](https://github.com/asgatcreation)

## Licence

Code: [MIT](LICENSE). Data: [CC BY 4.0](LICENSE-DATA). Upstream sources are credited in
[ATTRIBUTION.md](ATTRIBUTION.md).

---

Created and maintained by **Akanji Oluwaseun Gabriel** ([@asgatcreation](https://github.com/asgatcreation)).
