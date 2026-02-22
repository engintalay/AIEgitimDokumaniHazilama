const CACHE_NAME = 'ai-assistant-v3';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/css/themes.css',
    '/static/js/app.js',
    '/static/img/icon-192.png',
    '/static/img/icon-512.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
    self.skipWaiting(); // Force activate immediately
});

self.addEventListener('activate', (event) => {
    // Delete old caches
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // Network first for JS/CSS to always get latest
    if (event.request.url.includes('/static/js/') || event.request.url.includes('/static/css/')) {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
    } else if (event.request.url.includes('/static/') || event.request.mode === 'navigate') {
        event.respondWith(
            caches.match(event.request).then((response) => response || fetch(event.request))
        );
    } else {
        event.respondWith(fetch(event.request));
    }
});
