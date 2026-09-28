/* SMKRE Kripto — enkriptasaun dadus iha HP ho PIN (WebCrypto).
   PIN (númeru 6) + salt → PBKDF2-SHA256 (310.000 iterasaun) → xavi AES-256-GCM.
   Xavi la bele esporta (non-extractable) no hela iha memória deit bainhira app loke. */
var SmkreKripto = (function () {
	'use strict';
	var ITERASAUN = 310000;
	var enc = new TextEncoder(), dec = new TextDecoder();

	function randomBytes(n) { return crypto.getRandomValues(new Uint8Array(n)); }

	function uuid() {
		if (crypto.randomUUID) return crypto.randomUUID();
		var b = randomBytes(16);
		b[6] = (b[6] & 0x0f) | 0x40; b[8] = (b[8] & 0x3f) | 0x80;
		var h = Array.prototype.map.call(b, function (x) { return ('0' + x.toString(16)).slice(-2); }).join('');
		return h.slice(0, 8) + '-' + h.slice(8, 12) + '-' + h.slice(12, 16) + '-' + h.slice(16, 20) + '-' + h.slice(20);
	}

	// PIN → xavi AES-256
	function deriveKey(pin, salt) {
		return crypto.subtle.importKey('raw', enc.encode(pin), 'PBKDF2', false, ['deriveKey']).then(function (base) {
			return crypto.subtle.deriveKey(
				{ name: 'PBKDF2', salt: salt, iterations: ITERASAUN, hash: 'SHA-256' },
				base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
		});
	}

	// Enkripta ArrayBuffer → {iv, ct}
	function encryptBuffer(key, buf) {
		var iv = randomBytes(12);
		return crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, key, buf).then(function (ct) { return { iv: iv, ct: ct }; });
	}

	function decryptBuffer(key, box) {
		return crypto.subtle.decrypt({ name: 'AES-GCM', iv: box.iv }, key, box.ct);
	}

	// Objetu JSON
	function encryptJSON(key, obj) { return encryptBuffer(key, enc.encode(JSON.stringify(obj))); }
	function decryptJSON(key, box) { return decryptBuffer(key, box).then(function (b) { return JSON.parse(dec.decode(b)); }); }

	// Blob (foto / vídeo)
	function encryptBlob(key, blob) {
		return blob.arrayBuffer().then(function (buf) { return encryptBuffer(key, buf); });
	}
	function decryptBlob(key, box, mime) {
		return decryptBuffer(key, box).then(function (buf) { return new Blob([buf], { type: mime }); });
	}

	return {
		randomBytes: randomBytes, uuid: uuid, deriveKey: deriveKey,
		encryptJSON: encryptJSON, decryptJSON: decryptJSON, encryptBlob: encryptBlob, decryptBlob: decryptBlob
	};
})();
