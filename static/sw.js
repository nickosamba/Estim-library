const CACHE_NAME = 'estim-library-v5'; // Cache version incremented to reflect changes in caching strategy
const ASSETS_TO_CACHE = [
  '/',
  '/static/vendor/pdfjs/pdf.mjs',
  'https://cdn.tailwindcss.com?plugins=forms,container-queries',
  'https://unpkg.com/htmx.org@1.9.10',
  'https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js',
  'https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Merriweather:wght@400;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap'
];

// Installation : Mise en cache des ressources critiques
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('PWA: Caching critical assets');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting(); // Forcer l'activation du nouveau SW immédiatement
});

// Activation : Nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('PWA: Clearing old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Stratégie Stale-While-Revalidate : 
// Servir depuis le cache instantanément, puis mettre à jour en arrière-plan.
self.addEventListener('fetch', (event) => {
  // Ignorer les requêtes non-GET et les requêtes vers le panel admin ou chrome-extension
  if (event.request.method !== 'GET' || 
      event.request.url.includes('/admin/') || 
      event.request.url.startsWith('chrome-extension')) {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.match(event.request).then((cachedResponse) => {
        const fetchedResponse = fetch(event.request).then((networkResponse) => {
          // Ne mettre en cache que les succès et éviter les fichiers média/PDF volumineux
          const isPdf = event.request.url.endsWith('.pdf');
          const isMedia = event.request.url.includes('/media/');
          
          if (networkResponse.status === 200 && !isPdf && !isMedia) {
            cache.put(event.request, networkResponse.clone());
          }
          return networkResponse;
        }).catch(() => {
          // En cas d'échec total (hors ligne), renvoyer la réponse du cache
          return cachedResponse;
        });

        // Renvoyer la réponse du cache si elle existe, sinon attendre le réseau
        return cachedResponse || fetchedResponse;
      });
    })
  );
});
