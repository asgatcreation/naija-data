---
title: REST API
description: The free, read-only naija-data REST API.
---

**Base URL:** `https://naija-data-api.asgatcreation.workers.dev/v1`

Interactive documentation: [/v1/docs](https://naija-data-api.asgatcreation.workers.dev/v1/docs) ·
OpenAPI spec: [/v1/openapi.json](https://naija-data-api.asgatcreation.workers.dev/v1/openapi.json)

```bash
curl https://naija-data-api.asgatcreation.workers.dev/v1/states/lagos/lgas
curl "https://naija-data-api.asgatcreation.workers.dev/v1/search?q=lagso"
curl "https://naija-data-api.asgatcreation.workers.dev/v1/validate/nuban?account=0000014579&bank=First%20Bank"
curl https://naija-data-api.asgatcreation.workers.dev/v1/phone/08031234567
```

```js
const res = await fetch("https://naija-data-api.asgatcreation.workers.dev/v1/states/abuja");
const { data } = await res.json();   // { code: "FC", name: "Federal Capital Territory", ... }
```

## Conventions

- Lists return `{ "count": n, "data": [...] }`; single records return `{ "data": {...} }`.
- Errors return `{ "error": { "code": "...", "message": "..." } }` with status 400 (bad parameter),
  404 (not found), 409 (ambiguous LGA name, with `candidates`), 422 (invalid phone, plate or account number)
  or 429 (too many requests).
- CORS is open to every origin, so you can call it from the browser.
- Responses can be cached for an hour and carry an `ETag`; send `If-None-Match` to get `304 Not Modified`.
- Please keep to about 120 requests per minute per IP (enforced on a best-effort basis). The service runs on
  Cloudflare's free plan; for heavy or offline use, install one of the packages instead.
- The API is versioned: `/v1` will not change in breaking ways.

See all endpoints on the [API reference](/reference/api/) page.
