# naija-data (JavaScript / TypeScript)

Accurate, sourced Nigerian reference data: 36 states + FCT, 774 LGAs, 8,809 wards, CBN-licensed
banks with NUBAN validation, and mobile phone helpers. Zero dependencies, ESM + CommonJS, full
TypeScript types, tree-shakeable.

```bash
npm install naija-data
```

```ts
import { getState, lgas, search, getBank, isValidNuban, banksForNuban, normalizePhone, parsePhone, phoneError, parsePlate } from "naija-data";
import { wards } from "naija-data/wards"; // 8,809 wards: separate entry point, only loaded if imported

getState("lagos")?.capital;               // "Ikeja"
lgas("FCT").map((l) => l.name);          // ["Abaji", "Abuja Municipal", "Bwari", ...]
search("lagso")[0].name;                  // "Lagos" (typo-tolerant, knows aliases and accents: "Ọ̀yọ́")
wards("Ikeja", "Lagos")[0].name;          // "Anifowoshe/Ikeja"

getBank("058")?.name;                     // "Guaranty Trust Bank Plc"
isValidNuban("0000014579", "011");        // true (CBN check-digit algorithm)
banksForNuban("0000014579");              // banks this account number could belong to

normalizePhone("0803 123 4567");          // "+2348031234567"
parsePhone("08031234567")?.network;       // "MTN" (allocation; numbers can be ported)
parsePhone("01 269 1531")?.area;          // "Lagos" (landlines, 0800 toll-free and 0700 too)
phoneError("0900 123 4567");              // "reserved" (why a number is invalid)
parsePlate("kja 123 ab")?.display;        // "KJA-123AB"
```

## Zod

```ts
import { z } from "zod";
import { phoneSchema, nubanWithBankSchema, plateSchema } from "naija-data/zod"; // needs zod 3.25+ or 4

const Signup = z.object({
  phone: phoneSchema({ types: ["mobile"] }), // parses to "+2348031234567", clear messages on failure
  plate: plateSchema().optional(),           // parses to "KJA-123AB"
  payout: nubanWithBankSchema(),             // { account, bank }: account must be valid for the bank
});
```

Command line: `npx naija-data lga lagos`, `npx naija-data bank 058`, `npx naija-data nuban 0000014579`.

## Bundle size

What your bundle grows by (minified + gzipped, measured with esbuild):

| Import | Gzipped |
|---|---|
| `getState`, `states` | 2.3 KB |
| `parsePlate` | 2.4 KB |
| `parsePhone`, `normalizePhone` (includes the NCC number tables) | 4.9 KB |
| banks + NUBAN | 15 KB |
| states + LGAs + `search` | 30 KB |
| everything in `naija-data` | 54 KB |
| `naija-data/zod` (plus zod itself) | 5.3 KB |
| `naija-data/wards` | 148 KB |

Record fields keep the dataset's names (`state.iso_code`, `bank.cbn_code`), identical in the Python
and Go packages and the REST API. Every record carries its `sources` and lists any
`unverified_fields`. Docs, sources and known gaps: https://github.com/asgatcreation/naija-data

Code: MIT. Data: CC BY 4.0 — credit "naija-data by Akanji Oluwaseun Gabriel".
