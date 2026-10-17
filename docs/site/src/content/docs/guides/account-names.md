---
title: Account names (name enquiry)
description: Why naija-data does not show account holder names, and how to look them up safely with your own payment provider.
---

naija-data checks that an account number is **well formed** for a bank (the CBN NUBAN check digit). It
does not tell you who owns the account, and the public API never will. Here is why, and how to do it in
your own app.

## Why naija-data does not show names

- **The data is not public.** Account names come from a live "name enquiry" on NIBSS, which only banks and
  licensed payment companies can call.
- **Names are personal data.** Under the Nigeria Data Protection Act 2023 a name linked to an account
  number is personal data. A public, free lookup would let anyone collect names in bulk.
- **A valid check digit is not proof.** About 1 in 10 random 10-digit numbers passes the check for any
  given bank, so only a name enquiry confirms that an account really exists.

## How to do it with your own provider

Payment providers such as Paystack, Flutterwave and Monnify offer a "resolve account" call to their
customers. You sign up, get a **secret key**, and call it from your **server**.

1. Validate first with naija-data, so obvious typos never cost you an API call:

   ```python
   import naija_data as ng

   if not ng.is_valid_nuban(account, bank_code):
       raise ValueError("Check the account number and bank.")
   ```

2. Then ask your provider. With Paystack (see its "Resolve Account Number" docs):

   ```python
   import os, requests

   r = requests.get(
       "https://api.paystack.co/bank/resolve",
       params={"account_number": account, "bank_code": bank_code},
       headers={"Authorization": f"Bearer {os.environ['PAYSTACK_SECRET_KEY']}"},
       timeout=10,
   )
   name = r.json()["data"]["account_name"] if r.ok else None
   ```

   Flutterwave and Monnify have the same check under their own endpoints; follow their documentation.
   Use the bank code your provider expects (its own bank list), which is usually but not always the CBN
   code that naija-data shows.

## Do it safely

- **Keep the secret key on the server.** Never put it in a browser, mobile app or public repository.
- **Ask only when you need it**, for example to confirm a payout account the user just entered, and show
  the name back to that user to confirm.
- **Don't store or log names you don't need**, and rate-limit the endpoint in your app so it cannot be
  used to look up strangers' accounts in bulk.
- **Phone-number wallets.** OPay, PalmPay and similar wallets usually use the phone number (without its
  first 0) as the account number. They have no CBN bank code, so the NUBAN check digit does not apply;
  check them with your provider instead, using the provider's code for that wallet.
