/* SMKRE Kámera — foto no vídeo husi kámera HP deit (la husi galeria).
   Uza getUserMedia (Android Chrome, iOS Safari 14.3+). Se la bele → input capture ho kontrolu:
   file tenke foun (minutu 5 ikus) atu evita foto tuan husi galeria.
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
				if (Date.now() - f.lastModified > FOUN_MS) { reject(erru('Foto/vídeo tenke foti agora husi kámera (la husi galeria).')); return; }
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
		if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
			return kameraLive(modu).catch(function (e) {
				if (e && e.kamera) throw e;
				throw erru(e && e.name === 'NotAllowedError'
					? 'Favor permite kámera' + (modu === 'video' ? ' no mikrofone' : '') + ' ba SMKRE iha setting browser.'
					: 'Kámera la bele loke. Taka app seluk ne\'ebé uza kámera no koko fali.');
			});
		}
		return kameraInput(modu);                // browser tuan: input capture (iha klik nia laran)
	}

	return {
		foto: function () { return foti('foto'); },
		video: function () { return foti('video'); }
	};
})();
