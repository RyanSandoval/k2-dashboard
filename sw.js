// K-2 Command Center Service Worker
const CACHE_NAME = 'k2-hq-v1';
const ASSETS = [
  '/k2-dashboard/',
  '/k2-dashboard/index.html',
  '/k2-dashboard/favicon.svg',
  '/k2-dashboard/manifest.json',
  '/k2-dashboard/icon-192.png',
  '/k2-dashboard/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => 
    Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Network-first for API calls, cache-first for assets
  if (e.request.url.includes('api.github.com')) return;
  e.respondWith(
    fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      return res;
    }).catch(() => caches.match(e.request))
  );
});
