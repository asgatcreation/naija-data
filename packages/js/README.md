# naija-data (JavaScript / TypeScript)

Accurate, sourced Nigerian reference data: 36 states + FCT, 774 LGAs, 8,809 wards, CBN-licensed
banks with NUBAN validation, and mobile phone helpers. Zero dependencies, ESM + CommonJS, full
TypeScript types, tree-shakeable.

```bash
npm install naija-data
```

```ts
import { getState, lgas, search, getBank, isValidNuban, banksForNuban, normalizePhone, lookupPhone } from "naija-data";
import { wards } from "naija-data/wards"; // 8,809 wards: separate entry point, only loaded if imported

getState("lagos")?.capital;               // "Ikeja"
lgas("FCT").map((l) => l.name);          // ["Abaji", "Abuja Municipal", "Bwari", ...]
search("lagso")[0].name;                  // "Lagos" (typo-tolerant, knows aliases and accents: "Ọ̀yọ́")
wards("Ikeja", "Lagos")[0].name;          // "Anifowoshe/Ikeja"

getBank("058")?.name;                     // "Guaranty Trust Bank Plc"
isValidNuban("0000014579", "011");        // true (CBN check-digit algorithm)
banksForNuban("0000014579");              // banks this account number could belong to

normalizePhone("0803 123 4567");          // "+2348031234567"
lookupPhone("08031234567")?.network;      // "MTN" (allocation; numbers can be ported)
```

Command line: `npx naija-data lga lagos`, `npx naija-data bank 058`, `npx naija-data nuban 0000014579`.

## Bundle size

What your bundle grows by (minified + gzipped, measured with esbuild):

| Import | Gzipped |
|---|---|
| `normalizePhone`, `lookupPhone` | 0.8 KB |
| `getState`, `states` | 2.3 KB |
| states + LGAs + `search` | 30 KB |
| banks + NUBAN | 15 KB |
| everything in `naija-data` | 49 KB |
| `naija-data/wards` | 148 KB |

Record fields keep the dataset's names (`state.iso_code`, `bank.cbn_code`), identical in the Python
and Go packages and the REST API. Every record carries its `sources` and lists any
`unverified_fields`. Docs, sources and known gaps: https://github.com/asgatcreation/naija-data

Code: MIT. Data: CC BY 4.0 — credit "naija-data by Akanji Oluwaseun Gabriel".
