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

export type PhoneType = "mobile" | "fixed" | "toll_free" | "non_toll_free";

export type PhoneError =
  | "empty"
  | "invalid_characters"
  | "not_nigerian"
  | "bad_length"
  | "unknown_prefix"
  | "unallocated"
  | "reserved"
  | "unknown_area_code";

export interface PhoneNumber {
  /** +2348031234567 */
  e164: string;
  /** 08031234567 */
  local: string;
  /** 8031234567 (national significant number, without the trunk 0) */
  national: string;
  type: PhoneType;
  /** Mobile or special prefix ("0803", "0800") or fixed-line area code ("01"). */
  prefix: string;
  /** Fixed lines: the NCC primary centre, e.g. "Lagos". */
  area: string | null;
  /** Mobile: network the block was allocated to (numbers can be ported). Others: the allottee. */
  network: string | null;
  /** The number falls in a block the NCC has allocated. */
  allocated: boolean;
  /** Mobile: number portability caveat. */
  note: string | null;
}

export interface AreaCode {
  area_code: string;
  primary_centre: string;
  ncc_zone: string;
  unverified_fields: string[];
}

export type PlateFormat = "standard" | "dealer";
export type PlateError = "empty" | "invalid_characters" | "unknown_format" | "unknown_state";

export interface Plate {
  /** KJA123AB */
  compact: string;
  /** KJA-123AB */
  display: string;
  format: PlateFormat;
  /** Standard: the Local Government code. Dealer: "D" + state code. */
  prefix: string;
  number: string;
  suffix: string;
  /** Dealer plates only. */
  state_code: string | null;
  note: string | null;
}

export interface PlateCategory {
  category: string;
  vehicle: "vehicle" | "motorcycle";
  lettering_colour: string;
  background_colour: string;
  /** Where the National Road Traffic Regulations 2012 set it. */
  provision: string;
}

export interface Meta {
  data_version: string;
  counts: Record<string, number>;
  licence: string;
  attribution: string;
  sources: { id: string; name: string; url: string; retrieved: string; licence: string }[];
}
