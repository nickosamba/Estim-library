const CACHE_NAME = 'estim-library-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/vendor/pdfjs/pdf.mjs',
  'https://cdn.tailwindcss.com?plugins=forms,container-queries',
  'https://unpkg.com/htmx.org@1.9.10',
  'https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js',
  'https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Merriweather:wght@400;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
