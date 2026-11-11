// Ledger offline support: keeps the app's own files on the phone so it opens without internet.
// Your data is cached separately by Firebase (IndexedDB) and syncs when you're back online.
const CACHE = 'ledger-shell-v1.5.0';
const SHELL = ['./', './index.html', './manifest.json', './logo.svg', './apple-touch-icon.png', './icons/icon-192.png', './icons/icon-512.png'];
// third-party files the app needs (Firebase SDK, fonts, spreadsheet import)
const CDN = /^https:\/\/(www\.gstatic\.com\/firebasejs|fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.jsdelivr\.net)\//;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('ledger-shell-') && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;                       // never touch writes / AI calls
  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  if (!sameOrigin && !CDN.test(req.url)) return;          // Firestore, Gemini, FX APIs go straight to the network

  // The page itself: network first (so updates arrive), fall back to the cached copy when offline.
  if (req.mode === 'navigate' || (sameOrigin && /\/(index\.html)?$/.test(url.pathname))) {
    e.respondWith(
      fetch(req).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put('./index.html', copy)); return res; })
        .catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  // Everything else (icons, fonts, Firebase SDK): serve cached, refresh in the background.
  e.respondWith(
    caches.match(req).then(cached => {
      const net = fetch(req).then(res => {
        if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => cached);
      return cached || net;
    })
  );
});
