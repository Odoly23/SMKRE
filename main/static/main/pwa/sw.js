/* SMKRE Service Worker
   - Aset static: cache uluk (cache-first)
   - App offline /sinkron/: rede uluk, se offline → kópia iha cache (pájina la iha dadus privadu)
   - Pájina seluk: rede uluk, se offline → /offline/ (dadus privadu LA rai iha cache)
   Dadus kazu offline iha IndexedDB (enkriptadu ho PIN), la iha cache ne'e. */
const VERSION = 'smkre-' + '__SW_VERSAUN__';     // Django hatama (main/views.py → service_worker)
const STATIC_CACHE = VERSION + '-static';
const APP_URL = '/sinkron/';
const PRECACHE = ['/offline/', APP_URL].concat('__SW_ASSETS__');

self.addEventListener('install', (event) => {
	// Kada file ida-ida: file ida lakon la halo instalasaun hotu falla
	event.waitUntil(caches.open(STATIC_CACHE).then((c) => Promise.all(
		PRECACHE.map((url) => c.add(new Request(url, { cache: 'reload' })).catch(() => null))
	)).then(() => self.skipWaiting()));
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
	if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/media/')) return;   // dadus privadu: rede deit

	// Static ho hash iha naran (produsaun: main.3f2a9c1b7e4d.js): cache uluk — naran muda bainhira konteúdu muda.
	// Static sein hash (DEBUG): rede uluk, cache ba offline deit — atu kódigu foun mosu kedas.
	if (url.pathname.startsWith('/static/')) {
		const guarda = (res) => {
			if (res.ok) { const copy = res.clone(); caches.open(STATIC_CACHE).then((c) => c.put(req, copy)); }
			return res;
		};
		const hashadu = /\.[0-9a-f]{12}\.[a-z0-9]+$/i.test(url.pathname);
		event.respondWith(hashadu
			? caches.match(req).then((hit) => hit || fetch(req).then(guarda))
			: fetch(req).then(guarda).catch(() => caches.match(req)));
		return;
	}

	// App offline: rede uluk (atualiza cache), offline → cache
	if (url.pathname === APP_URL) {
		event.respondWith(
			fetch(req).then((res) => {
				if (res.ok && !res.redirected) { const copy = res.clone(); caches.open(STATIC_CACHE).then((c) => c.put(APP_URL, copy)); }
				return res;
			}).catch(() => caches.match(APP_URL))
		);
		return;
	}

	// Pájina HTML seluk: rede uluk; offline → pájina offline
	if (req.mode === 'navigate') {
		event.respondWith(fetch(req).catch(() => caches.match('/offline/')));
	}
});
