/* SMKRE DB — IndexedDB iha HP.
   meta  : {k, v}                       (salt, verifikadór PIN, token, opsaun — enkriptadu)
   kazu  : {id, estadu, kria_iha, atualiza, kode, erru, box}   box = dadus kazu enkriptadu
   media : {id, kazu_id, tipu, mime, tamanu, box}              box = foto/vídeo enkriptadu
   Estadu kazu: RASCUNHO → PRONTU (hein sinkron) → SINKRON (server simu). ERRU = server rejeita, hadia. */
var SmkreDB = (function () {
	'use strict';
	var NARAN = 'smkre-offline', VERSAUN = 1;
	var dbPromise = null;

	function open() {
		if (dbPromise) return dbPromise;
		dbPromise = new Promise(function (resolve, reject) {
			var req = indexedDB.open(NARAN, VERSAUN);
			req.onupgradeneeded = function () {
				var db = req.result;
				if (!db.objectStoreNames.contains('meta')) db.createObjectStore('meta', { keyPath: 'k' });
				if (!db.objectStoreNames.contains('kazu')) db.createObjectStore('kazu', { keyPath: 'id' });
				if (!db.objectStoreNames.contains('media')) {
					db.createObjectStore('media', { keyPath: 'id' }).createIndex('kazu_id', 'kazu_id');
				}
			};
			req.onsuccess = function () { resolve(req.result); };
			req.onerror = function () { reject(req.error); };
		});
		return dbPromise;
	}

	function tx(store, mode, fn) {
		return open().then(function (db) {
			return new Promise(function (resolve, reject) {
				var t = db.transaction(store, mode);
				var result = fn(t.objectStore(store));
				t.oncomplete = function () { resolve(result instanceof IDBRequest ? result.result : undefined); };
				t.onerror = function () { reject(t.error); };
				t.onabort = function () { reject(t.error); };
			});
		});
	}

	function get(store, key) { return tx(store, 'readonly', function (s) { return s.get(key); }); }
	function put(store, obj) { return tx(store, 'readwrite', function (s) { s.put(obj); }); }
	function del(store, key) { return tx(store, 'readwrite', function (s) { s.delete(key); }); }
	function all(store) { return tx(store, 'readonly', function (s) { return s.getAll(); }); }

	function mediaKazu(kazuId) {
		return tx('media', 'readonly', function (s) { return s.index('kazu_id').getAll(kazuId); });
	}

	function hamoosMediaKazu(kazuId) {
		return mediaKazu(kazuId).then(function (lista) {
			return tx('media', 'readwrite', function (s) { lista.forEach(function (m) { s.delete(m.id); }); });
		});
	}

	// Meta
	function metaGet(k) { return get('meta', k).then(function (r) { return r ? r.v : null; }); }
	function metaSet(k, v) { return put('meta', { k: k, v: v }); }

	// Hamoos dadus hotu iha HP (haluha PIN / sala PIN dala 5)
	function wipe() {
		return open().then(function (db) {
			db.close();
			dbPromise = null;
			return new Promise(function (resolve) {
				var req = indexedDB.deleteDatabase(NARAN);
				req.onsuccess = req.onerror = req.onblocked = function () { resolve(); };
			});
		});
	}

	return {
		get: get, put: put, del: del, all: all, mediaKazu: mediaKazu, hamoosMediaKazu: hamoosMediaKazu,
		metaGet: metaGet, metaSet: metaSet, wipe: wipe
	};
})();
