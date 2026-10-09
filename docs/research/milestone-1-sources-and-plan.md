# Milestone 1 — Sources, licences, schema, layout, hosting

Research date: 2026-10-09. Every licence below was checked on the source itself (HDX via its CKAN API,
geoBoundaries via its API, NCC/CBN/NIPOST/INEC via their websites). Not legal advice.

## 1. Package names (checked against the live registries)

| Registry | Name | Status |
|---|---|---|
| PyPI | `naija-data` | available (404) |
| npm | `naija-data` | available (404) |
| npm | `@asgatcreation/naija-data` | available |
| GitHub | `asgatcreation/naija-data` | not created yet |

Recommendation: `naija-data` on both PyPI (import as `naija_data`) and npm (unscoped). Go module:
`github.com/asgatcreation/naija-data/go` (package `naija`), tagged `go/vX.Y.Z`.
Names are only "reserved" once something is published, so availability can change before v0.1.0.

## 2. Sources and licences

| Data | Recommended source | Licence | Verdict |
|---|---|---|---|
| States + LGA names (canonical) | 1999 Constitution, First Schedule Part I (lists every state and its 774 LGAs) | Federal law (public legal text) | Use as the canonical name list |
| State/LGA codes, P-codes, ward layer, boundaries | OCHA COD-AB Nigeria (`cod-ab-nga`, HDX). Source: OSGOF + eHealth + UN Cartographic Section. Updated 2026-04-16 | **CC BY-IGO** (attribution only) | Use. Gives P-codes (e.g. NG025001), 37/774 features, ward level "for operational purposes only" |
| State + LGA boundaries (GeoJSON) and centroids | geoBoundaries gbOpen NGA ADM1/ADM2 (from GRID3, 2022) | **CC BY 4.0** | Use for optional boundaries package and for centroid coordinates |
| Wards / registration areas (8,809) | INEC Polling Unit Directory PDFs (one per state, revised Jan 2015) + INEC site totals (8,809 RAs, 774 LGAs, 176,846 PUs) | Public government documents, no licence stated; we take only factual names/codes | Use, with provenance; extract PDFs to CSV and cross-check |
| Wards cross-check | OCHA "INEC LGA and wards" (HDX, 2017, some states only) | **CC0** | Use as a secondary check |
| Ward boundaries | GRID3 NGA Operational Wards v3.0 (24 states only, not government-validated) | **CC BY-SA** (share-alike) | Do NOT put in core. Share-alike would force the derived files to be CC BY-SA. Optional separate package later |
| Postcodes (new) | NIPOST National Digital Alphanumeric Postcode System (postcode.gov.ng), launched 1 Oct 2026; 11 chars, e.g. `FC02A09DB09` | Gated API with keys; fees for bulk/premium; no open licence | Cannot redistribute. Ship a format parser/validator + link to official lookup |
| Postcodes (legacy 6-digit) | No authoritative, redistributable source found. Web lists are low-quality and contradict each other | Unknown | Leave out of v1 (listed as a gap) unless NIPOST grants permission |
| Banks: names, types, status | CBN "Financial Institutions" lists (DMBs, merchant, non-interest, MFBs, PSBs, MMOs...) | Public facts from regulator site | Use as source of truth for "is this licensed" |
| Bank codes: 3-digit CBN + 6-digit NIP | No public official NIBSS list. CBN NUBAN docs show some codes. Payment-provider docs (Paystack, Flutterwave, Kuda...) publish NIP codes | Facts; third-party lists | Use with a per-row `verification` field: `verified` only if 2+ independent sources agree |
| USSD codes, websites | Each bank's official website | Facts | Per-row source |
| NUBAN algorithm | CBN "Revised Standards on NUBAN" (2020), PSMD | Public standard | Implement exactly; includes worked example to test against |
| Phone prefixes | NCC "Mobile Number Allocation Table" (as at Dec 2023, page updated Nov 2024) | NCC site "All rights reserved"; we take only factual prefix→operator facts | Use; note number portability (since 2013) |
| State metadata (capital, creation date, zone) | Constitution + creation decrees; state government sites | Facts | Per-row source |
| Nicknames ("Centre of Excellence") | State government sites / official number-plate slogans | Facts | Per-row source, else omit |
| LGA headquarters | No single official list found yet. Avoid copying Wikipedia (CC BY-SA) | — | Research in M3; mark `unverified` where needed |

Coordinates: computed as polygon centroids from geoBoundaries (CC BY 4.0) and labelled "centroid", not "capital location". OpenStreetMap (ODbL) is avoided in the core because ODbL adds share-alike database terms.

## 3. Licence conclusion

- Code: MIT. Dataset: CC BY 4.0 — compatible with CC BY-IGO, CC BY 4.0 and CC0 inputs, as long as we credit them (a `NOTICE`/`ATTRIBUTION.md` file plus `sources.json`).
- The only share-alike inputs (GRID3 wards, OSM, Wikipedia) are kept out of the core.

## 4. Proposed schema (CSV in `data/`, validated by JSON Schema)

Every row has `sources` (ids into `data/sources.json`) and, where relevant, `verification` (`verified` | `unverified`).

- `sources.json`: id, name, publisher, url, retrieved (date), licence, notes
- `states.csv`: iso_code (`NG-LA`), code (`LA`), inec_code, pcode (`NG025`), name, slug, capital, zone, created (date), aliases, nicknames, lat, lon, sources
- `lgas.csv`: pcode (primary key, `NG025001`), inec_code, state_code, name, slug, headquarters, aliases, former_names, lat, lon, sources, verification
- `wards.csv`: id, inec_code (state/lga/ra), lga_pcode, name, slug, aliases, pcode (if matched to COD-AB), sources
- `banks.csv`: id (slug), name, short_name, cbn_code, nip_code, type (commercial | merchant | non_interest | microfinance | payment_service_bank | mobile_money_operator | ...), ussd, website, status (active | merged | defunct | licence_revoked), merged_into, status_date, sources, verification
- `phone_prefixes.csv`: prefix, operator, range_start, range_end, status, sources
- `postcode_formats.json`: NDAPS structure and state prefixes (if published openly), else format rules only

Aliases are `|`-separated in CSV, arrays in generated JSON.

## 5. Repo layout

```
naija-data/
  data/            CSV + sources.json (the single source of truth)
  schemas/         JSON Schemas
  scripts/         extract/clean/validate/build (Python)
  fixtures/        shared parity test cases (JSON)
  packages/python/ generated data + hand-written API, CLI
  packages/js/     TypeScript, ESM+CJS, lazy-loaded wards
  go/              Go module (data embedded)
  api/             Cloudflare Worker + OpenAPI
  docs/            Astro Starlight site + playground
  boundaries/      optional GeoJSON package (later)
```

## 6. Hosting

| Option | Free tier | Sleeps? | Verdict |
|---|---|---|---|
| Cloudflare Workers | 100k requests/day, global edge, Cache API, rate-limit binding | No | **Recommended** for the API |
| Deno Deploy | generous free requests | No | Good backup |
| Vercel functions | Hobby plan, non-commercial | Cold starts | OK, less ideal |
| Render free (used for CarHub) | Free | Yes (sleeps) | Not suitable |

Docs: Astro Starlight on Cloudflare Pages (same account) or GitHub Pages. Uptime: `/v1/health` + a free
external monitor (e.g. UptimeRobot) linked from the docs.

## 7. Decisions (approved by the owner, 2026-10-09)

1. Postcodes: v1 ships a format validator for NDAPS codes and a link to the official lookup. No
   legacy list. This is listed as a known gap.
2. Ward boundaries (CC BY-SA, 24 states): not in the core. A separate CC BY-SA package may follow later.
3. Names: `naija-data` on PyPI and npm (unscoped). Go module `github.com/asgatcreation/naija-data/go`.
4. Hosting: API on Cloudflare Workers; docs on Cloudflare Pages (Astro Starlight).
5. Bank codes: each row carries `verification` (`verified` needs 2+ independent sources).
