import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { createReadStream } from 'node:fs'
import { resolve } from 'node:path'

const tikTokCallbackHtml = resolve('public/tiktok/callback/index.html')

function tikTokCallbackMiddleware() {
  return {
    name: 'tiktok-callback-middleware',
    configureServer(server) {
      server.middlewares.use(serveTikTokCallback)
    },
    configurePreviewServer(server) {
      server.middlewares.use(serveTikTokCallback)
    },
  }
}

function serveTikTokCallback(req, res, next) {
  const path = (req.url || '').split('?')[0]

  if (path !== '/tiktok/callback' && path !== '/tiktok/callback/') {
    next()
    return
  }

  res.statusCode = 200
  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  createReadStream(tikTokCallbackHtml).pipe(res)
}

// https://vitejs.dev/config/
export default defineConfig({
  base: "/",
  plugins: [tikTokCallbackMiddleware(), react()],
})
