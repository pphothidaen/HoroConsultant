/**
 * sw.js — HoroConsultant Service Worker for PWA Offline Caching
 * ============================================================
 * Provides offline resilience for core computation, UI styling, and i18n assets.
 * Implements aggressive cache invalidation on new version deployments.
 */

const CACHE_VERSION = 'v1.0.0.e3249d9';
const CACHE_NAME = `horoconsultant-${CACHE_VERSION}-cache`;
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/admin.html',
  '/style.css',
  '/app.js',
  '/i18n.js',
  '/voice_engine.js',
  '/version.json',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  // Force immediate activation without waiting for existing tabs to close
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[SW] Pre-caching asset warning:', err);
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  // Purge all outdated cache stores immediately
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.info(`[SW] Purging outdated cache: ${key}`);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // version.json and API requests are strictly Network-First
  if (url.pathname === '/version.json' || url.pathname.startsWith('/api/') || url.pathname.startsWith('/hitl/')) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' }).catch(() => {
        return caches.match(event.request);
      })
    );
    return;
  }

  // Network-First with Cache Fallback for navigation & HTML
  if (event.request.mode === 'navigate' || url.pathname.endsWith('.html')) {
    event.respondWith(
      fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        }
        return networkResponse;
      }).catch(() => caches.match('/index.html'))
    );
    return;
  }

  // Stale-While-Revalidate for other static assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && event.request.method === 'GET') {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
