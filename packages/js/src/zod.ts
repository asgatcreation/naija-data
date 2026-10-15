// Zod schemas for Nigerian phone numbers, NUBAN account numbers and plate numbers.
//
//   import { phoneSchema, nubanSchema, plateSchema, nubanWithBankSchema } from "naija-data/zod";
//   const Form = z.object({ phone: phoneSchema({ types: ["mobile"] }), account: nubanSchema() });
//
// Requires `zod` (v3.25+ or v4), which is an optional peer dependency of naija-data.
import { z } from "zod";
import { isValidNuban, getBank } from "./banks";
import { parsePhone, phoneError } from "./phone";
import { parsePlate, plateError } from "./plates";
import type { PhoneError, PhoneType, PlateError, PlateFormat } from "./types";

/** Default English error messages, keyed by the error codes of phoneError() and plateError(). */
export const PHONE_MESSAGES: Record<PhoneError | "wrong_type", string> = {
  empty: "Enter a phone number.",
  invalid_characters: "A phone number can only contain digits, spaces, dashes, brackets and a leading +.",
  not_nigerian: "Enter a Nigerian phone number (+234).",
  bad_length: "This phone number has the wrong number of digits.",
  unknown_prefix: "This is not a Nigerian mobile prefix.",
  unallocated: "This number range is not allocated to any network.",
  reserved: "This number range is reserved and not in service.",
  unknown_area_code: "This is not a Nigerian landline area code.",
  wrong_type: "This type of phone number is not accepted here.",
};

export const PLATE_MESSAGES: Record<PlateError | "wrong_format", string> = {
  empty: "Enter a plate number.",
  invalid_characters: "A plate number can only contain letters, digits, spaces and dashes.",
  unknown_format: "Enter a plate number like ABC-123DE.",
  unknown_state: "This dealer plate does not start with D and a valid state code.",
  wrong_format: "This type of plate number is not accepted here.",
};

export const NUBAN_MESSAGES = {
  format: "Enter a 10-digit account number.",
  check_digit: "This account number is not valid for the selected bank.",
  unknown_bank: "Select a valid bank.",
};

export interface PhoneSchemaOptions {
  /** Accept only these types, e.g. ["mobile"] for numbers that can receive SMS. */
  types?: readonly PhoneType[];
  /** Override messages. */
  messages?: Partial<typeof PHONE_MESSAGES>;
}

/** A Nigerian phone number. Parses to the E.164 form, e.g. "+2348031234567". */
export function phoneSchema(options: PhoneSchemaOptions = {}) {
  const messages = { ...PHONE_MESSAGES, ...options.messages };
  return z
    .string()
    .superRefine((value, ctx) => {
      const error = phoneError(value);
      if (error) ctx.addIssue({ code: "custom", message: messages[error], params: { reason: error } });
      else if (options.types && !options.types.includes(parsePhone(value)!.type)) {
        ctx.addIssue({ code: "custom", message: messages.wrong_type, params: { reason: "wrong_type" } });
      }
    })
    .transform((value) => parsePhone(value)!.e164);
}

export interface PlateSchemaOptions {
  formats?: readonly PlateFormat[];
  messages?: Partial<typeof PLATE_MESSAGES>;
}

/** A vehicle plate number. Parses to the display form, e.g. "KJA-123AB". */
export function plateSchema(options: PlateSchemaOptions = {}) {
  const messages = { ...PLATE_MESSAGES, ...options.messages };
  return z
    .string()
    .superRefine((value, ctx) => {
      const error = plateError(value);
      if (error) ctx.addIssue({ code: "custom", message: messages[error], params: { reason: error } });
      else if (options.formats && !options.formats.includes(parsePlate(value)!.format)) {
        ctx.addIssue({ code: "custom", message: messages.wrong_format, params: { reason: "wrong_format" } });
      }
    })
    .transform((value) => parsePlate(value)!.display);
}

const digits = (value: string) => value.replace(/[\s-]/g, "");

/**
 * A 10-digit NUBAN account number. Pass `bank` (CBN code, id or name) to also check the CBN check
 * digit for that bank. Parses to the 10 digits without spaces.
 */
export function nubanSchema(options: { bank?: string; messages?: Partial<typeof NUBAN_MESSAGES> } = {}) {
  const messages = { ...NUBAN_MESSAGES, ...options.messages };
  return z
    .string()
    .superRefine((value, ctx) => {
      if (!/^\d{10}$/.test(digits(value))) ctx.addIssue({ code: "custom", message: messages.format, params: { reason: "format" } });
      else if (options.bank && !isValidNuban(value, options.bank)) {
        ctx.addIssue({ code: "custom", message: messages.check_digit, params: { reason: "check_digit" } });
      }
    })
    .transform(digits);
}

/** An { account, bank } pair where the account number must be valid for the chosen bank. */
export function nubanWithBankSchema(options: { messages?: Partial<typeof NUBAN_MESSAGES> } = {}) {
  const messages = { ...NUBAN_MESSAGES, ...options.messages };
  return z
    .object({ account: nubanSchema({ messages }), bank: z.string() })
    .superRefine((value, ctx) => {
      const bank = getBank(value.bank);
      if (!bank || !bank.cbn_code) {
        ctx.addIssue({ code: "custom", path: ["bank"], message: messages.unknown_bank, params: { reason: "unknown_bank" } });
      } else if (!isValidNuban(value.account, bank.cbn_code)) {
        ctx.addIssue({ code: "custom", path: ["account"], message: messages.check_digit, params: { reason: "check_digit" } });
      }
    });
}
