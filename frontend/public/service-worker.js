/*
 * Retirement worker for an older cached/PWA build of the site.
 *
 * Golden Touch no longer registers a service worker. Browsers that visited an
 * earlier build may nevertheless keep the old worker alive and combine stale
 * JavaScript with current Next.js HTML, causing hydration failures. Serving
 * this worker at the old URL lets those browsers update once, remove the old
 * caches and registration, and reload controlled pages with current assets.
 */
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));
      await self.registration.unregister();

      const clients = await self.clients.matchAll({
        includeUncontrolled: true,
        type: "window",
      });
      await Promise.all(clients.map((client) => client.navigate(client.url)));
    })(),
  );
});
