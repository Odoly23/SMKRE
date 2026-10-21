/* SIBAR-RbR Offline — Survei Legál (Perguntas Xave Sira Legal) ba Ofisiál Legál.
   Uza app offline nia login, PIN, enkriptasaun no sinkron (smkre_offline.js → window.SmkreApp).
   Survei rai iha store 'kazu' ho legal: true; foto / dokumentu iha store 'media' (enkriptadu).
   Fluxu: Input (5 pasu) → Prontu → Sinkron: survei JSON → file ida-ida → haruka (Hein Verifikasaun Admin). */
var SmkreLegal = (function () {
	'use strict';
	var A = window.SmkreApp, K = SmkreKripto, DB = SmkreDB, KAM = SmkreKamera, B = document.body.dataset;
	if (!A) return null;
	var S = A.S, $ = A.$, esc = A.esc, msg = A.msg;
	var PASU_TOTAL = 5, MAX_FILE = 10;
	var LISTA = ['dok_identifikasaun', 'dok_relevante', 'fotografia'];
	// Grupu → kampu (hanesan server legal/forms.py SURVEI_GRUPU)
	var GRUPU = {
		entidade: ['entidade_naran', 'entidade_kontaktu', 'entidade_instituisaun', 'entidade_enderesu'],
		estadu_seluk: ['parte_estadu_civil_seluk'],
		eransa: ['eransa_husi_se', 'eransa_relasaun', 'eransa_herdeiru', 'eransa_rai_seluk', 'eransa_fahe', 'eransa_fahe_ba_se', 'eransa_fahe_lokalizasaun', 'eransa_fahe_desde'],
		eransa_fahe: ['eransa_fahe_ba_se', 'eransa_fahe_lokalizasaun', 'eransa_fahe_desde'],
		sosa: ['sosa_husi_se', 'sosa_folin', 'sosa_bainhira', 'sosa_halo_saida', 'sosa_halo_desde', 'sosa_halo_se', 'sosa_akordu', 'sosa_akordu_fatin', 'sosa_sasin', 'sasin_1', 'sasin_2', 'sasin_3', 'sasin_4'],
		sosa_akordu: ['sosa_akordu_fatin'],
		sosa_sasin: ['sasin_1', 'sasin_2', 'sasin_3', 'sasin_4'],
		foo: ['foo_se', 'foo_bainhira', 'foo_akordu', 'foo_akordu_fatin', 'foo_relasaun'],
		foo_akordu: ['foo_akordu_fatin'],
		posse: ['posse_hahu', 'posse_halo_saida', 'posse_se_mak_halo', 'posse_periodu', 'posse_ema_seluk_tinan', 'posse_relasaun_sosa', 'posse_uza_rai', 'posse_luan_rai', 'posse_luan_disputa', 'posse_luan_uma']
	};
	var FATIN = ['titulu', 'munisipiu', 'postu', 'suku', 'aldeia'];

	function v(id) { var el = $('l-' + id); return el ? el.value : ''; }
	function regra() {
		var m = v('meius');
		return {
			entidade: $('l-sw-entidade').checked,
			estadu_seluk: v('parte_estadu_civil') === 'SELUK',
			eransa: m === 'ERANSA', sosa: m === 'SOSA', foo: m === 'FOO', posse: m === 'POSSE',
			eransa_fahe: m === 'ERANSA' && v('eransa_fahe') === 'SIN',
			sosa_akordu: m === 'SOSA' && v('sosa_akordu') === 'SIN',
			sosa_sasin: m === 'SOSA' && v('sosa_sasin') === 'SIN',
			foo_akordu: m === 'FOO' && v('foo_akordu') === 'SIN'
		};
	}
	function hatuduKond() {
		var r = regra();
		document.querySelectorAll('[data-lgrp]').forEach(function (g) { g.hidden = !r[g.dataset.lgrp]; });
		$('l-grp-fatin').hidden = !!v('kazu');
	}

	// ── Opsaun ──
	function opsaunKazu(valor) {
		var buka = ($('l-kazu-buka').value || '').trim().toLowerCase();
		var lista = (S.opsaun.kazu || []).filter(function (k) {
			return String(k.id) === String(valor) || !buka || (k.kode + ' ' + k.titulu).toLowerCase().indexOf(buka) >= 0;
		}).slice(0, 200);
		A.opsaunSelect($('l-kazu'), lista.map(function (k) { return { id: k.id, name: (k.kode || '?') + (k.titulu ? ' · ' + k.titulu : '') }; }), valor, '— Kazu legál foun (fatin rasik) —');
	}
	function enxeFatin(s) {
		var o = S.opsaun;
		A.opsaunSelect($('l-munisipiu'), o.munisipiu_lista || [], s.munisipiu);
		A.opsaunSelect($('l-postu'), o.postu.filter(function (p) { return String(p.munisipiu_id) === String(s.munisipiu); }), s.postu);
		A.opsaunSelect($('l-suku'), o.suku.filter(function (x) { return String(x.postu_id) === String(s.postu); }), s.suku);
		A.opsaunSelect($('l-aldeia'), o.aldeia.filter(function (x) { return String(x.suku_id) === String(s.suku); }), s.aldeia);
	}
	$('l-kazu-buka').addEventListener('input', function () { opsaunKazu(v('kazu')); });
	$('l-munisipiu').addEventListener('change', function () { leeForm(); S.legal.postu = S.legal.suku = S.legal.aldeia = ''; enxeFatin(S.legal); });
	$('l-postu').addEventListener('change', function () { leeForm(); S.legal.suku = S.legal.aldeia = ''; enxeFatin(S.legal); });
	$('l-suku').addEventListener('change', function () { leeForm(); S.legal.aldeia = ''; enxeFatin(S.legal); });
	$('form-legal').addEventListener('change', function (e) { if (e.target.tagName === 'SELECT' || e.target.id === 'l-sw-entidade') hatuduKond(); });

	// ── Formuláriu ↔ dadus ──
	function surveiFoun() {
		return { id: K.uuid(), kria_iha: new Date().toISOString(), data_survei: A.hoje(), kazu: '', munisipiu: (S.auth.me || {}).munisipiu || '',
			latitude: null, longitude: null, gps_akurasia: null, dok_identifikasaun: [], dok_relevante: [], fotografia: [] };
	}
	function enxeForm() {
		var s = S.legal;
		msg(null);
		$('l-kazu-buka').value = '';
		opsaunKazu(s.kazu);
		enxeFatin(s);
		document.querySelectorAll('[data-lk]').forEach(function (el) {
			if (['kazu', 'munisipiu', 'postu', 'suku', 'aldeia'].indexOf(el.dataset.lk) >= 0) return;
			var x = s[el.dataset.lk];
			el.value = x == null ? '' : x;
		});
		$('l-data_survei').max = A.hoje();
		LISTA.forEach(function (c) {
			document.querySelectorAll('[data-lk-lista="' + c + '"] input').forEach(function (i) { i.checked = (s[c] || []).indexOf(i.value) >= 0; });
		});
		$('l-sw-entidade').checked = GRUPU.entidade.some(function (c) { return s[c]; });
		gpsInfo();
		hatuduKond();
		hatuduMedia();
	}
	function leeForm() {
		var s = S.legal;
		document.querySelectorAll('[data-lk]').forEach(function (el) { s[el.dataset.lk] = el.value.trim(); });
		LISTA.forEach(function (c) {
			s[c] = Array.prototype.map.call(document.querySelectorAll('[data-lk-lista="' + c + '"] input:checked'), function (i) { return i.value; });
		});
		// Grupu subar → mamuk (la haruka resposta la relevante)
		var r = regra();
		Object.keys(GRUPU).forEach(function (g) { if (!r[g]) GRUPU[g].forEach(function (c) { s[c] = ''; }); });
		if (s.kazu) { FATIN.forEach(function (c) { s[c] = ''; }); s.latitude = s.longitude = s.gps_akurasia = null; }
		return s;
	}
	function valida(pasu) {
		var s = S.legal, e = [];
		if (pasu === 1) {
			if (!s.data_survei) e.push('Hakerek data survei.');
			else if (s.data_survei > A.hoje()) e.push('Data survei labele iha futuru.');
			if (!s.kazu && !s.munisipiu) e.push('Hili Kazu SIBAR ka Munisipiu ba kazu legál foun.');
			if (!s.kazu && s.latitude != null && s.gps_akurasia > A.GPS_MAX) e.push('Akurasia GPS ' + s.gps_akurasia + ' m. Tenke ≤ ' + A.GPS_MAX + ' m (ka hamoos GPS).');
		}
		if (pasu === 2) {
			if (!s.parte_naran) e.push('Hakerek naran parte (disputante).');
			if (s.parte_data_moris && s.parte_data_moris > A.hoje()) e.push('Data moris labele iha futuru.');
		}
		if (pasu === 4 && !s.meius) e.push('Hili meius ka maneira hetan rai.');
		return e;
	}

	function baPasu(n) {
		S.legal_pasu = n;
		document.querySelectorAll('#form-legal .step').forEach(function (f) { f.hidden = parseInt(f.dataset.step, 10) !== n; });
		document.querySelectorAll('#l-stepper span').forEach(function (sp) {
			var p = parseInt(sp.dataset.step, 10);
			sp.className = p === n ? 'ativu' : (p < n ? 'remata' : '');
		});
		$('l-btn-kotuk').innerHTML = n === 1 ? '<i class="fa fa-times"></i> Taka' : '<i class="fa fa-chevron-left"></i> Kotuk';
		$('l-btn-oin').innerHTML = n === PASU_TOTAL ? '<i class="fa fa-check"></i> Manda ba Server' : 'Oin <i class="fa fa-chevron-right"></i>';
		if (n === PASU_TOTAL) rezumu();
		window.scrollTo(0, 0);
	}
	function rezumu() {
		var s = S.legal, k = (S.opsaun.kazu || []).filter(function (x) { return x.id === s.kazu; })[0];
		var mun = (S.opsaun.munisipiu_lista || []).filter(function (m) { return String(m.id) === String(s.munisipiu); })[0];
		var meius = { SOSA: 'Sosa', FOO: 'Foó / Doasaun', ERANSA: 'Eransa', POSSE: 'Posse / Okupa' }[s.meius] || '-';
		$('l-rezumu').innerHTML = '<div class="sub-box"><b>Rezumu</b><br>' +
			'Kazu: ' + esc(k ? k.kode : 'Kazu legál foun' + (mun ? ' · ' + mun.name : '')) + '<br>' +
			'Parte: ' + esc(s.parte_naran || '-') + '<br>Meius: ' + esc(meius) + '<br>' +
			'Foto / dokumentu: ' + S.legal_media.length + '/' + MAX_FILE + '</div>';
	}

	function rai(estadu) {
		if (!S.legal) return Promise.resolve();
		var s = S.legal;
		return K.encryptJSON(S.xavi, s).then(function (box) {
			return DB.put('kazu', { id: s.id, estadu: estadu || 'RASCUNHO', kria_iha: s.kria_iha, atualiza: new Date().toISOString(), box: box, erru: null, kode: null, legal: true });
		});
	}

	$('l-btn-oin').addEventListener('click', function () {
		leeForm();
		var e = valida(S.legal_pasu);
		if (e.length) { msg(e); return; }
		msg(null);
		if (S.legal_pasu < PASU_TOTAL) { rai(); baPasu(S.legal_pasu + 1); return; }
		for (var p = 1; p <= PASU_TOTAL; p++) {
			var ep = valida(p);
			if (ep.length) { baPasu(p); msg(ep); return; }
		}
		rai('PRONTU').then(function () {
			A.baVaranda();
			msg(navigator.onLine ? 'Survei prontu. Sinkron hela…' : 'Survei rai ona iha HP (enkriptadu). Sinkron bainhira iha sinál.', 'success');
			if (navigator.onLine) A.sinkronHotu(true);
		});
	});
	$('l-btn-kotuk').addEventListener('click', function () {
		leeForm();
		if (S.legal_pasu > 1) { rai(); baPasu(S.legal_pasu - 1); return; }
		rai().then(A.baVaranda);
	});
	$('l-btn-rai').addEventListener('click', function () {
		leeForm();
		rai().then(function () { msg('Save ona (enkriptadu iha HP).', 'success'); });
	});

	function loke(id) {
		DB.get('kazu', id).then(function (r) {
			return K.decryptJSON(S.xavi, r.box);
		}).then(function (s) {
			S.legal = s;
			return DB.mediaKazu(id);
		}).then(function (media) {
			S.legal_media = media;
			enxeForm(); baPasu(1); A.hatudu('scr-legal');
		}).catch(function () { msg('Survei la bele loke.'); });
	}
	$('btn-legal').addEventListener('click', function () {
		if (!A.permValidu()) { msg('Autorizasaun input legál remata. Kontaktu Admin.'); return; }
		S.legal = surveiFoun(); S.legal_media = [];
		enxeForm(); baPasu(1); A.hatudu('scr-legal');
	});

	// ── GPS (opsionál; kazu legál foun) ──
	var gpsWatch = null, gpsTimer = null;
	function gpsInfo() {
		var s = S.legal;
		$('l-gps-info').textContent = s.latitude != null ? s.latitude.toFixed(6) + ', ' + s.longitude.toFixed(6) + ' (±' + s.gps_akurasia + ' m)' : 'GPS opsionál.';
	}
	function gpsPara() {
		if (gpsWatch !== null) navigator.geolocation.clearWatch(gpsWatch);
		clearTimeout(gpsTimer); gpsWatch = null;
		$('l-btn-gps').disabled = false;
	}
	$('l-btn-gps').addEventListener('click', function () {
		if (!navigator.geolocation) { msg('HP ne\'e la iha GPS.'); return; }
		var diak = null;
		$('l-btn-gps').disabled = true;
		$('l-gps-info').textContent = 'Buka GPS…';
		gpsWatch = navigator.geolocation.watchPosition(function (p) {
			if (!diak || p.coords.accuracy < diak.accuracy) diak = p.coords;
			S.legal.latitude = diak.latitude; S.legal.longitude = diak.longitude; S.legal.gps_akurasia = Math.round(diak.accuracy);
			gpsInfo();
			if (diak.accuracy <= A.GPS_MAX) { gpsPara(); rai(); }
		}, function () { gpsPara(); msg('La bele hetan GPS. Ativa Lokalizasaun no fó permisaun.'); },
		{ enableHighAccuracy: true, maximumAge: 0, timeout: 60000 });
		gpsTimer = setTimeout(gpsPara, 60000);
	});

	// ── Foto / dokumentu (enkriptadu) ──
	var urls = [];
	function hatuduMedia() {
		urls.forEach(URL.revokeObjectURL); urls = [];
		var n = S.legal_media.length;
		$('l-n-file').textContent = n + '/' + MAX_FILE;
		$('l-btn-foto').disabled = $('l-btn-dok').disabled = $('l-btn-galeria').disabled = n >= MAX_FILE;
		var grid = $('l-lista-media');
		grid.innerHTML = '';
		S.legal_media.forEach(function (m) {
			K.decryptBlob(S.xavi, m.box, m.mime).then(function (blob) {
				var url = URL.createObjectURL(blob);
				urls.push(url);
				var d = document.createElement('div');
				d.className = 'media-item';
				d.innerHTML = '<img alt=""><small>' + (m.tipu === 'DOKUMENTU' ? 'Dokumentu' : 'Foto') + '</small>' +
					'<button type="button" class="btn btn-sm btn-danger" data-media="' + esc(m.id) + '" aria-label="Hamoos"><i class="fa fa-trash"></i></button>';
				d.firstChild.src = url;
				grid.appendChild(d);
			});
		});
	}
	function raiMedia(tipu, blob) {
		if (!blob) return Promise.resolve();
		var m = { id: K.uuid(), kazu_id: S.legal.id, tipu: tipu, mime: blob.type || 'image/jpeg', tamanu: blob.size };
		return K.encryptBlob(S.xavi, blob).then(function (box) {
			m.box = box;
			return DB.put('media', m);
		}).then(function () { S.legal_media.push(m); return rai(); }).then(hatuduMedia);
	}
	$('l-btn-foto').addEventListener('click', function () {
		KAM.foto().then(function (b) { return raiMedia('FOTO', b); }).catch(function (e) { msg(e.message); });
	});
	$('l-btn-dok').addEventListener('click', function () {
		KAM.foto().then(function (b) { return raiMedia('DOKUMENTU', b); }).catch(function (e) { msg(e.message); });
	});
	$('l-btn-galeria').addEventListener('click', function () {
		KAM.galeria(MAX_FILE - S.legal_media.length).then(function (r) {
			return r.blobs.reduce(function (p, b) { return p.then(function () { return raiMedia('FOTO', b); }); }, Promise.resolve()).then(function () {
				if (r.liu) msg('Foto ' + r.liu + ' la rai (máximu ' + MAX_FILE + ').', 'warning');
			});
		}).catch(function (e) { msg(e.message); });
	});
	$('l-lista-media').addEventListener('click', function (ev) {
		var b = ev.target.closest('[data-media]');
		if (!b || !confirm('Hamoos foto ne\'e?')) return;
		var id = b.dataset.media;
		DB.del('media', id).then(function () {
			S.legal_media = S.legal_media.filter(function (m) { return m.id !== id; });
			return rai();
		}).then(hatuduMedia);
	});

	// ── Sinkron ──
	function payload(s) {
		var d = {};
		Object.keys(s).forEach(function (c) { if (s[c] !== '' && s[c] != null) d[c] = s[c]; });
		d.id = s.id; d.kria_iha = s.kria_iha;
		return d;
	}
	function markaErru(r, erru) { r.estadu = 'ERRU'; r.erru = erru; return DB.put('kazu', r).then(function () { return false; }); }
	function sinkron(r) {
		var s;
		return K.decryptJSON(S.xavi, r.box).then(function (x) {
			s = x;
			return A.apiJSON(B.apiSurvei, 'POST', payload(s));
		}).then(function (res) {
			if (!res.ok) { if (res.status >= 500) throw new Error('server'); return markaErru(r, A.erruLista(res.data)); }
			return DB.mediaKazu(s.id).then(function (media) {
				return media.reduce(function (p, m) {
					return p.then(function (ok) {
						if (!ok) return false;
						return K.decryptBlob(S.xavi, m.box, m.mime).then(function (blob) {
							var fd = new FormData();
							fd.append('id', m.id); fd.append('tipu', m.tipu);
							fd.append('file', blob, m.id + (m.mime === 'image/png' ? '.png' : '.jpg'));
							return A.api(B.apiSurvei + s.id + '/file/', { method: 'POST', body: fd });
						}).then(function (up) {
							if (up.ok) return true;
							if (up.status >= 500) throw new Error('server');
							return up.json().catch(function () { return {}; }).then(function (d) { return markaErru(r, A.erruLista(d)); });
						});
					});
				}, Promise.resolve(true));
			});
		}).then(function (ok) {
			if (!ok) return false;
			return A.apiJSON(B.apiSurvei + s.id + '/haruka/', 'POST', {}).then(function (res) {
				if (!res.ok) { if (res.status >= 500) throw new Error('server'); return markaErru(r, A.erruLista(res.data)); }
				return DB.hamoosMediaKazu(s.id).then(function () {
					return DB.put('kazu', { id: s.id, estadu: 'SINKRON', kria_iha: s.kria_iha, atualiza: new Date().toISOString(), kode: res.data.kode, box: null, erru: null, legal: true });
				}).then(function () { return true; });
			});
		});
	}

	var STATUS_KOR = { HARUKA: 'badge-warning', VERIFIKADU: 'badge-success', REJEITADU: 'badge-danger', RASCUNHO: 'badge-secondary' };
	function atualizaServer() {
		A.apiJSON(B.apiSurvei).then(function (r) {
			if (!r.ok) return;
			var lista = r.data.survei || [];
			$('lista-server').innerHTML = lista.length ? lista.map(function (x) {
				return '<div class="lokal-item"><div class="d-flex justify-content-between"><b>' + esc(x.kode || 'Rascunho') + '</b>' +
					'<span class="badge ' + (STATUS_KOR[x.status] || 'badge-light') + '">' + esc(x.status_label) + '</span></div>' +
					'<small class="text-muted">' + esc(x.parte || '') + '</small>' +
					(x.nota ? '<small class="text-danger d-block">Razaun: ' + esc(x.nota) + ' — hadia iha SIBAR-RbR online.</small>' : '') + '</div>';
			}).join('') : '<p class="text-muted small">Seidauk iha.</p>';
		}).catch(function (e) { if (e.relogin) A.pedeRelogin(); });
	}

	return { loke: loke, rai: function () { if (S.legal) { leeForm(); return rai(); } }, sinkron: sinkron, atualizaServer: atualizaServer };
})();
