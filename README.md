# naija-data

**Accurate, sourced, open Nigerian reference data (states, LGAs, wards, banks, phone prefixes) for
Python, JavaScript/TypeScript and Go, plus a free REST API.**

[![CI](https://github.com/asgatcreation/naija-data/actions/workflows/ci.yml/badge.svg)](https://github.com/asgatcreation/naija-data/actions/workflows/ci.yml)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)

> 🚧 **Work in progress.** No package has been published yet. Follow the repo for the v1.0.0 release.

## Why

Nigerian developers often copy state and LGA lists from old gists that are outdated, have typos
and give no source. naija-data aims to be the trusted alternative:

- **Every record has a source.** The publisher, URL, retrieval date and licence are recorded in
  [`data/sources.json`](data/sources.json).
- **Nothing is guessed.** Anything we can't verify is marked `unverified` or left out, and the gaps
  are listed publicly.
- **Validated in CI.** Schema checks, unique codes, expected counts (36 states + FCT, 774 LGAs,
  8,809 registration areas).
- **One dataset, three languages.** The Python, JS and Go packages are generated from the same data,
  and shared tests check that they return identical results.

## Coverage

| Dataset | Rows | Main sources | Status |
|---|---|---|---|
| States + FCT | 37 | INEC, Constitution, OCHA COD-AB, Unicode CLDR | ✅ data ready |
| LGAs (incl. 6 FCT area councils) | 774 | INEC, Constitution, OCHA COD-AB | ✅ data ready |
| Wards / registration areas | 8,809 | INEC (live list + 2015 directory) | ✅ data ready |
| Banks and licensed financial institutions | 899 | CBN register; codes from Paystack + Monnify | ✅ data ready, codes partial |
| Mobile number prefixes | 45 | NCC | ✅ data ready |
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
