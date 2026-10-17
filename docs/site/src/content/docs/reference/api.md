---
title: REST API endpoints
description: Every endpoint of the naija-data REST API.
---

Base URL: `https://naija-data-api.asgatcreation.workers.dev`. Try every endpoint in the
[interactive docs](https://naija-data-api.asgatcreation.workers.dev/v1/docs).

| Endpoint | Description |
|---|---|
| `GET /v1/states` | All 36 states and the FCT |
| `GET /v1/states/{state}` | One state (ISO code, INEC code, P-code, slug, name or alias) |
| `GET /v1/states/{state}/lgas` | LGAs of a state |
| `GET /v1/lgas?state=` | All 774 LGAs, or those of one state |
| `GET /v1/lgas/{lga}?state=` | One LGA (P-code, INEC code or name); 409 with `candidates` if a name is shared |
| `GET /v1/lgas/{lga}/wards` | Wards of an LGA |
| `GET /v1/lgas/{lga}/constituencies` | The senatorial district and federal and state constituencies of an LGA |
| `GET /v1/wards/{code}` | One ward by INEC code, with its senatorial district and constituencies |
| `GET /v1/constituencies?kind=&state=&q=` | Senatorial districts, federal and state constituencies |
| `GET /v1/senatorial-districts?state=` | The 109 senatorial districts |
| `GET /v1/federal-constituencies?state=` | The 360 federal constituencies (House of Representatives) |
| `GET /v1/state-constituencies?state=` | The 990 state constituencies (Houses of Assembly) |
| `GET /v1/constituencies/{code}` | One unit by code (`FC236`) or INEC code (`FC/236/LA`) |
| `GET /v1/constituencies/{code}/lgas` | LGAs a unit covers |
| `GET /v1/constituencies/{code}/wards` | Wards that make up a unit |
| `GET /v1/search?q=&kinds=state,lga,ward&limit=` | Fuzzy search |
| `GET /v1/banks?type=&active=&q=` | Licensed institutions, by type or fuzzy name |
| `GET /v1/banks/{bank}` | One institution (id, CBN code, NIP code or name) |
| `GET /v1/validate/nuban?account=&bank=` | Check digit for a bank, or the candidate banks if `bank` is omitted |
| `GET /v1/phone/{number}` | Validate and describe a phone number; 422 with the reason if invalid |
| `GET /v1/area-codes` | The 56 landline area codes |
| `GET /v1/plates` | Plate colours by category |
| `GET /v1/plates/{plate}` | Validate and parse a plate number |
| `GET /v1/meta` | Data version, counts and sources |
| `GET /v1/health` | Health check with data and API versions |
| `GET /v1/openapi.json` | OpenAPI 3.1 description |

Postcodes are not served: NIPOST's postcode records are only available through its own gated API and are not
licensed for redistribution. See [coverage and gaps](/data/coverage/).
