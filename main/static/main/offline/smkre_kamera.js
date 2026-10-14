/* SIBAR-RbR Kámera — foto husi aplikasaun kámera HP (input capture) ka galeria; vídeo husi kámera ka galeria.
   Vídeo galeria liu 60 segundu: Investigadór hili pontu hahú, HP kota 60 segundu (grava fali liuhusi canvas).
   Foto: input capture loke aplikasaun kámera HP — servisu iha HP hotu (inklui app instaladu, iPhone).
   Vídeo: getUserMedia (para automátiku iha segundu 60); se la bele → input capture ho kontrolu
   file tenke foun (minutu 5 ikus) atu evita vídeo tuan husi galeria.
   Foto: JPEG máximu 1600px, ~1 MB · Vídeo: máximu 60 segundu, 50 MB. */
var SmkreKamera = (function () {
	'use strict';
	var FOTO_MAX_PX = 1600, FOTO_MAX_BYTES = 1024 * 1024;
	var VIDEO_MAX_S = 60, VIDEO_MAX_BYTES = 50 * 1024 * 1024;
	var FOUN_MS = 5 * 60 * 1000;

	var scr = document.getElementById('scr-kamera');
	var video = document.getElementById('kam-video');
	var btnFoti = document.getElementById('kam-foti');
	var btnTaka = document.getElementById('kam-taka');
	var timer = document.getElementById('kam-timer');

	function erru(msg) { var e = new Error(msg); e.kamera = true; return e; }

	// Kompresa imajen (canvas) → JPEG ≤ ~1 MB
	function kompresa(source, w, h) {
		var skala = Math.min(1, FOTO_MAX_PX / Math.max(w, h));
		var c = document.createElement('canvas');
		c.width = Math.round(w * skala); c.height = Math.round(h * skala);
		c.getContext('2d').drawImage(source, 0, 0, c.width, c.height);
		var kualidade = [0.8, 0.7, 0.6, 0.5];
		function tenta(i) {
			return new Promise(function (resolve) { c.toBlob(resolve, 'image/jpeg', kualidade[i]); }).then(function (blob) {
				if (blob.size > FOTO_MAX_BYTES && i < kualidade.length - 1) return tenta(i + 1);
				return blob;
			});
		}
		return tenta(0);
	}

	function videoMime() {
		var opsaun = ['video/mp4;codecs=avc1', 'video/mp4', 'video/webm;codecs=vp8,opus', 'video/webm'];
		if (!window.MediaRecorder) return null;
		for (var i = 0; i < opsaun.length; i++) { if (MediaRecorder.isTypeSupported(opsaun[i])) return opsaun[i]; }
		return '';
	}

	function taka(stream) {
		if (stream) stream.getTracks().forEach(function (t) { t.stop(); });
		video.srcObject = null;
		scr.hidden = true;
		timer.hidden = true;
		btnFoti.classList.remove('rec');
		document.body.classList.remove('kamera-loke');
	}

	// ── Kámera ho getUserMedia ──
	function kameraLive(modu) {
		var constraints = { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: modu === 'video' };
		return navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
			video.srcObject = stream;
			scr.hidden = false;
			document.body.classList.add('kamera-loke');
			btnFoti.classList.toggle('video', modu === 'video');
			return new Promise(function (resolve, reject) {
				var recorder = null, pedasu = [], interval = null;
				btnTaka.onclick = function () {
					if (recorder && recorder.state === 'recording') { recorder.onstop = null; recorder.stop(); }
					clearInterval(interval); taka(stream); resolve(null);
				};
				btnFoti.onclick = function () {
					if (modu === 'foto') {
						kompresa(video, video.videoWidth, video.videoHeight).then(function (blob) { taka(stream); resolve(blob); });
						return;
					}
					// Vídeo: klik dala 1 hahú, dala 2 para (ka automátiku iha segundu 60)
					if (recorder && recorder.state === 'recording') { recorder.stop(); return; }
					var mime = videoMime();
					if (mime === null) { taka(stream); reject(erru('HP ne\'e la suporta grava vídeo.')); return; }
					recorder = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 1500000, audioBitsPerSecond: 64000 } : undefined);
					recorder.ondataavailable = function (e) { if (e.data && e.data.size) pedasu.push(e.data); };
					recorder.onstop = function () {
						clearInterval(interval);
						var blob = new Blob(pedasu, { type: (recorder.mimeType || mime || 'video/webm').split(';')[0] });
						taka(stream);
						if (blob.size > VIDEO_MAX_BYTES) { reject(erru('Vídeo boot liu 50 MB.')); return; }
						resolve(blob);
					};
					recorder.start(1000);
					btnFoti.classList.add('rec');
					var restu = VIDEO_MAX_S;
					timer.textContent = restu; timer.hidden = false;
					interval = setInterval(function () {
						restu -= 1; timer.textContent = restu;
						if (restu <= 0 && recorder.state === 'recording') recorder.stop();
					}, 1000);
				};
			});
		});
	}

	// ── Fallback: input capture (kontrolu file foun) ──
	function kameraInput(modu) {
		var input = document.getElementById(modu === 'foto' ? 'fb-foto' : 'fb-video');
		return new Promise(function (resolve, reject) {
			input.value = '';
			input.onchange = function () {
				var f = input.files && input.files[0];
				if (!f) { resolve(null); return; }
				if (modu === 'video' && f.lastModified && Date.now() - f.lastModified > FOUN_MS) { reject(erru('Vídeo tenke grava agora husi kámera (la husi galeria).')); return; }
				var url = URL.createObjectURL(f);
				if (modu === 'foto') {
					var img = new Image();
					img.onload = function () { kompresa(img, img.naturalWidth, img.naturalHeight).then(function (b) { URL.revokeObjectURL(url); resolve(b); }); };
					img.onerror = function () { URL.revokeObjectURL(url); reject(erru('Foto la bele loke.')); };
					img.src = url;
				} else {
					var v = document.createElement('video');
					v.preload = 'metadata';
					v.onloadedmetadata = function () {
						URL.revokeObjectURL(url);
						if (v.duration > VIDEO_MAX_S + 1) { reject(erru('Vídeo máximu 60 segundu.')); return; }
						if (f.size > VIDEO_MAX_BYTES) { reject(erru('Vídeo boot liu 50 MB.')); return; }
						resolve(f);
					};
					v.onerror = function () { URL.revokeObjectURL(url); reject(erru('Vídeo la bele loke.')); };
					v.src = url;
				}
			};
			input.click();
		});
	}

	function foti(modu) {
		// Foto: aplikasaun kámera HP direta (estável liu kámera iha browser)
		if (modu === 'foto') return kameraInput('foto');
		if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
			return kameraLive(modu).catch(function (e) {
				if (e && e.kamera) throw e;
				throw erru(e && e.name === 'NotAllowedError'
					? 'Favor permite kámera' + (modu === 'video' ? ' no mikrofone' : '') + ' ba SIBAR-RbR iha setting browser.'
					: 'Kámera la bele loke. Taka app seluk ne\'ebé uza kámera no koko fali.');
			});
		}
		return kameraInput(modu);                // browser tuan: input capture (iha klik nia laran)
	}

	// ── Galeria: hili foto barak (máximu `restu`), kompresa hanesan kámera ──
	function galeria(restu) {
		var input = document.getElementById('fb-galeria');
		return new Promise(function (resolve, reject) {
			input.value = '';
			input.onchange = function () {
				var files = Array.prototype.slice.call(input.files || []).filter(function (f) { return /^image\//.test(f.type); });
				var liu = Math.max(0, files.length - restu);
				Promise.all(files.slice(0, restu).map(function (f) {
					return new Promise(function (ok) {
						var url = URL.createObjectURL(f), img = new Image();
						img.onload = function () { kompresa(img, img.naturalWidth, img.naturalHeight).then(function (b) { URL.revokeObjectURL(url); ok(b); }); };
						img.onerror = function () { URL.revokeObjectURL(url); ok(null); };     // file la'ós imajen: hakat
						img.src = url;
					});
				})).then(function (blobs) { resolve({ blobs: blobs.filter(Boolean), liu: liu }); }, reject);
			};
			input.click();
		});
	}

	// ── Vídeo husi galeria: hili file; se ≤ 60 s no ≤ 50 MB rai direta, se lae presiza kota ──
	function videoGaleria() {
		var input = document.getElementById('fb-video-galeria');
		return new Promise(function (resolve, reject) {
			input.value = '';
			input.onchange = function () {
				var f = input.files && input.files[0];
				if (!f) { resolve(null); return; }
				var url = URL.createObjectURL(f), v = document.createElement('video');
				v.preload = 'metadata';
				v.onloadedmetadata = function () {
					URL.revokeObjectURL(url);
					var d = v.duration;
					if (!isFinite(d) || d <= 0) { reject(erru('Vídeo la bele lee durasaun.')); return; }
					resolve({ file: f, durasaun: d, presizaKota: d > VIDEO_MAX_S + 1 || f.size > VIDEO_MAX_BYTES });
				};
				v.onerror = function () { URL.revokeObjectURL(url); reject(erru('Vídeo la bele loke iha HP ne\'e.')); };
				v.src = url;
			};
			input.click();
		});
	}

	// ── Kota vídeo: halimar parte [hahu, hahu+60] no grava fali (canvas + WebAudio) ──
	// La presiza biblioteka: servisu iha Chrome Android no Safari. Durasaun prosesu = durasaun parte.
	function kota(file, hahu, progresu) {
		var mime = videoMime();
		if (mime === null) return Promise.reject(erru('HP ne\'e la suporta kota vídeo.'));
		var url = URL.createObjectURL(file);
		var v = document.createElement('video');
		v.playsInline = true; v.preload = 'auto'; v.src = url;
		return new Promise(function (resolve, reject) {
			var audioCtx = null, recorder = null, pedasu = [], rAF = null;
			function remata(erro, blob) {
				cancelAnimationFrame(rAF);
				v.pause(); URL.revokeObjectURL(url);
				if (audioCtx) audioCtx.close();
				if (erro) reject(erro); else resolve(blob);
			}
			v.onerror = function () { remata(erru('Vídeo la bele loke.')); };
			v.onloadedmetadata = function () {
				var naruk = Math.min(VIDEO_MAX_S, v.duration - hahu);
				var skala = Math.min(1, 1280 / Math.max(v.videoWidth, v.videoHeight));
				var c = document.createElement('canvas');
				c.width = Math.round(v.videoWidth * skala) || 640; c.height = Math.round(v.videoHeight * skala) || 360;
				var ctx = c.getContext('2d');
				var stream = c.captureStream(30);
				try {                                   // audio: la sai iha altifalante, tama ba gravasaun deit
					var AC = window.AudioContext || window.webkitAudioContext;
					audioCtx = new AC();
					var dest = audioCtx.createMediaStreamDestination();
					audioCtx.createMediaElementSource(v).connect(dest);
					dest.stream.getAudioTracks().forEach(function (t) { stream.addTrack(t); });
				} catch (e) { v.muted = true; }        // la iha audio → vídeo de'it
				v.onseeked = function () {
					v.onseeked = null;
					recorder = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 1500000, audioBitsPerSecond: 64000 } : undefined);
					recorder.ondataavailable = function (e) { if (e.data && e.data.size) pedasu.push(e.data); };
					recorder.onstop = function () {
						var blob = new Blob(pedasu, { type: (recorder.mimeType || mime || 'video/webm').split(';')[0] });
						if (blob.size > VIDEO_MAX_BYTES) { remata(erru('Vídeo boot liu 50 MB.')); return; }
						remata(null, blob);
					};
					function pinta() {
						ctx.drawImage(v, 0, 0, c.width, c.height);
						var pasa = v.currentTime - hahu;
						if (progresu) progresu(Math.min(1, pasa / naruk));
						if (pasa >= naruk || v.ended) { if (recorder.state === 'recording') recorder.stop(); return; }
						rAF = requestAnimationFrame(pinta);
					}
					v.onended = function () { if (recorder.state === 'recording') recorder.stop(); };
					if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
					v.play().then(function () { recorder.start(1000); pinta(); }, function () { remata(erru('Vídeo la bele halimar. Koko fali.')); });
				};
				v.currentTime = hahu;
			};
		});
	}

	return {
		galeria: galeria,
		videoGaleria: videoGaleria,
		kota: kota,
		VIDEO_MAX_S: VIDEO_MAX_S,
		foto: function () { return foti('foto'); },
		video: function () { return foti('video'); }
	};
})();
