/* eslint-env node */
import express from 'express';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const app = express();
const port = Number(process.env.PORT || 4173);
const tikTokAccessTokenUrl = 'https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/';
const rootDir = dirname(fileURLToPath(import.meta.url));
const distDir = resolve(rootDir, 'dist');
const publicDir = resolve(rootDir, 'public');
const staticRoot = existsSync(distDir) ? distDir : publicDir;
const indexHtmlPath = join(staticRoot, 'index.html');
const tikTokCallbackPath = join(staticRoot, 'tiktok', 'callback', 'index.html');

app.disable('x-powered-by');
app.use('/api', (_req, res, next) => {
  res.set('Cache-Control', 'no-store');
  next();
});
app.use(express.json({ limit: '12kb' }));

function isAuthorizedExchangeRequest(req) {
  const adminSecret = process.env.TIKTOK_EXCHANGE_ADMIN_SECRET;

  if (!adminSecret) {
    return true;
  }

  return (
    req.get('x-admin-secret') === adminSecret ||
    req.get('authorization') === `Bearer ${adminSecret}`
  );
}

app.post('/api/tiktok/exchange-token', async (req, res) => {
  const appId = process.env.TIKTOK_APP_ID;
  const appSecret = process.env.TIKTOK_APP_SECRET;
  const missing = [];

  if (!isAuthorizedExchangeRequest(req)) {
    res.status(401).json({
      error: 'unauthorized',
      message: 'Token exchange requires a valid admin secret.',
    });
    return;
  }

  if (!appId) missing.push('TIKTOK_APP_ID');
  if (!appSecret) missing.push('TIKTOK_APP_SECRET');

  if (missing.length > 0) {
    res.status(500).json({
      error: 'server_not_configured',
      message: 'TikTok token exchange environment variables are missing.',
      missing,
    });
    return;
  }

  const authCode = typeof req.body?.auth_code === 'string' ? req.body.auth_code.trim() : '';

  if (!authCode) {
    res.status(400).json({
      error: 'missing_auth_code',
      message: 'Request body must include auth_code.',
    });
    return;
  }

  try {
    const tikTokResponse = await fetch(tikTokAccessTokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        app_id: appId,
        secret: appSecret,
        auth_code: authCode,
      }),
    });
    const contentType = tikTokResponse.headers.get('content-type') || 'application/json; charset=utf-8';
    const responseText = await tikTokResponse.text();

    res
      .status(tikTokResponse.status)
      .set({
        'Cache-Control': 'no-store',
        'Content-Type': contentType,
      })
      .send(responseText);
  } catch {
    res.status(502).json({
      error: 'tiktok_exchange_failed',
      message: 'Could not reach TikTok token exchange endpoint.',
    });
  }
});

app.all('/api/tiktok/exchange-token', (_req, res) => {
  res.set('Allow', 'POST');
  res.status(405).json({
    error: 'method_not_allowed',
    message: 'Use POST.',
  });
});

app.get(['/tiktok/callback', '/tiktok/callback/'], (_req, res) => {
  res.sendFile(tikTokCallbackPath);
});

app.use(express.static(staticRoot));

app.use('/api', (_req, res) => {
  res.status(404).json({ error: 'not_found' });
});

app.use((_req, res) => {
  res.sendFile(indexHtmlPath);
});

app.use((error, _req, res, next) => {
  if (error instanceof SyntaxError && 'body' in error) {
    res.status(400).json({
      error: 'invalid_request_body',
      message: 'Request body must be valid JSON.',
    });
    return;
  }

  if (error.type === 'entity.too.large') {
    res.status(413).json({
      error: 'request_body_too_large',
      message: 'Request body must be 12kb or smaller.',
    });
    return;
  }

  next(error);
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server listening on port ${port}`);
});
