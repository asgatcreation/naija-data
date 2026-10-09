# Security policy

## Supported versions

Security fixes are made for the latest release of each package (PyPI `naija-data`, npm
`naija-data`, the Go module) and for the current `/v1` public API.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately using GitHub's **"Report a vulnerability"** button under the repository's
**Security** tab, or email the maintainer at asgatcreation@gmail.com.

Please include what you found, how to reproduce it, and what impact you think it has. You will get
a reply within 7 days. Once a fix is released, you'll be credited unless you'd rather not be.

## Scope

- The packages and CLI (for example, crashes or very slow responses on malicious input to the
  fuzzy search, NUBAN or phone helpers).
- The public REST API (for example, getting around the rate limit, or injection through query
  parameters).
- Supply-chain concerns about the release workflow.

Wrong data is not a security issue. Please use the **Data correction** issue template for that.

## Note on NUBAN validation

`validateNuban` only checks the CBN check digit. A valid result does **not** mean the account
exists or belongs to anyone. Never use it alone to authorise payments.
