# naija-data API (Cloudflare Worker)

Free, read-only REST API built on the `naija-data` JavaScript package, so its answers match the
Python, JavaScript and Go packages exactly.

- Versioned under `/v1`; interactive docs at `/v1/docs`, OpenAPI spec at `/v1/openapi.json`.
- JSON everywhere; errors are `{"error": {"code", "message"}}` with 400/404/409/422/429 statuses.
- CORS open to all origins; read-only (`GET`, `HEAD`, `OPTIONS`).
- Cached for an hour in browsers and a day at Cloudflare's edge; `ETag` supports `304 Not Modified`.
- Rate limited to 120 requests per minute per IP (Cloudflare rate limiting binding). `/v1/health` is
  never limited or cached.

## Develop

```bash
cd packages/js && npm ci && npm run build   # the API uses the built package
cd ../../api && npm ci
npm test        # bundles the Worker and calls every endpoint
npm run dev     # local server at http://localhost:8787/v1
```

## Deploy

Deploys run automatically from GitHub Actions (`.github/workflows/deploy-api.yml`) after CI passes
on `main`, once the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` secrets are set. A manual
deploy is `npx wrangler login` once, then `npm run deploy`.
