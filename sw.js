const CACHE = 'pic-v1';
const ASSETS = [
  '/Pinellasiceco/',
  '/Pinellasiceco/index.html',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Network first for the main HTML (always get fresh data)
  // Cache fallback if offline
  if (e.request.url.includes('index.html') || e.request.url.endsWith('/Pinellasiceco/')) {
    e.respondWith(
      fetch(e.request)
        .then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  // Cache first for everything else (Leaflet, fonts)
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
