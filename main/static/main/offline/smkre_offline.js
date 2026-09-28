/* SMKRE Offline — app Investigadór iha terrenu (la iha sinál).
   Fluxu: Login (online dala ida) → Kria PIN → Rejista kazu (6 pasu, GPS, kámera) → Sinkron bainhira iha sinál.
   Dadus kazu, foto, vídeo no token hotu enkripta ho PIN (smkre_kripto.js) iha IndexedDB (smkre_db.js). */
(function () {
	'use strict';
	var B = document.body.dataset;
	var K = SmkreKripto, DB = SmkreDB, KAM = SmkreKamera;

	var TL_LAT = [-9.60, -8.10], TL_LON = [124.00, 127.40], GPS_MAX = 50;
	var MAX_FOTO = 5, MAX_VIDEO = 1, PIN_SALA_MAX = 5, XAVI_MINUTU = 5, PASU_TOTAL = 6;
	var VERIFIKA_TESTU = 'SMKRE-PIN-OK';

	// Estadu app (iha memória deit; lakon bainhira xavi)
	var S = { xavi: null, auth: null, opsaun: null, kazu: null, pasu: 1, media: [], urls: [], sinkron: false, ativu: Date.now(), relogin: false };

	function $(id) { return document.getElementById(id); }
	function esc(t) { var d = document.createElement('div'); d.textContent = t == null ? '' : String(t); return d.innerHTML; }

	function hoje() {
		var d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
		return d.toISOString().slice(0, 10);
	}

	function dataTL(iso) {
		if (!iso) return '-';
		var d = new Date(iso);
		return ('0' + d.getDate()).slice(-2) + '/' + ('0' + (d.getMonth() + 1)).slice(-2) + '/' + d.getFullYear();
	}

	// ══════════════ Ekran no mensajen ══════════════
	function hatudu(scr) {
		document.querySelectorAll('.scr').forEach(function (s) { s.hidden = s.id !== scr; });
		$('btn-lock').hidden = !S.xavi;
		window.scrollTo(0, 0);
	}

	function msg(testu, tipu) {
		var m = $('msg');
		if (!testu) { m.hidden = true; return; }
		m.className = 'alert alert-' + (tipu || 'danger');
		m.innerHTML = Array.isArray(testu) ? testu.map(esc).join('<br>') : esc(testu);
		m.hidden = false;
		window.scrollTo(0, 0);
	}

	function net() {
		var n = $('net');
		n.textContent = navigator.onLine ? 'Online' : 'Offline';
		n.className = 'badge badge-pill ' + (navigator.onLine ? 'badge-success' : 'badge-secondary');
	}
	window.addEventListener('online', function () { net(); if (S.xavi) { atualizaServer(); sinkronHotu(true); } });
	window.addEventListener('offline', net);

	// Erru server {'erru': {kampu: [..]}} → lista testu
	function erruLista(data) {
		var lista = [];
		var e = (data && data.erru) || {};
		Object.keys(e).forEach(function (k) {
			[].concat(e[k]).forEach(function (m) { lista.push(((k === '__all__' || k === 'non_field_errors' || k === 'detail') ? '' : k.replace(/_/g, ' ') + ': ') + m); });
		});
		return lista.length ? lista : ['Erru server. Koko fali.'];
	}

	// ══════════════ API (token JWT) ══════════════
	function postJSON(url, body, token) {
		var h = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
		if (token) h.Authorization = 'Bearer ' + token;
		return fetch(url, { method: 'POST', headers: h, body: JSON.stringify(body), credentials: 'omit' });
	}

	function refreshToken() {
		return postJSON(B.apiRefresh, { refresh: S.auth.refresh }).then(function (r) {
			if (!r.ok) { var e = new Error('relogin'); e.relogin = true; throw e; }
			return r.json();
		}).then(function (d) {
			S.auth.access = d.access;
			if (d.refresh) S.auth.refresh = d.refresh;
			S.auth.offline_ativu = d.offline_ativu;
			S.auth.offline_until = d.offline_until;
			return raiAuth();
		});
	}

	// fetch ho token; 401 → refresh dala ida → koko fali
	function api(url, opts, dalaIda) {
		opts = opts || {};
		opts.headers = opts.headers || {};
		opts.headers.Authorization = 'Bearer ' + S.auth.access;
		opts.headers.Accept = 'application/json';
		opts.credentials = 'omit';
		return fetch(url, opts).then(function (r) {
			if (r.status === 401 && !dalaIda) return refreshToken().then(function () { return api(url, opts, true); });
			return r;
		});
	}

	function apiJSON(url, metodu, body) {
		var opts = { method: metodu || 'GET' };
		if (body !== undefined) { opts.body = JSON.stringify(body); opts.headers = { 'Content-Type': 'application/json' }; }
		return api(url, opts).then(function (r) {
			return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, status: r.status, data: d }; });
		});
	}

	// ══════════════ Rai / lee dadus enkriptadu ══════════════
	function raiAuth() { return K.encryptJSON(S.xavi, S.auth).then(function (box) { return DB.metaSet('auth', box); }); }
	function raiOpsaun() { return K.encryptJSON(S.xavi, S.opsaun).then(function (box) { return DB.metaSet('opsaun', box); }); }

	// ══════════════ 1. LOGIN ══════════════
	$('form-login').addEventListener('submit', function (ev) {
		ev.preventDefault();
		if (!navigator.onLine) { msg('Login presiza internet. Buka fatin ho sinál.'); return; }
		var email = $('login-email').value.trim().toLowerCase(), pw = $('login-pw').value;
		msg('Hein…', 'info');
		postJSON(B.apiToken, { username: email, password: pw }).then(function (r) {
			return r.json().catch(function () { return {}; }).then(function (d) {
				if (r.status === 429) throw new Error('Konta xave tanba sala dala barak. Koko fali minutu 30 ka kontaktu Admin.');
				if (!r.ok) throw new Error(d.detail || erruLista({ erru: d }).join(' ') || 'Email ka password sala.');
				return d;
			});
		}).then(function (d) {
			var auth = { access: d.access, refresh: d.refresh, offline_ativu: d.offline_ativu, offline_until: d.offline_until };
			S.auth = auth;
			return apiJSON(B.apiMe).then(function (me) {
				if (S.relogin && S.meEmail && me.data.email !== S.meEmail) throw new Error('HP ne\'e iha dadus husi utilizador seluk. Sinkron uluk ka hamoos dadus.');
				auth.me = me.data;
				return apiJSON(B.apiOpsaun);
			}).then(function (op) {
				if (!op.ok) throw new Error(erruLista(op.data).join(' '));
				S.opsaun = op.data;
				$('login-pw').value = '';
				msg(null);
				if (S.relogin && S.xavi) {
					S.relogin = false;
					return Promise.all([raiAuth(), raiOpsaun()]).then(function () { baVaranda(); sinkronHotu(true); });
				}
				hatudu('scr-pin-set');
			});
		}).catch(function (e) { S.auth = null; msg(e.message || 'La bele login.'); });
	});

	// ══════════════ 2. KRIA PIN ══════════════
	$('form-pin-set').addEventListener('submit', function (ev) {
		ev.preventDefault();
		var p1 = $('pin1').value, p2 = $('pin2').value;
		if (!/^\d{6}$/.test(p1)) { msg('PIN tenke númeru 6.'); return; }
		if (/^(\d)\1{5}$/.test(p1) || '0123456789'.indexOf(p1) >= 0 || '9876543210'.indexOf(p1) >= 0) { msg('PIN fásil liu (ex. 111111, 123456). Hili seluk.'); return; }
		if (p1 !== p2) { msg('PIN la hanesan.'); return; }
		msg('Kria xavi…', 'info');
		var salt = K.randomBytes(16);
		K.deriveKey(p1, salt).then(function (xavi) {
			S.xavi = xavi;
			return K.encryptJSON(xavi, VERIFIKA_TESTU);
		}).then(function (verif) {
			return Promise.all([DB.metaSet('salt', salt), DB.metaSet('verifika', verif), DB.metaSet('pin_sala', 0), raiAuth(), raiOpsaun()]);
		}).then(function () {
			$('pin1').value = $('pin2').value = '';
			msg(null);
			baVaranda();
		}).catch(function () { msg('La bele rai PIN. HP ne\'e presiza browser foun (Chrome / Safari).'); });
	});

	// ══════════════ 3. LOKE HO PIN ══════════════
	$('form-pin').addEventListener('submit', function (ev) {
		ev.preventDefault();
		var pin = $('pin').value;
		if (!/^\d{6}$/.test(pin)) { msg('PIN tenke númeru 6.'); return; }
		msg('Loke…', 'info');
		var xavi;
		Promise.all([DB.metaGet('salt'), DB.metaGet('verifika')]).then(function (r) {
			return K.deriveKey(pin, r[0]).then(function (k) { xavi = k; return K.decryptJSON(k, r[1]); });
		}).then(function (testu) {
			if (testu !== VERIFIKA_TESTU) throw new Error('pin');
			S.xavi = xavi;
			return DB.metaSet('pin_sala', 0).then(function () { return Promise.all([DB.metaGet('auth'), DB.metaGet('opsaun')]); });
		}).then(function (r) {
			return Promise.all([K.decryptJSON(S.xavi, r[0]), K.decryptJSON(S.xavi, r[1])]);
		}).then(function (r) {
			S.auth = r[0]; S.opsaun = r[1];
			$('pin').value = '';
			msg(null);
			baVaranda();
			if (navigator.onLine) { atualizaOpsaun(); atualizaServer(); }
		}).catch(function () {
			$('pin').value = '';
			DB.metaGet('pin_sala').then(function (n) {
				n = (n || 0) + 1;
				if (n >= PIN_SALA_MAX) {
					return DB.wipe().then(function () { msg('PIN sala dala ' + PIN_SALA_MAX + '. Dadus iha HP hamoos ona ba seguransa. Login fali.'); hatudu('scr-login'); });
				}
				return DB.metaSet('pin_sala', n).then(function () {
					msg('PIN sala. Restu tentativa: ' + (PIN_SALA_MAX - n) + '.');
					$('pin-sala').textContent = 'Sala ' + n + '/' + PIN_SALA_MAX;
				});
			});
		});
	});

	$('btn-reset').addEventListener('click', function () {
		if (!confirm('Hamoos dadus HOTU iha HP? Kazu seidauk sinkron sei LAKON.')) return;
		DB.wipe().then(function () { xavi(); msg('Dadus iha HP hamoos ona. Login fali.', 'warning'); hatudu('scr-login'); });
	});

	// Xavi app: hamoos xavi no dadus husi memória
	function xavi() {
		S.xavi = null; S.auth = null; S.opsaun = null; S.kazu = null;
		limpaUrls();
	}
	$('btn-lock').addEventListener('click', function () { xavi(); msg(null); hatudu('scr-pin'); });

	// Xavi automátiku: minutu 5 la uza (ka app iha kotuk)
	['click', 'keydown', 'touchstart', 'input'].forEach(function (ev) {
		document.addEventListener(ev, function () { S.ativu = Date.now(); }, { passive: true });
	});
	setInterval(function () {
		if (S.xavi && !S.sinkron && Date.now() - S.ativu > XAVI_MINUTU * 60000) {
			if (S.kazu) raiRascunho(true);
			xavi(); msg('App xave tanba la uza minutu ' + XAVI_MINUTU + '.', 'info'); hatudu('scr-pin');
		}
	}, 30000);

	// ══════════════ 4. VARANDA ══════════════
	function permValidu() {
		return S.auth && S.auth.offline_ativu && S.auth.offline_until && new Date(S.auth.offline_until) > new Date();
	}

	function baVaranda() {
		S.kazu = null;
		limpaUrls();
		var me = S.auth.me || {};
		$('off-user').textContent = (me.naran || me.email || '') + (me.munisipiu_naran ? ' · ' + me.munisipiu_naran : '');
		var box = $('perm-box');
		if (permValidu()) {
			var loron = Math.max(0, Math.ceil((new Date(S.auth.offline_until) - new Date()) / 86400000));
			box.className = 'perm-box ok';
			box.innerHTML = '<i class="fa fa-check-circle"></i> Autorizasaun offline ativu to\'o <b>' + dataTL(S.auth.offline_until) + '</b> (loron ' + loron + ')';
			$('btn-foun').disabled = false;
		} else {
			box.className = 'perm-box remata';
			box.innerHTML = '<i class="fa fa-ban"></i> Autorizasaun offline remata. Ita bele <b>sinkron</b> kazu uluk deit. Kontaktu Admin atu hetan autorizasaun foun.';
			$('btn-foun').disabled = true;
		}
		hatudu('scr-home');
		listaLokal();
	}

	var ESTADU = {
		RASCUNHO: ['Rascunho', 'badge-secondary'], PRONTU: ['Hein Sinkron', 'badge-warning'],
		SINKRON: ['Sinkron ona', 'badge-success'], ERRU: ['Presiza hadia', 'badge-danger']
	};

	function listaLokal() {
		return DB.all('kazu').then(function (lista) {
			lista.sort(function (a, b) { return (b.atualiza || '').localeCompare(a.atualiza || ''); });
			var n = lista.filter(function (r) { return r.estadu === 'PRONTU'; }).length;
			$('sync-n').textContent = n || '';
			return Promise.all(lista.map(function (r) {
				return r.box ? K.decryptJSON(S.xavi, r.box).then(function (k) { return [r, k]; }) : Promise.resolve([r, null]);
			}));
		}).then(function (items) {
			var el = $('lista-lokal');
			if (!items.length) { el.innerHTML = '<p class="text-muted small">Seidauk iha kazu iha HP.</p>'; return; }
			el.innerHTML = items.map(function (it) {
				var r = it[0], k = it[1], e = ESTADU[r.estadu] || ['?', 'badge-light'];
				var titulu = r.kode || (k && (k.titulu || naranSuku(k.suku))) || 'Kazu';
				var edita = r.estadu !== 'SINKRON';
				return '<div class="lokal-item" data-id="' + esc(r.id) + '">' +
					'<div class="d-flex justify-content-between"><b>' + esc(titulu) + '</b><span class="badge ' + e[1] + '">' + e[0] + '</span></div>' +
					'<small class="text-muted">Kria ' + dataTL(r.kria_iha) + (k && k.urjente ? ' · <span class="text-danger">URJENTE</span>' : '') + '</small>' +
					(r.erru ? '<div class="small text-danger mt-1">' + r.erru.map(esc).join('<br>') + '</div>' : '') +
					(edita ? '<div class="mt-1"><button type="button" class="btn btn-sm btn-outline-rbr js-edita"><i class="fa fa-pencil"></i> Loke</button>' +
						(r.estadu !== 'PRONTU' ? ' <button type="button" class="btn btn-sm btn-link text-danger js-hamoos"><i class="fa fa-trash"></i> Hamoos</button>' : '') + '</div>' : '') +
					'</div>';
			}).join('');
		});
	}

	$('lista-lokal').addEventListener('click', function (ev) {
		var item = ev.target.closest('.lokal-item');
		if (!item) return;
		var id = item.dataset.id;
		if (ev.target.closest('.js-edita')) loke(id);
		if (ev.target.closest('.js-hamoos') && confirm('Hamoos kazu ne\'e husi HP?')) {
			DB.hamoosMediaKazu(id).then(function () { return DB.del('kazu', id); }).then(listaLokal);
		}
	});

	var STATUS_KOR = { SYNCED: 'badge-info', VERIFIED: 'badge-primary', APPROVED: 'badge-success', COMPLETED: 'badge-dark', REJECTED: 'badge-danger', CANCELED: 'badge-secondary', PENDING: 'badge-warning' };

	function atualizaServer() {
		if (!navigator.onLine || !S.auth) { $('lista-server').innerHTML = '<p class="text-muted small">Offline.</p>'; return; }
		apiJSON(B.apiKazu).then(function (r) {
			if (!r.ok) return;
			var lista = r.data.kazu || [];
			$('lista-server').innerHTML = lista.length ? lista.map(function (k) {
				return '<div class="lokal-item"><div class="d-flex justify-content-between"><b>' + esc(k.kode || 'Hein kódigu') + '</b>' +
					'<span class="badge ' + (STATUS_KOR[k.status] || 'badge-light') + '">' + esc(k.status_label) + '</span></div>' +
					(k.nota ? '<small class="text-danger">Razaun: ' + esc(k.nota) + ' — hadia iha SMKRE online.</small>' : '') + '</div>';
			}).join('') : '<p class="text-muted small">Seidauk iha.</p>';
		}).catch(function (e) { if (e.relogin) pedeRelogin(); });
	}

	function atualizaOpsaun() {
		apiJSON(B.apiOpsaun).then(function (r) { if (r.ok) { S.opsaun = r.data; raiOpsaun(); } }).catch(function () {});
	}

	function pedeRelogin() {
		S.relogin = true;
		S.meEmail = S.auth && S.auth.me ? S.auth.me.email : null;
		$('login-email').value = S.meEmail || '';
		msg('Sesaun sinkron remata. Login fali (dadus iha HP la lakon).', 'warning');
		hatudu('scr-login');
	}

	// ══════════════ 5. FORMULÁRIU ══════════════
	function naranSuku(id) {
		var s = S.opsaun && S.opsaun.suku.filter(function (x) { return String(x.id) === String(id); })[0];
		return s ? s.name : '';
	}

	function opsaunSelect(sel, lista, valor, mamuk) {
		sel.innerHTML = '<option value="">' + (mamuk || '---------') + '</option>' + lista.map(function (o) {
			return '<option value="' + o.id + '"' + (String(o.id) === String(valor) ? ' selected' : '') + '>' + esc(o.name) + '</option>';
		}).join('');
	}

	function opsaunCheck(div, lista, valor, naran) {
		valor = (valor || []).map(String);
		div.innerHTML = lista.map(function (o) {
			var id = naran + '-' + o.id;
			return '<div class="custom-control custom-checkbox"><input type="checkbox" class="custom-control-input" id="' + id + '" value="' + o.id + '"' +
				(o.presiza_esplika ? ' data-esplika="1"' : '') + (valor.indexOf(String(o.id)) >= 0 ? ' checked' : '') + '>' +
				'<label class="custom-control-label" for="' + id + '">' + esc(o.name) + '</label></div>';
		}).join('');
	}

	function checkValor(div) {
		return Array.prototype.map.call(div.querySelectorAll('input:checked'), function (i) { return parseInt(i.value, 10); });
	}

	function kazuFoun() {
		return {
			id: K.uuid(), kria_iha: new Date().toISOString(), titulu: '', data_relatoriu: hoje(),
			postu: '', suku: '', aldeia: '', latitude: null, longitude: null, gps_akurasia: null,
			data_akontesimentu: '', tipu_konflitu: [], tipu_seluk: '', tipu_rai: '', deskrisaun: '',
			afetadu: {}, insidente: null, ator: [], estragu: [], estragu_seluk: '', nesesidade: [],
			konsentimentu: false, observasaun: ''
		};
	}

	$('btn-foun').addEventListener('click', function () {
		if (!permValidu()) { msg('Autorizasaun offline remata. Labele kria kazu foun.'); return; }
		S.kazu = kazuFoun(); S.estadu = 'RASCUNHO';
		S.media = [];
		enxeForm();
		baPasu(1);
		hatudu('scr-form');
	});

	function loke(id) {
		DB.get('kazu', id).then(function (r) {
			return K.decryptJSON(S.xavi, r.box).then(function (k) {
				S.kazu = k; S.estadu = r.estadu;
				return DB.mediaKazu(id);
			});
		}).then(function (media) {
			S.media = media;
			enxeForm();
			baPasu(1);
			hatudu('scr-form');
		}).catch(function () { msg('Kazu la bele loke.'); });
	}

	function enxeForm() {
		var k = S.kazu, o = S.opsaun;
		msg(null);
		$('f-titulu').value = k.titulu || '';
		$('f-data_relatoriu').value = k.data_relatoriu || '';
		$('f-data_relatoriu').max = hoje();
		$('f-munisipiu').value = o.munisipiu.name;
		opsaunSelect($('f-postu'), o.postu, k.postu);
		enxeSuku(); enxeAldeia();
		hatuduGPS();
		$('f-data_akontesimentu').value = k.data_akontesimentu || '';
		$('f-data_akontesimentu').max = hoje();
		opsaunCheck($('f-tipu_konflitu'), o.tipu_konflitu, k.tipu_konflitu, 'tk');
		$('f-tipu_seluk').value = k.tipu_seluk || '';
		opsaunSelect($('f-tipu_rai'), o.tipu_rai, k.tipu_rai);
		$('f-deskrisaun').value = k.deskrisaun || '';
		document.querySelectorAll('[data-afetadu]').forEach(function (i) { var v = (k.afetadu || {})[i.dataset.afetadu]; i.value = v == null ? '' : v; });
		var ins = k.insidente || {};
		$('i-ativu').checked = !!k.insidente;
		$('grp-insidente').hidden = !k.insidente;
		opsaunSelect($('i-tipu_eviksaun'), o.tipu_eviksaun, ins.tipu_eviksaun);
		$('i-loron_avizu').value = ins.loron_avizu == null ? '' : ins.loron_avizu;
		$('i-forsa_seguransa').checked = !!ins.forsa_seguransa;
		$('i-estragu').value = ins.estragu || '';
		$('lista-ator').innerHTML = '';
		(k.ator || []).forEach(aumentaAtor);
		opsaunCheck($('f-estragu'), o.estragu, k.estragu, 'es');
		$('f-estragu_seluk').value = k.estragu_seluk || '';
		opsaunCheck($('f-nesesidade'), o.nesesidade, k.nesesidade, 'ne');
		$('f-observasaun').value = k.observasaun || '';
		$('f-konsentimentu').checked = !!k.konsentimentu;
		hatuduSeluk();
		hatuduMedia();
	}

	function enxeSuku() {
		var postu = $('f-postu').value;
		opsaunSelect($('f-suku'), S.opsaun.suku.filter(function (s) { return String(s.postu_id) === postu; }), S.kazu.suku);
	}
	function enxeAldeia() {
		var suku = $('f-suku').value;
		opsaunSelect($('f-aldeia'), S.opsaun.aldeia.filter(function (a) { return String(a.suku_id) === suku; }), S.kazu.aldeia);
	}
	$('f-postu').addEventListener('change', function () { S.kazu.suku = ''; S.kazu.aldeia = ''; enxeSuku(); enxeAldeia(); });
	$('f-suku').addEventListener('change', function () { S.kazu.aldeia = ''; enxeAldeia(); });

	function hatuduSeluk() {
		var presiza = !!$('f-tipu_konflitu').querySelector('input[data-esplika]:checked');
		$('grp-tipu_seluk').hidden = !presiza;
	}
	$('f-tipu_konflitu').addEventListener('change', hatuduSeluk);
	$('i-ativu').addEventListener('change', function () { $('grp-insidente').hidden = !this.checked; });

	function aumentaAtor(a) {
		var node = $('tpl-ator').content.firstElementChild.cloneNode(true);
		opsaunSelect(node.querySelector('[data-ator="tipu_ator"]'), S.opsaun.tipu_ator, a && a.tipu_ator, 'Tipu Atór');
		node.querySelector('[data-ator="naran"]').value = (a && a.naran) || '';
		node.querySelector('[data-ator="papel"]').value = (a && a.papel) || '';
		$('lista-ator').appendChild(node);
	}
	$('btn-ator').addEventListener('click', function () {
		if ($('lista-ator').children.length >= 20) { msg('Atór máximu 20.'); return; }
		aumentaAtor(null);
	});
	$('lista-ator').addEventListener('click', function (ev) {
		if (ev.target.closest('.js-ator-hamoos')) ev.target.closest('.ator-row').remove();
	});

	function num(v) { return v === '' || v == null ? null : parseInt(v, 10); }

	// Formuláriu → S.kazu
	function leeForm() {
		var k = S.kazu;
		k.titulu = $('f-titulu').value.trim();
		k.data_relatoriu = $('f-data_relatoriu').value;
		k.postu = $('f-postu').value; k.suku = $('f-suku').value; k.aldeia = $('f-aldeia').value;
		k.data_akontesimentu = $('f-data_akontesimentu').value;
		k.tipu_konflitu = checkValor($('f-tipu_konflitu'));
		k.tipu_seluk = $('grp-tipu_seluk').hidden ? '' : $('f-tipu_seluk').value.trim();
		k.tipu_rai = $('f-tipu_rai').value;
		k.deskrisaun = $('f-deskrisaun').value.trim();
		k.afetadu = {};
		document.querySelectorAll('[data-afetadu]').forEach(function (i) { k.afetadu[i.dataset.afetadu] = num(i.value); });
		k.insidente = $('i-ativu').checked ? {
			tipu_eviksaun: $('i-tipu_eviksaun').value, loron_avizu: num($('i-loron_avizu').value),
			forsa_seguransa: $('i-forsa_seguransa').checked, estragu: $('i-estragu').value.trim()
		} : null;
		k.ator = Array.prototype.map.call(document.querySelectorAll('#lista-ator .ator-row'), function (row) {
			return {
				tipu_ator: row.querySelector('[data-ator="tipu_ator"]').value,
				naran: row.querySelector('[data-ator="naran"]').value.trim(),
				papel: row.querySelector('[data-ator="papel"]').value.trim()
			};
		}).filter(function (a) { return a.tipu_ator || a.naran || a.papel; });
		k.estragu = checkValor($('f-estragu'));
		k.estragu_seluk = $('f-estragu_seluk').value.trim();
		k.nesesidade = checkValor($('f-nesesidade'));
		k.urjente = k.nesesidade.length > 0;
		k.observasaun = $('f-observasaun').value.trim();
		k.konsentimentu = $('f-konsentimentu').checked;
		return k;
	}

	// Validasaun kada pasu (hanesan regra server)
	function valida(pasu) {
		var k = S.kazu, e = [];
		if (pasu === 1) {
			if (!k.data_relatoriu) e.push('Data Relatóriu obrigatóriu.');
			if (k.data_relatoriu > hoje()) e.push('Data Relatóriu labele iha futuru.');
			if (!k.postu) e.push('Hili Postu Administrativu.');
			if (!k.suku) e.push('Hili Suku.');
			if (k.latitude == null) e.push('Foti koordenada GPS iha fatin akontesimentu.');
			else if (k.gps_akurasia > GPS_MAX) e.push('Akurasia GPS ' + k.gps_akurasia + ' m. Tenke ≤ 50 m.');
		}
		if (pasu === 2) {
			if (!k.data_akontesimentu) e.push('Data Akontesimentu obrigatóriu.');
			if (k.data_akontesimentu > hoje()) e.push('Data Akontesimentu labele iha futuru.');
			if (!k.tipu_konflitu.length) e.push('Hili tipu konflitu rai.');
			if (!$('grp-tipu_seluk').hidden && !k.tipu_seluk) e.push('Favor esplika tipu konflitu "Seluk".');
			if (!k.deskrisaun) e.push('Deskrisaun Insidente obrigatóriu.');
		}
		if (pasu === 3) {
			var a = k.afetadu;
			if (a.total_ema != null && a.mane != null && a.feto != null && a.mane + a.feto !== a.total_ema) e.push('Mane + Feto tenke hanesan Total Ema (' + (a.mane + a.feto) + ').');
			if (k.insidente && !k.insidente.tipu_eviksaun) e.push('Hili Tipu Eviksaun.');
			if (k.ator.some(function (x) { return !x.tipu_ator; })) e.push('Hili Tipu Atór ba atór hotu.');
		}
		if (pasu === 6 && !k.konsentimentu) e.push('Laiha konsentimentu = labele rai kazu.');
		return e;
	}

	function baPasu(n) {
		S.pasu = n;
		document.querySelectorAll('#form-kazu .step').forEach(function (f) { f.hidden = parseInt(f.dataset.step, 10) !== n; });
		document.querySelectorAll('#stepper span').forEach(function (s) {
			var p = parseInt(s.dataset.step, 10);
			s.className = p === n ? 'ativu' : (p < n ? 'remata' : '');
		});
		$('btn-kotuk').innerHTML = n === 1 ? '<i class="fa fa-times"></i> Taka' : '<i class="fa fa-chevron-left"></i> Kotuk';
		$('btn-oin').innerHTML = n === PASU_TOTAL ? '<i class="fa fa-check"></i> Prontu' : 'Oin <i class="fa fa-chevron-right"></i>';
		if (n === PASU_TOTAL) rezumu();
		window.scrollTo(0, 0);
	}

	$('btn-oin').addEventListener('click', function () {
		leeForm();
		var e = valida(S.pasu);
		if (e.length) { msg(e); return; }
		msg(null);
		if (S.pasu < PASU_TOTAL) { raiRascunho(true); baPasu(S.pasu + 1); return; }
		// Pasu ikus: valida hotu → PRONTU (hein sinkron)
		for (var p = 1; p <= PASU_TOTAL; p++) {
			var ep = valida(p);
			if (ep.length) { baPasu(p); msg(ep); return; }
		}
		raiKazu('PRONTU').then(function () {
			baVaranda();
			msg(navigator.onLine ? 'Kazu prontu. Sinkron hela…' : 'Kazu rai ona iha HP (enkriptadu). Sinkron bainhira iha sinál.', 'success');
			if (navigator.onLine) sinkronHotu(true);
		});
	});

	$('btn-kotuk').addEventListener('click', function () {
		leeForm();
		if (S.pasu > 1) { raiRascunho(true); baPasu(S.pasu - 1); return; }
		raiRascunho(true).then(baVaranda);
	});

	$('btn-rai').addEventListener('click', function () {
		leeForm();
		raiRascunho(false).then(function () { msg('Rai ona hanesan rascunho (enkriptadu).', 'success'); });
	});

	function raiRascunho(silensiu) {
		// Kazu PRONTU / ERRU ne'ebé edita fali → fila ba rascunho to'o klik "Prontu"
		return raiKazu('RASCUNHO');
	}

	function raiKazu(estadu) {
		var k = S.kazu;
		return K.encryptJSON(S.xavi, k).then(function (box) {
			return DB.put('kazu', { id: k.id, estadu: estadu, kria_iha: k.kria_iha, atualiza: new Date().toISOString(), box: box, erru: null });
		});
	}

	function rezumu() {
		var k = S.kazu;
		var foto = S.media.filter(function (m) { return m.tipu === 'FOTO'; }).length;
		var video = S.media.filter(function (m) { return m.tipu === 'VIDEO'; }).length;
		var afe = k.afetadu || {};
		$('rezumu').innerHTML = '<div class="sub-box"><b>Rezumu</b><br>' +
			'Fatin: ' + esc(naranSuku(k.suku)) + ', ' + esc(S.opsaun.munisipiu.name) + '<br>' +
			'GPS: ' + (k.latitude != null ? k.latitude.toFixed(5) + ', ' + k.longitude.toFixed(5) + ' (±' + k.gps_akurasia + ' m)' : '-') + '<br>' +
			'Uma-kain: ' + (afe.uma_kain == null ? '-' : afe.uma_kain) + ' · Ema: ' + (afe.total_ema == null ? '-' : afe.total_ema) + '<br>' +
			'Foto: ' + foto + '/' + MAX_FOTO + ' · Vídeo: ' + video + '/' + MAX_VIDEO +
			(k.nesesidade.length ? '<br><span class="badge badge-urjente">URJENTE</span>' : '') + '</div>';
	}

	// ══════════════ GPS ══════════════
	var gpsWatch = null, gpsTimer = null;

	function hatuduGPS() {
		var k = S.kazu, info = $('gps-info');
		if (k.latitude == null) { info.className = 'small mt-1 text-muted'; info.textContent = 'Tenke iha fatin akontesimentu. Akurasia tenke ≤ 50 m.'; return; }
		info.className = 'small mt-1 ' + (k.gps_akurasia <= GPS_MAX ? 'text-success' : 'text-danger');
		info.innerHTML = '<i class="fa fa-check"></i> ' + k.latitude.toFixed(6) + ', ' + k.longitude.toFixed(6) + ' · akurasia ±' + k.gps_akurasia + ' m';
	}

	function paraGPS() {
		if (gpsWatch !== null) navigator.geolocation.clearWatch(gpsWatch);
		clearTimeout(gpsTimer);
		gpsWatch = null;
		$('btn-gps').disabled = false;
	}

	$('btn-gps').addEventListener('click', function () {
		if (!navigator.geolocation) { msg('HP ne\'e la iha GPS.'); return; }
		var info = $('gps-info');
		info.className = 'small mt-1 text-info';
		info.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Buka GPS… hein iha fatin loke (la iha uma laran).';
		this.disabled = true;
		var diak = null;
		gpsWatch = navigator.geolocation.watchPosition(function (p) {
			var c = p.coords;
			if (c.latitude < TL_LAT[0] || c.latitude > TL_LAT[1] || c.longitude < TL_LON[0] || c.longitude > TL_LON[1]) {
				paraGPS(); msg('Koordenada GPS la iha territóriu Timor-Leste.'); info.textContent = ''; return;
			}
			if (!diak || c.accuracy < diak.accuracy) diak = c;
			var akur = Math.round(diak.accuracy);
			if (akur <= GPS_MAX) {
				S.kazu.latitude = Math.round(diak.latitude * 1e6) / 1e6;
				S.kazu.longitude = Math.round(diak.longitude * 1e6) / 1e6;
				S.kazu.gps_akurasia = akur;
				hatuduGPS();
				if (akur <= 10) paraGPS();
			} else {
				info.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Akurasia ±' + akur + ' m… hein (tenke ≤ 50 m)';
			}
		}, function (err) {
			paraGPS();
			msg(err.code === 1 ? 'Favor permite GPS (lokalizasaun) ba SMKRE iha setting browser.' : 'GPS la hetan sinál. Ba fatin loke no koko fali.');
			hatuduGPS();
		}, { enableHighAccuracy: true, maximumAge: 0, timeout: 60000 });
		gpsTimer = setTimeout(function () {
			paraGPS();
			if (S.kazu.latitude == null) msg('GPS la to\'o akurasia 50 m iha minutu 2. Koko fali iha fatin loke.');
		}, 120000);
	});

	// ══════════════ EVIDÉNSIA (kámera) ══════════════
	function limpaUrls() { S.urls.forEach(URL.revokeObjectURL); S.urls = []; }

	function hatuduMedia() {
		limpaUrls();
		var foto = S.media.filter(function (m) { return m.tipu === 'FOTO'; }).length;
		var video = S.media.filter(function (m) { return m.tipu === 'VIDEO'; }).length;
		$('n-foto').textContent = foto + '/' + MAX_FOTO;
		$('n-video').textContent = video + '/' + MAX_VIDEO;
		$('btn-foto').disabled = foto >= MAX_FOTO;
		$('btn-video').disabled = video >= MAX_VIDEO;
		var grid = $('lista-media');
		grid.innerHTML = '';
		S.media.forEach(function (m) {
			K.decryptBlob(S.xavi, m.box, m.mime).then(function (blob) {
				var url = URL.createObjectURL(blob);
				S.urls.push(url);
				var d = document.createElement('div');
				d.className = 'media-item';
				d.innerHTML = (m.tipu === 'FOTO' ? '<img alt="">' : '<video controls playsinline></video>') +
					'<small>' + (m.tamanu < 1048576 ? Math.round(m.tamanu / 1024) + ' KB' : (m.tamanu / 1048576).toFixed(1) + ' MB') + '</small>' +
					'<button type="button" class="btn btn-sm btn-danger" data-media="' + m.id + '" aria-label="Hamoos"><i class="fa fa-trash"></i></button>';
				d.firstChild.src = url;
				grid.appendChild(d);
			});
		});
	}

	function raiMedia(tipu, blob) {
		if (!blob) return;
		var m = { id: K.uuid(), kazu_id: S.kazu.id, tipu: tipu, mime: blob.type || (tipu === 'FOTO' ? 'image/jpeg' : 'video/mp4'), tamanu: blob.size };
		return K.encryptBlob(S.xavi, blob).then(function (box) {
			m.box = box;
			return DB.put('media', m);
		}).then(function () {
			S.media.push(m);
			return raiRascunho(true);
		}).then(hatuduMedia);
	}

	$('btn-foto').addEventListener('click', function () {
		S.ativu = Date.now();
		KAM.foto().then(function (b) { return raiMedia('FOTO', b); }).catch(function (e) { msg(e.message); });
	});
	$('btn-video').addEventListener('click', function () {
		S.ativu = Date.now();
		KAM.video().then(function (b) { return raiMedia('VIDEO', b); }).catch(function (e) { msg(e.message); });
	});
	$('lista-media').addEventListener('click', function (ev) {
		var b = ev.target.closest('[data-media]');
		if (!b || !confirm('Hamoos evidénsia ne\'e?')) return;
		var id = b.dataset.media;
		DB.del('media', id).then(function () {
			S.media = S.media.filter(function (m) { return m.id !== id; });
			hatuduMedia();
		});
	});

	// ══════════════ SINKRON ══════════════
	function payload(k) {
		var afe = k.afetadu || {};
		var temAfetadu = Object.keys(afe).some(function (x) { return afe[x] != null; });
		return {
			id: k.id, kria_iha: k.kria_iha, titulu: k.titulu, data_relatoriu: k.data_relatoriu,
			postu: k.postu, suku: k.suku, aldeia: k.aldeia,
			latitude: k.latitude, longitude: k.longitude, gps_akurasia: k.gps_akurasia,
			data_akontesimentu: k.data_akontesimentu, tipu_konflitu: k.tipu_konflitu, tipu_seluk: k.tipu_seluk,
			tipu_rai: k.tipu_rai, deskrisaun: k.deskrisaun, estragu: k.estragu, estragu_seluk: k.estragu_seluk,
			nesesidade: k.nesesidade, konsentimentu: k.konsentimentu, observasaun: k.observasaun,
			afetadu: temAfetadu ? [afe] : [], insidente: k.insidente ? [k.insidente] : [], ator: k.ator || []
		};
	}

	function markaErru(r, erru) {
		r.estadu = 'ERRU'; r.erru = erru;
		return DB.put('kazu', r);
	}

	// Kazu ida: dadus → evidénsia ida-ida → haruka. Kada pasu bele koko fali (server idempotente).
	function sinkronKazu(r) {
		var k;
		return K.decryptJSON(S.xavi, r.box).then(function (kazu) {
			k = kazu;
			return apiJSON(B.apiKazu, 'POST', payload(k));
		}).then(function (res) {
			if (!res.ok) { if (res.status >= 500) throw new Error('server'); return markaErru(r, erruLista(res.data)).then(function () { return false; }); }
			return DB.mediaKazu(k.id).then(function (media) {
				return media.reduce(function (p, m) {
					return p.then(function (ok) {
						if (!ok) return false;
						return K.decryptBlob(S.xavi, m.box, m.mime).then(function (blob) {
							var fd = new FormData();
							fd.append('id', m.id);
							fd.append('tipu', m.tipu);
							fd.append('file', blob, m.id + '.' + (m.mime.indexOf('webm') >= 0 ? 'webm' : m.tipu === 'FOTO' ? 'jpg' : 'mp4'));
							return api(B.apiKazu + k.id + '/evidensia/', { method: 'POST', body: fd });
						}).then(function (up) {
							if (up.ok) return true;
							if (up.status >= 500) throw new Error('server');
							return up.json().catch(function () { return {}; }).then(function (d) { return markaErru(r, erruLista(d)).then(function () { return false; }); });
						});
					});
				}, Promise.resolve(true));
			});
		}).then(function (ok) {
			if (!ok) return false;
			return apiJSON(B.apiKazu + k.id + '/haruka/', 'POST', {}).then(function (res) {
				if (!res.ok) { if (res.status >= 500) throw new Error('server'); return markaErru(r, erruLista(res.data)).then(function () { return false; }); }
				// Susesu: hamoos dadus privadu husi HP; rai kódigu deit
				return DB.hamoosMediaKazu(k.id).then(function () {
					return DB.put('kazu', { id: k.id, estadu: 'SINKRON', kria_iha: k.kria_iha, atualiza: new Date().toISOString(), kode: res.data.kode, box: null, erru: null });
				}).then(function () { return true; });
			});
		});
	}

	function sinkronHotu(silensiu) {
		if (S.sinkron || !S.xavi) return;
		if (!navigator.onLine) { if (!silensiu) msg('La iha sinál. Kazu seguru iha HP; sinkron bainhira iha internet.', 'warning'); return; }
		S.sinkron = true;                        // xavi kedas: evento 'online' dala rua la halo sinkron paralelu
		DB.all('kazu').then(function (lista) {
			lista = lista.filter(function (r) { return r.estadu === 'PRONTU'; });
			if (!lista.length) { S.sinkron = false; if (!silensiu) msg('La iha kazu atu sinkron.', 'info'); atualizaServer(); return; }
			var bar = $('sync-progress'), total = lista.length, ok = 0, erru = 0;
			bar.hidden = false; bar.firstElementChild.style.width = '5%';
			$('btn-sync').disabled = true;
			return lista.reduce(function (p, r, i) {
				return p.then(function () {
					return sinkronKazu(r).then(function (res) { if (res) ok++; else erru++; });
				}).then(function () { bar.firstElementChild.style.width = Math.round((i + 1) / total * 100) + '%'; });
			}, Promise.resolve()).then(function () {
				msg('Sinkron remata: ' + ok + ' susesu' + (erru ? ', ' + erru + ' presiza hadia' : '') + '.', erru ? 'warning' : 'success');
			}).catch(function (e) {
				if (e.relogin) { pedeRelogin(); return; }
				msg('Koneksaun kotu. Kazu seidauk sinkron sei hela iha HP. Koko fali.', 'warning');
			}).then(function () {
				S.sinkron = false;
				bar.hidden = true;
				$('btn-sync').disabled = false;
				if (S.xavi && !S.relogin) { listaLokal(); atualizaServer(); }
			});
		}).catch(function () { S.sinkron = false; });
	}
	$('btn-sync').addEventListener('click', function () { sinkronHotu(false); });

	// ══════════════ ARRANKA ══════════════
	function arranka() {
		net();
		if (!window.crypto || !crypto.subtle || !window.indexedDB) {
			msg('Browser ne\'e la suporta app offline. Uza Chrome (Android) ka Safari (iPhone) foun, liuhusi HTTPS.');
			return;
		}
		if ('serviceWorker' in navigator && B.sw) {
			navigator.serviceWorker.register(B.sw, { scope: '/' }).catch(function () {});
		}
		if (navigator.storage && navigator.storage.persist) navigator.storage.persist();   // browser labele hamoos dadus
		DB.metaGet('salt').then(function (salt) { hatudu(salt ? 'scr-pin' : 'scr-login'); })
			.catch(function () { msg('Armazenamentu HP la bele loke.'); });
	}
	arranka();
})();
