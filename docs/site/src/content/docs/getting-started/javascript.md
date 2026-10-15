---
title: JavaScript / TypeScript
description: Install and use naija-data in Node.js, browsers, Deno, Bun and edge runtimes.
---

ESM and CommonJS, full TypeScript types, no dependencies, tree-shakeable. Node.js 20 or newer.

```bash
npm install naija-data
```

```ts
import { getState, lgas, getLga, findLgas, search } from "naija-data";
import { wards, searchWards } from "naija-data/wards"; // the 8,809 wards: only loaded if you import them

getState("lagos")?.capital;              // "Ikeja"
lgas("FCT").map((l) => l.name);         // ["Abaji", "Abuja Municipal", ...]
getLga("Surulere");                      // null: two states have one
getLga("Surulere", "Oyo")?.code;         // "NG031033"
search("lagso")[0].name;                 // "Lagos"
wards("Ikeja", "Lagos").length;          // 10
```

Functions use JavaScript naming (`getState`); record fields keep the dataset's names (`state.iso_code`),
identical to Python, Go and the API.

## Banks, NUBAN, phone and plates

```ts
import { getBank, isValidNuban, banksForNuban, parsePhone, phoneError, parsePlate } from "naija-data";

getBank("GTB")?.cbn_code;                // "058"
isValidNuban("0000014579", "011");       // true
banksForNuban("0000014579");             // candidate banks
parsePhone("0803 123 4567")?.network;    // "MTN"
phoneError("0900 123 4567");             // "reserved"
parsePlate("kja 123 ab")?.display;       // "KJA-123AB"
```

## Zod

```ts
import { z } from "zod";
import { phoneSchema, plateSchema, nubanWithBankSchema } from "naija-data/zod";

const Signup = z.object({
  phone: phoneSchema({ types: ["mobile"] }), // parses to "+2348031234567"
  plate: plateSchema().optional(),           // parses to "KJA-123AB"
  payout: nubanWithBankSchema(),             // account must be valid for the chosen bank
});
```

`zod` (3.25+ or 4) is an optional peer dependency; install it yourself if you use this entry point.

## State → LGA → ward picker (React)

```tsx
import { useMemo, useState } from "react";
import { states, lgas } from "naija-data";

export function StateLgaWard() {
  const [state, setState] = useState("");
  const [lga, setLga] = useState("");
  const [wardList, setWardList] = useState<{ code: string; name: string }[]>([]);
  const lgaList = useMemo(() => (state ? lgas(state) : []), [state]);

  async function chooseLga(code: string) {
    setLga(code);
    const { wards } = await import("naija-data/wards"); // loaded on demand
    setWardList(code ? wards(code) : []);
  }

  return (
    <>
      <select value={state} onChange={(e) => { setState(e.target.value); setLga(""); setWardList([]); }}>
        <option value="">State</option>
        {states().map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
      </select>
      <select value={lga} onChange={(e) => chooseLga(e.target.value)} disabled={!state}>
        <option value="">LGA</option>
        {lgaList.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
      </select>
      <select disabled={!wardList.length}>
        <option value="">Ward</option>
        {wardList.map((w) => <option key={w.code} value={w.code}>{w.name}</option>)}
      </select>
    </>
  );
}
```

## Bundle size

| Import | Gzipped |
|---|---|
| `getState`, `states` | 2.3 KB |
| `parsePlate` | 2.4 KB |
| `parsePhone`, `normalizePhone` | 4.9 KB |
| banks + NUBAN | 15 KB |
| states + LGAs + `search` | 30 KB |
| `naija-data/wards` | 148 KB |

## Command line

```bash
npx naija-data lga lagos
npx naija-data phone 08031234567
```
