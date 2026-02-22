const CACHE_NAME = 'ai-assistant-v2';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/img/icon-192.png',
    '/static/img/icon-512.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
});

self.addEventListener('fetch', (event) => {
    // Static assets go to cache, API calls go to network
    if (event.request.url.includes('/static/') || event.request.mode === 'navigate') {
        event.respondWith(
            caches.match(event.request).then((response) => response || fetch(event.request))
        );
    } else {
        event.respondWith(fetch(event.request));
    }
});
