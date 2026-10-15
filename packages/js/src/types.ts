// Record types. Field names match the dataset (and the REST API) in every language.

export type Zone = "North-Central" | "North-East" | "North-West" | "South-East" | "South-South" | "South-West";

export interface State {
  code: string;
  iso_code: string;
  name: string;
  slug: string;
  inec_code: string;
  pcode: string;
  capital: string;
  zone: Zone;
  created: string | null;
  lat: number | null;
  lon: number | null;
  aliases: string[];
  unverified_fields: string[];
  sources: string[];
}

export interface LGA {
  code: string;
  state_code: string;
  inec_code: string;
  name: string;
  slug: string;
  headquarters: string | null;
  senatorial_district: string | null;
  lat: number | null;
  lon: number | null;
  aliases: string[];
  unverified_fields: string[];
  sources: string[];
}

export interface Ward {
  code: string;
  lga_code: string;
  state_code: string;
  name: string;
  slug: string;
  aliases: string[];
}

export type BankType =
  | "commercial"
  | "merchant"
  | "non_interest"
  | "payment_service_bank"
  | "mobile_money_operator"
  | "microfinance"
  | "mortgage"
  | "development_finance";

export interface Bank {
  id: string;
  name: string;
  short_name: string | null;
  type: BankType;
  cbn_code: string | null;
  nip_code: string | null;
  ussd: string | null;
  status: "active" | "merged" | "licence_revoked" | "defunct";
  status_date: string | null;
  merged_into: string | null;
  aliases: string[];
  unverified_fields: string[];
  sources: string[];
}

export type SearchKind = "state" | "lga" | "ward";

export interface SearchResult {
  kind: SearchKind;
  code: string;
  name: string;
  state_code: string;
  /** 0..1000 */
  score: number;
  /** The name or alias that matched. */
  matched: string;
}

export interface PhoneInfo {
  /** +2348031234567 */
  e164: string;
  /** 08031234567 */
  local: string;
  /** 0803 */
  prefix: string;
  /** Network the number block was allocated to (numbers can be ported, see `note`). */
  network: string | null;
  /** NCC block status, null if the prefix is not in the NCC table. */
  status: string | null;
  note: string;
}

export interface Meta {
  data_version: string;
  counts: Record<string, number>;
  licence: string;
  attribution: string;
  sources: { id: string; name: string; url: string; retrieved: string; licence: string }[];
}
