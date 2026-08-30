// K-2 Command Center Service Worker
const CACHE_NAME = 'k2-hq-v64-pr-backlog';
const ASSETS = [
  './',
  './index.html',
  './favicon.svg',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(c =>
      Promise.all(ASSETS.map(a => c.add(a).catch(err => console.warn('sw: skip', a, err))))
    )
  );
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

// ---------------------------------------------------------------------------
// WEB PUSH — reminders on the phone. iOS only delivers these to a PWA that was
// added to the Home Screen, and only if we show a notification for every push
// (no silent pushes), so there is no early return here.
// ---------------------------------------------------------------------------
self.addEventListener('push', (e) => {
  let d = { title: '⏰ Reminder', body: '', url: './#reminders' };
  try {
    if (e.data) d = Object.assign(d, e.data.json());
  } catch (err) {
    if (e.data) d.body = e.data.text();   // non-JSON payload — still worth showing
  }
  e.waitUntil(self.registration.showNotification(d.title, {
    body: d.body,
    icon: './icon-192.png',
    badge: './icon-192.png',
    data: { url: d.url },
    tag: d.tag || undefined
  }));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    for (const c of list) {
      // reuse an already-open dashboard rather than stacking windows
      if (c.url.includes('/k2-dashboard') && 'focus' in c) {
        if ('navigate' in c) { try { c.navigate(url); } catch (err) {} }
        return c.focus();
      }
    }
    return self.clients.openWindow(url);
  }));
});
