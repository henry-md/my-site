# TikTok Business OAuth Callback And Exchange

## Context

This site supports the first step of TikTok for Business / TikTok Ads API OAuth. The TikTok Developers app needs this redirect URL:

```text
https://henry-deutsch.com/tiktok/callback
```

After authorization, TikTok redirects back with query parameters such as:

```text
?auth_code=...&state=...
```

The callback page captures and displays the short-lived `auth_code`. The Express server can also exchange that code for TikTok's OAuth token response through a server-only endpoint, keeping `TIKTOK_APP_SECRET` out of browser code.

Most future TikTok Ads API calls will use the returned `access_token` in the `Access-Token` header plus an `advertiser_id`.

## Hosting Shape

The site is a Vite + React frontend deployed on Railway. Vite still builds the browser app into `dist/`, but Railway now runs an always-on Node/Express process:

```text
npm run build
npm start
```

`npm start` runs:

```text
node server.js
```

The Express process serves the built Vite site and handles API routes from the same Railway service.

## Implemented Files

### `public/tiktok/callback/index.html`

Standalone static utility page for:

```text
/tiktok/callback
/tiktok/callback/
```

Behavior:

- Reads query parameters from `window.location.search` using `URLSearchParams`.
- Handles `auth_code`.
- Handles `state`.
- Handles TikTok error fields:
  - `error`
  - `error_description`
- If `auth_code` is present, shows a success page with the code in a code block, a copy button, state if present, and a short-lived-code warning.
- If an error is present, shows a clear error page.
- If no code or error is present, shows "No authorization code found" and lists received query parameters.

Safety details:

- Renders dynamic values with `textContent`.
- Does not log, persist, send, or store the `auth_code`.
- Does not load the main portfolio page's analytics.

### `server.js`

Express server used by Railway.

Responsibilities:

- Parses JSON request bodies with a small `12kb` limit.
- Serves the built Vite app from `dist/`.
- Falls back to `public/` if `dist/` does not exist, which is useful for local callback checks before a build.
- Serves `/tiktok/callback` and `/tiktok/callback/` with the callback HTML.
- Handles `POST /api/tiktok/exchange-token`.
- Returns JSON 404s for unknown `/api/*` routes.
- Disables the `X-Powered-By` header.
- Adds `Cache-Control: no-store` for API responses.

Token exchange endpoint:

```http
POST /api/tiktok/exchange-token
Content-Type: application/json
Authorization: Bearer <TIKTOK_EXCHANGE_ADMIN_SECRET>

{
  "auth_code": "<auth_code>"
}
```

Equivalent admin-secret header:

```http
x-admin-secret: <TIKTOK_EXCHANGE_ADMIN_SECRET>
```

The server sends TikTok:

```json
{
  "app_id": "process.env.TIKTOK_APP_ID",
  "secret": "process.env.TIKTOK_APP_SECRET",
  "auth_code": "<auth_code>"
}
```

TikTok endpoint:

```text
https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/
```

The response from TikTok is proxied back to the caller with `Cache-Control: no-store`.

### `package.json`

Updated for Railway/server hosting:

- Added `express`.
- Changed `start` to `node server.js`.
- Removed old GitHub Pages deploy scripts:
  - `predeploy`
  - `deploy`
- Removed the stale `gh-pages` dev dependency.

### `vite.config.js`

Keeps a tiny Vite dev/preview middleware so local Vite-only development serves the callback HTML at both:

```text
/tiktok/callback
/tiktok/callback/
```

Production serving is handled by Express in `server.js`.

### `.env.example`

Documents Railway/local environment variables:

```text
TIKTOK_APP_ID=
TIKTOK_APP_SECRET=
TIKTOK_REDIRECT_URI=https://henry-deutsch.com/tiktok/callback
TIKTOK_EXCHANGE_ADMIN_SECRET=
```

`TIKTOK_REDIRECT_URI` is documented for consistency with the TikTok app setup. The current exchange call only sends `app_id`, `secret`, and `auth_code`, matching the known TikTok Business API token exchange shape.

## Railway Environment Variables

Set these in Railway:

```text
TIKTOK_APP_ID
TIKTOK_APP_SECRET
TIKTOK_REDIRECT_URI
TIKTOK_EXCHANGE_ADMIN_SECRET
```

`TIKTOK_EXCHANGE_ADMIN_SECRET` is recommended. Without it, the exchange endpoint still works, but anyone who can reach the endpoint could attempt to submit auth codes for exchange.

## Verification Performed

Ran:

```text
npm run lint
npm run build
```

Both passed.

Started Express locally:

```text
PORT=4181 TIKTOK_APP_ID=test-app TIKTOK_APP_SECRET=test-secret TIKTOK_EXCHANGE_ADMIN_SECRET=local-secret npm start
```

Verified callback serving:

```text
http://127.0.0.1:4181/tiktok/callback?auth_code=test123&state=teststate
http://127.0.0.1:4181/tiktok/callback?error=access_denied&error_description=Denied%20by%20user&state=teststate
http://127.0.0.1:4181/tiktok/callback?foo=bar
```

The success callback was also verified in Chromium with a screenshot saved at:

```text
/tmp/job-helper-verify-page/tiktok-callback-endpoint-retest.png
```

Verified exchange endpoint guard:

```text
POST http://127.0.0.1:4181/api/tiktok/exchange-token
```

Without the admin secret, the endpoint returns `401 unauthorized`.

Verified request validation:

```text
POST http://127.0.0.1:4181/api/tiktok/exchange-token
x-admin-secret: local-secret

{}
```

This returns `400 missing_auth_code`.

Additional endpoint checks:

- Invalid JSON returns `400 invalid_request_body`.
- `GET /api/tiktok/exchange-token` returns `405 method_not_allowed` with `Allow: POST`.
- Unknown API routes such as `/api/nope` return JSON `404 not_found`.
- API responses include `Cache-Control: no-store`.

With fake local credentials and a fake `auth_code`, the exchange endpoint reached TikTok's real token endpoint and TikTok returned its own validation error for the invalid test `app_id`. This confirms the proxy path is wired. A real token exchange still needs real Railway environment variables and a real short-lived TikTok `auth_code`.

## Security Notes

The callback page displays `auth_code` because that is the purpose of this private utility route. It does not treat the code as a long-lived token.

The server-side endpoint may return TikTok's token response, including `access_token` and `refresh_token`, to whoever successfully calls it. Keep `TIKTOK_EXCHANGE_ADMIN_SECRET` private and do not call the endpoint from public browser code unless a more complete authenticated admin UI exists.

Do not log:

- `auth_code`
- `access_token`
- `refresh_token`
- `TIKTOK_APP_SECRET`
- `TIKTOK_EXCHANGE_ADMIN_SECRET`

## What Remains

1. Configure Railway environment variables.

2. Confirm Railway uses the normal build/start flow:

   ```text
   npm run build
   npm start
   ```

3. Register this exact redirect URL in TikTok for Business Developers:

   ```text
   https://henry-deutsch.com/tiktok/callback
   ```

4. Run a real TikTok OAuth authorization flow and confirm the callback page displays the real `auth_code`.

5. Exchange the real code through:

   ```text
   POST https://henry-deutsch.com/api/tiktok/exchange-token
   ```

6. Decide what should happen to returned tokens after the manual test succeeds.

   Current endpoint returns the token response but does not persist it. A future production workflow should decide whether tokens belong in a secure database, Railway variable rotation workflow, a local admin-only script, or another private storage system.
