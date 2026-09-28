/* SMKRE Service Worker — faze 1: cache aset static + pájina offline.
   Formuláriu offline (IndexedDB + sinkron) sei aumenta iha faze 4. */
const VERSION = 'smkre-v1';
const STATIC_CACHE = VERSION + '-static';
const PRECACHE = [
	'/offline/',
	'/static/main/css/bootstrap.min.css',
	'/static/main/css/main.css',
	'/static/main/css/fonts.css',
	'/static/main/font-awesome/css/font-awesome.min.css',
	'/static/main/js/jquery.min.js',
	'/static/main/js/bootstrap.bundle.min.js',
	'/static/main/js/main.js',
	'/static/main/images/logo.png',
];

self.addEventListener('install', (event) => {
	event.waitUntil(caches.open(STATIC_CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) => Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const req = event.request;
	if (req.method !== 'GET') return;
	const url = new URL(req.url);
	if (url.origin !== self.location.origin) return;

	// Static: cache uluk, depois rede (cache-first)
	if (url.pathname.startsWith('/static/')) {
		event.respondWith(
			caches.match(req).then((hit) => hit || fetch(req).then((res) => {
				const copy = res.clone();
				caches.open(STATIC_CACHE).then((c) => c.put(req, copy));
				return res;
			}))
		);
		return;
	}

	// Pájina HTML: rede uluk; se offline → pájina offline (dadus privadu LA rai iha cache)
	if (req.mode === 'navigate') {
		event.respondWith(fetch(req).catch(() => caches.match('/offline/')));
	}
});
