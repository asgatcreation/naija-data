// Command line: `npx naija-data lga lagos`, `naija bank 058`, `naija nuban 0123456789`, ...
import {
  banks, banksForNuban, findBanks, getBank, getLga, getState, isValidNuban, lgas, meta, parsePhone, parsePlate,
  phoneError, plateError, search, states,
  type BankType,
} from "./index.js";
import { wards } from "./wards.js";

const HELP = `naija — Nigerian reference data (naija-data ${meta().data_version})

Usage: naija <command> [args] [--json]

  states                    list states and the FCT
  state <query>             show one state
  lga <state|lga> [--state] list a state's LGAs, or show one LGA
  wards <lga> [--state S]   list an LGA's wards
  search <query>            fuzzy search states and LGAs
  bank <code|name>          look up a bank
  banks [--type T]          list institutions
  nuban <account> [bank]    validate an account number (omit bank to list candidates)
  phone <number>            validate a phone number, show its type and network
  plate <plate>             validate a vehicle plate number`;

function main(argv: string[]): number {
  const json = argv.includes("--json");
  const opt = (name: string) => {
    const i = argv.indexOf(name);
    return i >= 0 ? argv[i + 1] : undefined;
  };
  const args = argv.filter((a, i) => !a.startsWith("--") && !(i > 0 && ["--state", "--type"].includes(argv[i - 1])));
  const [cmd, ...rest] = args;
  const q = rest.join(" ");
  const out = (data: unknown, lines: string[]) => {
    console.log(json ? JSON.stringify(data, null, 2) : lines.length ? lines.join("\n") : "No results.");
    return data == null || (Array.isArray(data) && data.length === 0) ? 1 : 0;
  };

  switch (cmd) {
    case "states": {
      const rows = states();
      return out(rows, rows.map((s) => `${s.code}  ${s.name.padEnd(26)} capital: ${s.capital.padEnd(14)} ${s.zone}`));
    }
    case "state": {
      const s = getState(q);
      return out(s, s ? [`${s.name} (${s.iso_code})`, `  capital: ${s.capital}`, `  zone: ${s.zone}`, `  LGAs: ${lgas(s).length}`] : []);
    }
    case "lga": {
      const st = opt("--state") ? null : getState(q);
      if (st) {
        const rows = lgas(st);
        return out(rows, [`${st.name}: ${rows.length} LGAs`, ...rows.map((l) => `  ${l.code}  ${l.name}`)]);
      }
      const l = getLga(q, opt("--state"));
      return out(l, l ? [`${l.name} (${l.code}), ${getState(l.state_code)!.name}`, `  headquarters: ${l.headquarters ?? "unknown"}`,
        `  senatorial district: ${l.senatorial_district}`, `  wards: ${wards(l).length}`] : []);
    }
    case "wards": {
      const rows = wards(q, opt("--state"));
      return out(rows, rows.map((w) => `  ${w.code}  ${w.name}`));
    }
    case "search": {
      const rows = search(q);
      return out(rows, rows.map((r) => `  ${String(r.score).padStart(4)}  ${r.kind.padEnd(5)} ${r.code.padEnd(9)} ${r.name}`));
    }
    case "bank": {
      const b = getBank(q);
      const rows = b ? [b] : findBanks(q, 5);
      return out(rows, rows.map((x) => `${x.name}  [${x.type}]  CBN code: ${x.cbn_code ?? "-"}  NIP code: ${x.nip_code ?? "-"}  USSD: ${x.ussd ?? "-"}`));
    }
    case "banks": {
      const rows = banks(opt("--type") as BankType | undefined);
      return out(rows, rows.map((b) => `  ${(b.cbn_code ?? "-").padEnd(6)} ${b.name}`));
    }
    case "nuban": {
      const [account, ...bank] = rest;
      if (bank.length) {
        const ok = isValidNuban(account, bank.join(" "));
        console.log(json ? JSON.stringify({ account, bank: bank.join(" "), valid: ok }) : `${account}: ${ok ? "valid" : "NOT valid"} for ${bank.join(" ")}`);
        return ok ? 0 : 1;
      }
      const rows = banksForNuban(account);
      return out(rows, [`${account} has a valid check digit for ${rows.length} banks:`, ...rows.map((b) => `  ${b.cbn_code!.padEnd(6)} ${b.name}`)]);
    }
    case "phone": {
      const info = parsePhone(q);
      if (!info) {
        console.log(json ? JSON.stringify({ number: q, valid: false, error: phoneError(q) }) : `${q}: NOT valid (${phoneError(q)})`);
        return 1;
      }
      return out(info, [`${info.e164}  (${info.local})`, `  type: ${info.type}`,
        `  network: ${info.network ?? "unknown"}${info.type === "mobile" ? ` (prefix ${info.prefix})` : ""}`,
        ...(info.area ? [`  area: ${info.area} (${info.prefix})`] : []), ...(info.note ? [`  note: ${info.note}`] : [])]);
    }
    case "plate": {
      const plate = parsePlate(q);
      if (!plate) {
        console.log(json ? JSON.stringify({ plate: q, valid: false, error: plateError(q) }) : `${q}: NOT valid (${plateError(q)})`);
        return 1;
      }
      return out(plate, [`${plate.display}  [${plate.format}]`,
        ...(plate.state_code ? [`  state: ${getState(plate.state_code)!.name}`] : []), ...(plate.note ? [`  note: ${plate.note}`] : [])]);
    }
    default:
      console.log(HELP);
      return cmd ? 2 : 0;
  }
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (e) {
  console.error((e as Error).message);
  process.exitCode = 2;
}
