---
title: Functions (all languages)
description: The same functions in Python, JavaScript/TypeScript and Go.
---

Every function exists in all three packages with the same behaviour; shared parity tests check that they
return identical results. Names follow each language's conventions.

## Places

| Python | JavaScript | Go | Returns |
|---|---|---|---|
| `states()` | `states()` | `States()` | All 37 states and FCT, by name |
| `get_state(q)` | `getState(q)` | `GetState(q)` | State by ISO code, INEC code, P-code, slug, name or alias, or none |
| `lgas(state=None)` | `lgas(state?)` | `LGAs(state)` | LGAs of a state, or all 774 |
| `get_lga(q, state=None)` | `getLga(q, state?)` | `GetLGA(q, state)` | LGA by P-code, INEC code or name (none if ambiguous) |
| `find_lgas(name)` | `findLgas(name)` | `FindLGAs(name)` | Every LGA with that name or alias |
| `wards(lga, state=None)` | `wards(lga, state?)` from `naija-data/wards` | `Wards(lga, state)` | Wards of an LGA |
| `get_ward(code)` | `getWard(code)` from `naija-data/wards` | `GetWard(code)` | Ward by INEC code |
| `search(q, kinds, limit)` | `search(q, {limit})` | `Search(q, opts)` | Fuzzy matches for states and LGAs, with scores 0-1000 |
| `search_wards(q, limit)` | `searchWards(q, {limit})` | `SearchWards(q, opts)` | Fuzzy matches for wards |

## Senate, House of Representatives and House of Assembly

INEC's electoral units: 109 senatorial districts, 360 federal constituencies and 990 state
constituencies (the FCT has no House of Assembly). Each is a `Constituency` record with `kind`, `code`
(`SD001`, `FC001`, `SC001`), `inec_code` (`FC/001/AB`), `name`, `lga_codes` and `sources`. Every ward
carries the codes of its `senatorial_district`, `federal_constituency` and `state_constituency`.
In JavaScript these functions come from `naija-data/constituencies` (and `constituencyWards` from `naija-data/wards`).

| Python | JavaScript | Go | Returns |
|---|---|---|---|
| `senatorial_districts(state=None)` | `senatorialDistricts(state?)` | `SenatorialDistricts(state)` | Senatorial districts, all or of one state |
| `federal_constituencies(state=None)` | `federalConstituencies(state?)` | `FederalConstituencies(state)` | Federal constituencies (House of Reps seats) |
| `state_constituencies(state=None)` | `stateConstituencies(state?)` | `StateConstituencies(state)` | State constituencies (House of Assembly seats) |
| `constituencies(kind=None, state=None)` | `constituencies(kind?, state?)` | `Constituencies(kind, state)` | Any or all kinds |
| `get_constituency(code)` | `getConstituency(code)` | `GetConstituency(code)` | Unit by code or INEC code, or none |
| `find_constituencies(name, kind, state)` | `findConstituencies(name, kind?, state?)` | `FindConstituencies(name, kind, state)` | Every unit with that name or alias |
| `lga_constituencies(lga, state=None)` | `lgaConstituencies(lga, state?)` | `LGAConstituencies(lga, state)` | The units an LGA lies in (several when it is split) |
| `constituency_lgas(code)` | `constituencyLgas(code)` | `ConstituencyLGAs(code)` | LGAs a unit covers in full or in part |
| `constituency_wards(code)` | `constituencyWards(code)` from `naija-data/wards` | `ConstituencyWards(code)` | Wards that make up a unit |

```python
import naija_data as ng
[u.name for u in ng.lga_constituencies("Surulere", "Lagos")]
# ['Lagos Central', 'Surulere I', 'Surulere II', 'Surulere I', 'Surulere II']
ng.get_lga("Offa").senatorial_district  # 'Kwara South'
```

## Banks and NUBAN

| Python | JavaScript | Go | Returns |
|---|---|---|---|
| `banks(type=None, active_only=True)` | `banks(type?, activeOnly?)` | `Banks(typ, activeOnly)` | Licensed institutions |
| `get_bank(q)` | `getBank(q)` | `GetBank(q)` | Bank by id, CBN code, NIP code, name or alias |
| `find_banks(q)` | `findBanks(q)` | `FindBanks(q, limit)` | Fuzzy name search |
| `is_valid_nuban(account, bank)` | `isValidNuban(account, bank)` | `IsValidNUBAN(account, bank)` | Check digit valid for that bank |
| `banks_for_nuban(account)` | `banksForNuban(account)` | `BanksForNUBAN(account)` | Banks the number could belong to |
| `nuban_check_digit(code, serial)` | `nubanCheckDigit(code, serial)` | `NUBANCheckDigit(code, serial)` | The CBN check digit |

## Phone numbers

| Python | JavaScript | Go | Returns |
|---|---|---|---|
| `parse_phone(text)` | `parsePhone(text)` | `ParsePhone(text)` | Type, E.164, local form, area, network, or none if invalid |
| `phone_error(text)` | `phoneError(text)` | `PhoneError(text)` | Why a number is invalid, or none |
| `is_valid_phone(text, types=None)` | `isValidPhone(text, types?)` | `IsValidPhone(text, types)` | Valid, optionally of given types |
| `normalize_phone(text)` | `normalizePhone(text)` | `NormalizePhone(text)` | `+2348031234567` |
| `to_local(text)` | `toLocal(text)` | `ToLocal(text)` | `08031234567` |
| `area_codes()` | `areaCodes()` | `AreaCodes()` | The 56 landline area codes |
| `networks()`, `prefixes(network)` | `networks()`, `prefixes(network?)` | `Networks()`, `Prefixes(network)` | Mobile networks and their prefixes |

Phone error codes: `empty`, `invalid_characters`, `not_nigerian`, `bad_length`, `unknown_prefix`,
`unallocated`, `reserved`, `unknown_area_code`.

## Plates

| Python | JavaScript | Go | Returns |
|---|---|---|---|
| `parse_plate(text)` | `parsePlate(text)` | `ParsePlate(text)` | Compact and display forms, format, parts |
| `plate_error(text)` | `plateError(text)` | `PlateError(text)` | `empty`, `invalid_characters`, `unknown_format`, `unknown_state` |
| `is_valid_plate(text, formats=None)` | `isValidPlate(text, formats?)` | `IsValidPlate(text, formats)` | Valid, optionally of given formats |
| `plate_categories()` | `plateCategories()` | `PlateCategories()` | Colours by category (Road Traffic Regulations 2012) |

## About the data

| Python | JavaScript | Go | Returns |
|---|---|---|---|
| `meta()` | `meta()` | `Meta()` | Data version, counts, licence, attribution and sources |
