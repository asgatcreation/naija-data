import bankData from "./data/banks.json";
import { cmp, norm, score } from "./text";
import type { Bank, BankType } from "./types";

const BANKS = bankData as Bank[];

export const BANK_TYPES: readonly BankType[] = [
  "commercial", "merchant", "non_interest", "payment_service_bank", "mobile_money_operator",
  "microfinance", "mortgage", "development_finance",
];

// CBN Revised Standards on NUBAN: weights for the 6-digit institution code + 9-digit serial.
const WEIGHTS = [3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3];

const terms = (b: Bank) => [b.name, b.short_name ?? "", ...b.aliases].filter(Boolean);

/** Licensed institutions, optionally of one type. Inactive ones only with activeOnly = false. */
export function banks(type?: BankType | null, activeOnly = true): Bank[] {
  if (type != null && !BANK_TYPES.includes(type)) {
    throw new Error(`Unknown bank type: ${JSON.stringify(type)}. Use one of ${BANK_TYPES.join(", ")}`);
  }
  return BANKS.filter((b) => (type == null || b.type === type) && (b.status === "active" || !activeOnly));
}

/**
 * Find an institution by id ("gtbank"), CBN code ("058", "50211"), NIP code ("000013"), name,
 * short name or alias ("GTB"). Active institutions win ties.
 */
export function getBank(query: string | Bank): Bank | null {
  if (typeof query !== "string") return query;
  const q = query.trim();
  if (!q) return null;
  let hits: Bank[];
  if (/^(\d{3}|\d{5})$/.test(q)) hits = BANKS.filter((b) => b.cbn_code === q);
  else if (/^\d{6}$/.test(q)) hits = BANKS.filter((b) => b.nip_code === q);
  else {
    const key = norm(q);
    hits = BANKS.filter((b) => b.id === q.toLowerCase());
    if (!hits.length) hits = BANKS.filter((b) => terms(b).some((t) => norm(t) === key));
  }
  const active = hits.filter((b) => b.status === "active");
  return active[0] ?? hits[0] ?? null;
}

/** Fuzzy search by name, short name or alias, best match first. */
export function findBanks(query: string, limit = 10, activeOnly = true, minScore = 600): Bank[] {
  const q = norm(query);
  if (!q) return [];
  const scored: [number, Bank][] = [];
  for (const b of BANKS) {
    if (activeOnly && b.status !== "active") continue;
    const best = Math.max(...terms(b).map((t) => score(q, norm(t))));
    if (best >= minScore) scored.push([best, b]);
  }
  scored.sort((x, y) => y[0] - x[0] || cmp(x[1].name, y[1].name) || cmp(x[1].id, y[1].id));
  return scored.slice(0, limit).map(([, b]) => b);
}

// ------------------------------------------------------------------ NUBAN

function institutionCode(cbnCode: string): string {
  if (/^\d{3}$/.test(cbnCode)) return "000" + cbnCode; // deposit money banks
  if (/^\d{5}$/.test(cbnCode)) return "9" + cbnCode; // other financial institutions
  throw new Error(`A CBN bank code has 3 digits (banks) or 5 digits (other institutions): ${JSON.stringify(cbnCode)}`);
}

/** Check digit for a 9-digit account serial at the bank with this CBN code. */
export function nubanCheckDigit(bankCode: string, serial: string): number {
  if (!/^\d{9}$/.test(serial)) throw new Error(`The NUBAN serial must be 9 digits: ${JSON.stringify(serial)}`);
  const digits = institutionCode(bankCode) + serial;
  let total = 0;
  for (let i = 0; i < 15; i++) total += Number(digits[i]) * WEIGHTS[i];
  return (10 - (total % 10)) % 10;
}

const clean = (account: string) => account.replace(/[\s-]/g, "");

/**
 * True if the 10-digit account number has a correct check digit for this bank. `bank` is a CBN
 * code ("058"), a Bank, or anything getBank() understands. This does not prove the account exists.
 */
export function isValidNuban(account: string, bank: string | Bank): boolean {
  const acct = clean(account);
  if (!/^\d{10}$/.test(acct)) return false;
  let code: string | null = typeof bank === "string" && /^(\d{3}|\d{5})$/.test(bank.trim()) ? bank.trim() : null;
  if (code === null) {
    const found = getBank(bank);
    if (!found || !found.cbn_code) throw new Error(`No CBN code known for bank ${JSON.stringify(bank)}`);
    code = found.cbn_code;
  }
  return nubanCheckDigit(code, acct.slice(0, 9)) === Number(acct[9]);
}

/**
 * Institutions for which this account number has a valid check digit. About 1 in 10 banks match
 * any number, so use it to narrow a bank picker, not to identify the bank for certain.
 */
export function banksForNuban(account: string, activeOnly = true): Bank[] {
  const acct = clean(account);
  if (!/^\d{10}$/.test(acct)) return [];
  const check = Number(acct[9]);
  return BANKS.filter((b) => b.cbn_code && (b.status === "active" || !activeOnly) && nubanCheckDigit(b.cbn_code, acct.slice(0, 9)) === check);
}
