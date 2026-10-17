// Minimal service worker: makes the app installable and keeps the shell cached for instant launches.
// Network-first for everything (the app is live data); the shell is served from cache only when offline.
const SHELL = 'rakshak-shell-v1';
const ASSETS = ['/', '/static/styles.css', '/static/common.js', '/static/app.js', '/static/worklet.js', '/static/icons/icon-192.png'];
self.addEventListener('install', (e) => { e.waitUntil(caches.open(SHELL).then((c) => c.addAll(ASSETS)).catch(() => null)); self.skipWaiting(); });
self.addEventListener('activate', (e) => { e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k))))); self.clients.claim(); });
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api') || url.pathname.startsWith('/ws')) return;
  e.respondWith(fetch(e.request).then((r) => { if (r.ok && (url.pathname === '/' || url.pathname.startsWith('/static'))) { const copy = r.clone(); caches.open(SHELL).then((c) => c.put(e.request, copy)); } return r; }).catch(() => caches.match(e.request)));
});
