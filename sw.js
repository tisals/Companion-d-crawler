// Service Worker de Kikin Battles.
// Estrategia: Network-First (el archivo más reciente se ve al instante) con respaldo en caché.
// El "shell" de la app se precachea al instalar para que abra offline en el celular.

const CACHE_NAME = 'kikin-battles-v25';

// Archivos indispensables para que la app arranque sin conexión.
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './tiles_metadata.json',
  './iconos/icono-192.png',
  './iconos/icono-512.png',
  './iconos/icono-maskable-512.png',
  './iconos/apple-touch-icon.png',
  './iconos/favicon-32.png',
  './vendor/tailwind.js'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  // Cada archivo se cachea por separado: que uno falle (ej. el CDN sin CORS)
  // no puede impedir que se guarde el resto del shell.
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.allSettled(SHELL.map((url) => cache.add(url)))
    )
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

// Network-First: primero pide el archivo más reciente (para ver cambios al instante).
// Si no hay red o está offline, usa la copia en caché.
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  // El código de la app se revalida SIEMPRE contra el servidor. Sin esto, el
  // navegador puede responder con un index.html viejo desde su caché HTTP
  // (GitHub Pages manda max-age=60) y la PWA seguiría mostrando la versión
  // anterior después de un deploy.
  const url = new URL(event.request.url);
  const esCodigo = event.request.mode === 'navigate'
    || /\.(?:html|js|json|webmanifest)$/i.test(url.pathname);

  const pedir = esCodigo
    ? fetch(event.request, { cache: 'no-cache' })
    : fetch(event.request);

  event.respondWith(
    pedir
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});
