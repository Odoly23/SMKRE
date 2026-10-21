/* SIBAR-RbR Offline — app Investigadór iha terrenu (la iha sinál).
   Fluxu: Login (online dala ida) → Kria PIN → Rejista kazu (6 pasu, GPS, kámera) → Sinkron bainhira iha sinál.
   Dadus kazu, foto, vídeo no token hotu enkripta ho PIN (smkre_kripto.js) iha IndexedDB (smkre_db.js). */
(function () {
	'use strict';
	var B = document.body.dataset;
	var K = SmkreKripto, DB = SmkreDB, KAM = SmkreKamera;

	var TL_LAT = [-9.60, -8.10], TL_LON = [124.00, 127.40], GPS_MAX = 50;
	var MAX_FOTO = 5, MAX_VIDEO = 3, PIN_SALA_MAX = 5, XAVI_MINUTU = 5, PASU_TOTAL = 8;
	var VERIFIKA_TESTU = 'SMKRE-PIN-OK';

	// Estadu app (iha memória deit; lakon bainhira xavi)
	var S = { xavi: null, auth: null, opsaun: null, kazu: null, pasu: 1, media: [], urls: [], sinkron: false, ativu: Date.now(), relogin: false };

	function $(id) { return document.getElementById(id); }
	// Ofisiál Legál: app hanesan, maibé input survei legál (smkre_legal.js) duké kazu
	function ehLegal() { return !!(S.auth && S.auth.me && S.auth.me.role === 'ofisial_legal'); }
	function LEGAL() { return window.SmkreLegal; }
	function urlOpsaun() { return ehLegal() ? B.apiOpsaunLegal : B.apiOpsaun; }
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
				return apiJSON(urlOpsaun());
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
			if (navigator.onLine) atualizaOpsaun();
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
		S.xavi = null; S.auth = null; S.opsaun = null; S.kazu = null; S.legal = null;
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
			if (S.legal && LEGAL()) LEGAL().rai();
			xavi(); msg('App xave tanba la uza minutu ' + XAVI_MINUTU + '.', 'info'); hatudu('scr-pin');
		}
	}, 30000);

	// ══════════════ 4. VARANDA ══════════════
	function permValidu() {
		return S.auth && S.auth.offline_ativu && S.auth.offline_until && new Date(S.auth.offline_until) > new Date();
	}

	function baVaranda() {
		S.kazu = null; S.legal = null;
		limpaUrls();
		if (navigator.onLine && S.auth && !S.relogin) atualizaServer();     // status server + kazu follow-up
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
		var legal = ehLegal();
		$('btn-foun').hidden = legal;
		$('btn-legal').hidden = !legal;
		$('btn-legal').disabled = !permValidu();
		$('lbl-lokal').textContent = legal ? 'Survei legál iha HP' : 'Kazu iha HP';
		if (legal) box.innerHTML = box.innerHTML.replace('kazu uluk', 'survei uluk').replace('Autorizasaun offline', 'Autorizasaun input legál');
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
				var titulu = r.kode || (r.legal ? (k && (k.parte_naran || k.titulu)) || 'Survei legál' : (k && (k.titulu || naranSuku(k.suku))) || 'Kazu');
				var edita = r.estadu !== 'SINKRON';
				return '<div class="lokal-item" data-id="' + esc(r.id) + '"' + (r.legal ? ' data-legal="1"' : '') + '>' +
					'<div class="d-flex justify-content-between"><b>' + esc(titulu) + '</b><span>' + (r.followup && r.estadu !== 'SINKRON' ? '<span class="badge badge-warning mr-1">Follow-up</span>' : '') +
					'<span class="badge ' + e[1] + '">' + e[0] + '</span></span></div>' +
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
		if (ev.target.closest('.js-edita')) { if (item.dataset.legal) LEGAL().loke(id); else loke(id); }
		if (ev.target.closest('.js-hamoos') && confirm('Hamoos dadus ne\'e husi HP?')) {
			DB.hamoosMediaKazu(id).then(function () { return DB.del('kazu', id); }).then(listaLokal);
		}
	});

	var STATUS_KOR = { FOLLOWUP: 'badge-warning', SYNCED: 'badge-info', VERIFIED: 'badge-primary', APPROVED: 'badge-success', COMPLETED: 'badge-dark', REJECTED: 'badge-danger', CANCELED: 'badge-secondary', PENDING: 'badge-warning' };

	function atualizaServer() {
		if (!navigator.onLine || !S.auth) { $('lista-server').innerHTML = '<p class="text-muted small">Offline.</p>'; return; }
		if (ehLegal()) { LEGAL().atualizaServer(); return; }
		apiJSON(B.apiKazu).then(function (r) {
			if (!r.ok) return;
			var lista = r.data.kazu || [];
			$('lista-server').innerHTML = lista.length ? lista.map(function (k) {
				return '<div class="lokal-item"><div class="d-flex justify-content-between"><b>' + esc(k.kode || 'Hein kódigu') + '</b>' +
					'<span class="badge ' + (STATUS_KOR[k.status] || 'badge-light') + '">' + esc(k.status_label) + '</span></div>' +
					(k.followup ? '<small class="text-warning d-block"><i class="fa fa-street-view"></i> Follow-up: ' + esc(k.nota) + '</small>' +
						'<button type="button" class="btn btn-sm btn-warning mt-1 js-followup" data-id="' + esc(k.id) + '"><i class="fa fa-download"></i> Download ba HP</button>'
					: (k.nota ? '<small class="text-danger">Razaun: ' + esc(k.nota) + ' — hadia iha SIBAR-RbR online.</small>' : '')) + '</div>';
			}).join('') : '<p class="text-muted small">Seidauk iha.</p>';
		}).catch(function (e) { if (e.relogin) pedeRelogin(); });
	}

	// Follow-up: download kazu husi server ba HP (enkriptadu) → edita iha terrenu → sinkron fali
	$('lista-server').addEventListener('click', function (ev) {
		var b = ev.target.closest('.js-followup');
		if (!b) return;
		var id = b.dataset.id;
		DB.get('kazu', id).then(function (uluk) {
			if (uluk && uluk.estadu !== 'SINKRON' && !confirm('Kazu ne\'e iha HP ona. Troka ho dadus husi server?')) return;
			b.disabled = true;
			return apiJSON(B.apiKazu + id + '/followup/').then(function (r) {
				if (!r.ok) { msg('Kazu follow-up la bele download.'); b.disabled = false; return; }
				var k = r.data;
				return K.encryptJSON(S.xavi, k).then(function (box) {
					return DB.put('kazu', { id: k.id, estadu: 'RASCUNHO', kria_iha: k.kria_iha, atualiza: new Date().toISOString(), box: box, erru: null, kode: k.kode, followup: true });
				}).then(function () {
					msg('Kazu ' + (k.kode || '') + ' iha HP ona. Klik Loke, tuun ba terrenu, hadia no Prontu → Sinkron.', 'success');
					listaLokal();
				});
			});
		}).catch(function (e) { b.disabled = false; if (e && e.relogin) pedeRelogin(); else msg('Kazu follow-up la bele download.'); });
	});

	function atualizaOpsaun() {
		apiJSON(urlOpsaun()).then(function (r) { if (r.ok) { S.opsaun = r.data; raiOpsaun(); } }).catch(function () {});
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
				(o.presiza_esplika ? ' data-esplika="1"' : '') + (o.entidade ? ' data-entidade="1"' : '') + (o.code === 'SELUK' ? ' data-seluk="1"' : '') + (valor.indexOf(String(o.id)) >= 0 ? ' checked' : '') + '>' +
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
			konsentimentu: false, la_publika: false, observasaun: '', rai_luan_unidade: 'M2', poligon_pontu: [[]], segimentu: {}
		};
	}

	// Kampu simples (formuláriu RbR): input/select ho data-kampu — enxe no lee automátiku
	function enxeKampu(k) {
		document.querySelectorAll('[data-kampu]').forEach(function (el) {
			var v = k[el.dataset.kampu];
			el.value = v == null ? (el.tagName === 'SELECT' && el.options.length ? el.options[0].value : '') : v;
		});
	}
	function leeKampu(k) {
		document.querySelectorAll('[data-kampu]').forEach(function (el) {
			var v = el.value.trim();
			if (el.dataset.tipu === 'int') v = v === '' ? null : parseInt(v, 10);
			else if (el.dataset.tipu === 'decimal') v = v === '' ? null : parseFloat(v);
			k[el.dataset.kampu] = v;
		});
	}
	var KAMPU_RBR = ['numeru_rbr', 'tinan_simu', 'akompanamentu_foun', 'enderesu_fatin', 'rai_luan', 'rai_luan_unidade', 'tinan_disputa_hahu', 'projetu', 'entidade_foti',
		'entidade_kategoria', 'entidade_kategoria_seluk', 'iha_dadus_uma_kain', 'fonte_dadus_uma_kain', 'observasaun_afetadu', 'eviksaun_akontese',
		'data_eviksaun', 'konsultasaun_molok', 'notifikasaun_klaru', 'uza_forsa', 'observasaun_eviksaun',
		'portavos_naran', 'portavos_kontaktu', 'portavos_observasaun'];

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
		// Tipu konflitu tuan (la ativu ona) → hasai, Investigadór hili fali tipu foun
		var tkValidu = o.tipu_konflitu.map(function (t) { return t.id; });
		var tkTuan = (k.tipu_konflitu || []).filter(function (id) { return tkValidu.indexOf(id) < 0; });
		k.tipu_konflitu = (k.tipu_konflitu || []).filter(function (id) { return tkValidu.indexOf(id) >= 0; });
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
		opsaunCheck($('f-estragu'), o.estragu, k.estragu, 'es');
		$('f-estragu_seluk').value = k.estragu_seluk || '';
		opsaunCheck($('f-nesesidade'), o.nesesidade, k.nesesidade, 'ne');
		$('f-observasaun').value = k.observasaun || '';
		$('f-konsentimentu').checked = !!k.konsentimentu;
		$('f-la_publika').checked = !!k.la_publika;
		enxeKampu(k);
		// Segimentu (tribunál, notifikasaun, status kazu, organizasaun seluk)
		var seg = k.segimentu || {};
		document.querySelectorAll('[data-seg]').forEach(function (el) { var v = seg[el.dataset.seg]; el.value = v == null ? '' : v; });
		tinanSimu();
		hatuduSeluk();
		hatuduMedia();
		// Switch "Iha …?" loke automátiku se iha ona dadus
		var afe = k.afetadu || {};
		var seg0 = k.segimentu || {}, iha = function (cs) { return cs.some(function (c) { return seg0[c] != null && seg0[c] !== ''; }); };
		$('sw-rai').checked = !!(k.enderesu_fatin || k.rai_luan != null || polPontuHotu(k) > 0);
		$('sw-org').checked = iha(['org_seluk', 'org_seluk_naran', 'org_seluk_kontaktu']);
		$('sw-status').checked = iha(['data_ikus_cek', 'status_rezolusaun', 'desizaun_rbr', 'observasaun_kazu']);
		$('sw-portavos').checked = !!(k.portavos_naran || k.portavos_kontaktu || k.portavos_observasaun);
		$('sw-entidade_foti').checked = !!(k.entidade_foti || k.entidade_kategoria);
		S.estraguSelukTuan = !!k.estragu_seluk;          // testu tuan → hatudu nafatin
		$('sw-estragu').checked = (k.estragu || []).length > 0 || !!k.estragu_seluk;
		$('sw-nesesidade').checked = (k.nesesidade || []).length > 0;
		$('sw-video').checked = S.media.some(function (m) { return m.tipu === 'VIDEO'; });
		// Kazu tuan la iha resposta "Dadus uma-kain iha?" maibé iha ona detalla → hatudu
		S.umaKainTuan = !k.iha_dadus_uma_kain && ['mane', 'feto', 'labarik', 'katuas_ferik', 'defisiensia'].some(function (x) { return afe[x] != null; });
		hatuduKond();
		polHatudu();
		if (tkTuan.length) msg('Tipu konflitu tuan la uza ona. Favor hili fali tipu konflitu iha pasu 2.', 'warning');
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
	$('f-tipu_konflitu').addEventListener('change', function () { hatuduSeluk(); hatuduKond(); });

	// ══ Hatudu / subar grupu tuir resposta (formuláriu badak) ══
	function hatuduKond() {
		var tk = $('f-tipu_konflitu');
		$('grp-entidade').hidden = !tk.querySelector('input[data-entidade]:checked');
		$('grp-uma_kain').hidden = !($('f-iha_dadus_uma_kain').value === 'SIN' || (S.umaKainTuan && !$('f-iha_dadus_uma_kain').value));
		$('grp-eviksaun').hidden = $('grp-eviksaun2').hidden = $('f-eviksaun_akontese').value !== 'SIN';
		$('grp-tribunal').hidden = ['SIN', 'DADAUN'].indexOf($('s-tribunal_rejistu').value) < 0;
		$('grp-tribunal_desizaun').hidden = $('s-tribunal_desizaun').value !== 'SIN';
		$('grp-notif').hidden = $('s-notif_simu').value !== 'SIN';
		document.querySelectorAll('[data-switch]').forEach(function (sw) { $(sw.dataset.switch).hidden = !sw.checked; });
		// Opsaun "Seluk" → kampu esplika
		$('grp-entidade_seluk').hidden = $('f-entidade_kategoria').value !== 'SELUK';
		$('grp-tribunal_desizaun_seluk').hidden = $('s-tribunal_desizaun').value !== 'SELUK';
		$('grp-estragu_seluk').hidden = !($('f-estragu').querySelector('input[data-seluk]:checked') || S.estraguSelukTuan);
	}
	['f-iha_dadus_uma_kain', 'f-eviksaun_akontese', 's-tribunal_rejistu', 's-tribunal_desizaun', 's-notif_simu', 'f-entidade_kategoria', 'f-estragu'].forEach(function (id) { $(id).addEventListener('change', hatuduKond); });
	document.querySelectorAll('[data-switch]').forEach(function (sw) {
		sw.addEventListener('change', function () {
			if (sw.id === 'sw-video' && !sw.checked && S.media.some(function (m) { return m.tipu === 'VIDEO'; })) {
				sw.checked = true; msg('Hamoos vídeo sira uluk mak bele taka.', 'info'); return;
			}
			hatuduKond();
		});
	});
	// Grupu subar = dadus la rai (hamoos), atu la haruka dadus ne'ebé la relevante
	function subar(id) { return $(id).hidden; }
	$('i-ativu').addEventListener('change', function () { $('grp-insidente').hidden = !this.checked; });

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
		k.ator = k.ator || [];                         // atór tuan (husi server) la muda; formuláriu uza entidade
		k.estragu = checkValor($('f-estragu'));
		k.estragu_seluk = $('f-estragu_seluk').value.trim();
		k.nesesidade = checkValor($('f-nesesidade'));
		k.urjente = k.nesesidade.length > 0;
		k.observasaun = $('f-observasaun').value.trim();
		k.konsentimentu = $('f-konsentimentu').checked;
		k.la_publika = $('f-la_publika').checked;
		leeKampu(k);
		k.segimentu = {};
		document.querySelectorAll('[data-seg]').forEach(function (el) { var v = el.value.trim(); if (v) k.segimentu[el.dataset.seg] = v; });
		document.querySelectorAll('.kond[hidden] [data-kampu]').forEach(function (el) { k[el.dataset.kampu] = null; });
		document.querySelectorAll('.kond[hidden] [data-afetadu]').forEach(function (el) { k.afetadu[el.dataset.afetadu] = null; });
		document.querySelectorAll('.kond[hidden] [data-seg]').forEach(function (el) { delete k.segimentu[el.dataset.seg]; });
		if (subar('grp-rai')) k.poligon_pontu = [[]];
		if (polBidang(k).length) { var lr = luanRai(SIBARPoligon.kalkula(polBidang(k)).luan_m2); k.rai_luan = lr[0]; k.rai_luan_unidade = lr[1]; }
		if (subar('grp-estragu_seluk')) k.estragu_seluk = '';
		if (subar('grp-estragu')) { k.estragu = []; k.estragu_seluk = ''; }
		if (subar('grp-nesesidade')) { k.nesesidade = []; k.urjente = false; }
		return k;
	}

	// Validasaun kada pasu (hanesan regra server) — pasu tuir orden dokumentu pergunta RbR
	function valida(pasu) {
		var k = S.kazu, e = [];
		if (pasu === 1) {
			if (!k.data_relatoriu && !k.tinan_simu) e.push('Hakerek Data Simu ka Tinan Simu Kazu iha RbR.');
			if (k.data_relatoriu > hoje()) e.push('Data Simu labele iha futuru.');
			if (!k.tipu_konflitu.length) e.push('Hili Tipu Kazu.');
			if (!$('grp-tipu_seluk').hidden && !k.tipu_seluk) e.push('Favor esplika tipu konflitu "Seluk".');
		}
		if (pasu === 2) {
			if (!k.postu) e.push('Hili Postu Administrativu.');
			if (!k.suku) e.push('Hili Suku.');
			if (k.latitude == null) e.push('Foti koordenada GPS iha fatin akontesimentu.');
			else if (k.gps_akurasia > GPS_MAX) e.push('Akurasia GPS ' + k.gps_akurasia + ' m. Tenke ≤ 50 m.');
			(k.poligon_pontu || []).forEach(function (b, i) {
				if (b.length && b.length < 3) e.push('Poligon área ' + (i + 1) + ': presiza pontu 3 ka liu (ka hamoos).');
			});
			polBidang(k).forEach(function (f, i) { if (SIBARPoligon.kruza(f)) e.push('Poligon área ' + (i + 1) + ': liña kruza malu. Hamoos pontu ikus no foti fali.'); });
		}
		if (pasu === 3) {
			var a = k.afetadu;
			if (a.total_ema != null && a.mane != null && a.feto != null && a.mane + a.feto !== a.total_ema) e.push('Mane + Feto tenke hanesan Total Ema (' + (a.mane + a.feto) + ').');
		}
		if (pasu === 7) {
			if (k.data_akontesimentu && k.data_akontesimentu > hoje()) e.push('Data Akontesimentu labele iha futuru.');
			if (k.insidente && !k.insidente.tipu_eviksaun) e.push('Hili Tipu Eviksaun.');
		}
		if (pasu === 8 && !k.konsentimentu) e.push('Laiha konsentimentu = labele rai kazu.');
		return e;
	}

	// Tinan Simu automátiku husi Data Simu (manuál de'it se data la hatene)
	function tinanSimu() {
		var d = $('f-data_relatoriu').value, t = $('f-tinan_simu');
		if (d) t.value = parseInt(d.slice(0, 4), 10);
		t.readOnly = !!d;
	}
	$('f-data_relatoriu').addEventListener('change', tinanSimu);

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
			return DB.put('kazu', { id: k.id, estadu: estadu, kria_iha: k.kria_iha, atualiza: new Date().toISOString(), box: box, erru: null,
				kode: k.kode || null, followup: !!k.followup });
		});
	}

	function rezumu() {
		var k = S.kazu;
		var foto = nMedia('FOTO');
		var video = nMedia('VIDEO');
		var afe = k.afetadu || {};
		$('rezumu').innerHTML = '<div class="sub-box"><b>Rezumu</b><br>' +
			'Fatin: ' + esc(naranSuku(k.suku)) + ', ' + esc(S.opsaun.munisipiu.name) + '<br>' +
			'GPS: ' + (k.latitude != null ? k.latitude.toFixed(5) + ', ' + k.longitude.toFixed(5) + (k.gps_akurasia == null ? '' : ' (±' + k.gps_akurasia + ' m)') : '-') + '<br>' +
			'Uma-kain: ' + (afe.uma_kain == null ? '-' : afe.uma_kain) + ' · Ema: ' + (afe.total_ema == null ? '-' : afe.total_ema) + '<br>' +
			'Foto: ' + foto + '/' + MAX_FOTO + ' · Vídeo: ' + video + '/' + MAX_VIDEO +
			(k.nesesidade.length ? '<br><span class="badge badge-urjente">URJENTE</span>' : '') + '</div>';
	}

	// ══════════════ POLIGON RAI (la'o haleu rai ho GPS, offline) ══════════════
	var POL_GPS_MAX = 10;
	function polPontuHotu(k) { return (k.poligon_pontu || []).reduce(function (s, b) { return s + b.length; }, 0); }
	// Bidang ho pontu 3+ → Feature Polygon (anel taka)
	function polBidang(k) {
		return (k.poligon_pontu || []).filter(function (b) { return b.length >= 3; }).map(function (b) {
			var anel = b.map(function (p) { return [p[0], p[1]]; });
			anel.push(anel[0]);
			return turf.polygon([anel]);
		});
	}
	function luanRai(m2) { return m2 >= 10000 ? [Math.round(m2 / 100) / 100, 'HA'] : [Math.round(m2 * 100) / 100, 'M2']; }

	// Sketch SVG (la presiza mapa / internet) + luan, haleu, naruk × luan
	function polHatudu() {
		var k = S.kazu, P = SIBARPoligon;
		if (!k.poligon_pontu || !k.poligon_pontu.length) k.poligon_pontu = [[]];
		var bidang = k.poligon_pontu, fs = polBidang(k), hotu = [].concat.apply([], bidang), html = '';
		if (hotu.length) {
			var kx = Math.cos(hotu[0][1] * Math.PI / 180);
			var xs = hotu.map(function (p) { return p[0] * kx; }), ys = hotu.map(function (p) { return p[1]; });
			var minX = Math.min.apply(null, xs), maxX = Math.max.apply(null, xs), minY = Math.min.apply(null, ys), maxY = Math.max.apply(null, ys);
			var sk = Math.min(270 / ((maxX - minX) || 1e-9), 150 / ((maxY - minY) || 1e-9));
			var ox = (300 - (maxX - minX) * sk) / 2, oy = (180 - (maxY - minY) * sk) / 2;
			var pt = function (p) { return [(ox + (p[0] * kx - minX) * sk).toFixed(1), (180 - oy - (p[1] - minY) * sk).toFixed(1)]; };
			bidang.forEach(function (b, i) {
				var pts = b.map(function (p) { return pt(p).join(','); }).join(' ');
				if (b.length >= 3) html += '<polygon points="' + pts + '"/>';
				else if (b.length === 2) html += '<polyline points="' + pts + '"/>';
				b.forEach(function (p, j) {
					var c = pt(p);
					html += '<circle cx="' + c[0] + '" cy="' + c[1] + '" r="4"' + (i === bidang.length - 1 && j === b.length - 1 ? ' class="ativu"' : '') + '/>';
				});
				if (b.length >= 3) {
					var cc = pt(turf.centroid(polBidang({ poligon_pontu: [b] })[0]).geometry.coordinates);
					html += '<text x="' + cc[0] + '" y="' + cc[1] + '" text-anchor="middle">' + (i + 1) + '</text>';
				}
			});
		}
		$('pol-sketch').innerHTML = html;
		var atual = bidang[bidang.length - 1];
		var linha = ['Área ' + bidang.length + ': ' + atual.length + ' pontu' + (atual.length && atual.length < 3 ? ' (presiza 3+)' : '')];
		if (fs.length) {
			var r = P.kalkula(fs);
			r.bidang.forEach(function (m, i) {
				linha.push('<b>Área ' + (i + 1) + '</b>: ' + P.luan(m.luan_m2) + ' · haleu ' + P.metru(m.keliling_m) + ' · ' + P.metru(m.naruk_m) + ' × ' + P.metru(m.lebar_m) +
					(P.kruza(fs[i]) ? ' <span class="text-danger">· liña kruza!</span>' : ''));
			});
			if (fs.length > 1) linha.push('<b>Total: ' + P.luan(r.luan_m2) + '</b>');
			var lr = luanRai(r.luan_m2);
			$('f-rai_luan').value = lr[0]; $('f-rai_luan_unidade').value = lr[1];
		}
		$('pol-info').innerHTML = linha.join('<br>');
		$('f-rai_luan').readOnly = $('f-rai_luan_unidade').disabled = fs.length > 0;
		$('pol-desfaz').disabled = $('pol-hamoos').disabled = !hotu.length;
		$('pol-foun').disabled = atual.length < 3;
	}

	var polWatch = null, polTimer = null;
	function polPara() {
		if (polWatch !== null) navigator.geolocation.clearWatch(polWatch);
		clearTimeout(polTimer); polWatch = null;
		$('pol-pontu').disabled = false;
		$('pol-pontu').innerHTML = '<i class="fa fa-crosshairs"></i> Aumenta pontu';
	}
	// Pontu ida = GPS diak liu to'o ±10 m (hein máximu minutu 1)
	$('pol-pontu').addEventListener('click', function () {
		if (!navigator.geolocation) { msg('HP ne\'e la iha GPS.'); return; }
		var btn = this, diak = null;
		btn.disabled = true;
		btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Buka GPS…';
		polWatch = navigator.geolocation.watchPosition(function (p) {
			var c = p.coords;
			if (!diak || c.accuracy < diak.accuracy) diak = c;
			btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> ±' + Math.round(diak.accuracy) + ' m…';
			if (diak.accuracy > POL_GPS_MAX) return;
			polPara();
			var bidang = S.kazu.poligon_pontu, atual = bidang[bidang.length - 1];
			var foun = [Math.round(diak.longitude * 1e7) / 1e7, Math.round(diak.latitude * 1e7) / 1e7, Math.round(diak.accuracy)];
			var ikus = atual[atual.length - 1];
			if (ikus && turf.distance(ikus.slice(0, 2), foun.slice(0, 2), { units: 'meters' }) < 1) { msg('Pontu besik liu pontu ikus (< 1 m). La\'o ba kantu tuir mai.', 'info'); return; }
			atual.push(foun);
			msg(null);
			polHatudu(); raiRascunho(true);
		}, function (err) {
			polPara();
			msg(err.code === 1 ? 'Favor permite GPS (lokalizasaun) ba SIBAR-RbR iha setting browser.' : 'GPS la hetan sinál. Ba fatin loke no koko fali.');
		}, { enableHighAccuracy: true, maximumAge: 0, timeout: 60000 });
		polTimer = setTimeout(function () {
			polPara();
			msg('GPS la to\'o ±' + POL_GPS_MAX + ' m' + (diak ? ' (diak liu: ±' + Math.round(diak.accuracy) + ' m)' : '') + '. Hein uitoan iha fatin loke no koko fali.');
		}, 60000);
	});
	$('pol-desfaz').addEventListener('click', function () {
		var bidang = S.kazu.poligon_pontu;
		if (!bidang[bidang.length - 1].length && bidang.length > 1) bidang.pop();
		bidang[bidang.length - 1].pop();
		polHatudu(); raiRascunho(true);
	});
	$('pol-foun').addEventListener('click', function () {
		S.kazu.poligon_pontu.push([]);
		polHatudu(); raiRascunho(true);
	});
	$('pol-hamoos').addEventListener('click', function () {
		if (!confirm('Hamoos poligon hotu?')) return;
		S.kazu.poligon_pontu = [[]];
		polHatudu(); raiRascunho(true);
	});

	// ══════════════ GPS ══════════════
	var gpsWatch = null, gpsTimer = null;

	function hatuduGPS() {
		var k = S.kazu, info = $('gps-info');
		if (k.latitude == null) { info.className = 'small mt-1 text-muted'; info.textContent = 'Tenke iha fatin akontesimentu. Akurasia tenke ≤ 50 m.'; return; }
		info.className = 'small mt-1 ' + (k.gps_akurasia == null || k.gps_akurasia <= GPS_MAX ? 'text-success' : 'text-danger');
		info.innerHTML = '<i class="fa fa-check"></i> ' + k.latitude.toFixed(6) + ', ' + k.longitude.toFixed(6) + (k.gps_akurasia == null ? '' : ' · akurasia ±' + k.gps_akurasia + ' m');
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
			msg(err.code === 1 ? 'Favor permite GPS (lokalizasaun) ba SIBAR-RbR iha setting browser.' : 'GPS la hetan sinál. Ba fatin loke no koko fali.');
			hatuduGPS();
		}, { enableHighAccuracy: true, maximumAge: 0, timeout: 60000 });
		gpsTimer = setTimeout(function () {
			paraGPS();
			if (S.kazu.latitude == null) msg('GPS la to\'o akurasia 50 m iha minutu 2. Koko fali iha fatin loke.');
		}, 120000);
	});

	// ══════════════ EVIDÉNSIA (kámera ka galeria) ══════════════
	// Evidénsia iha HP + ida ne'ebé iha server ona (kazu follow-up)
	function nMedia(tipu) {
		var server = (S.kazu && S.kazu[tipu === 'FOTO' ? 'foto_server' : 'video_server']) || 0;
		return server + S.media.filter(function (m) { return m.tipu === tipu; }).length;
	}
	function limpaUrls() { S.urls.forEach(URL.revokeObjectURL); S.urls = []; }

	function hatuduMedia() {
		limpaUrls();
		var foto = nMedia('FOTO');
		var video = nMedia('VIDEO');
		$('n-foto').textContent = foto + '/' + MAX_FOTO;
		$('n-video').textContent = video + '/' + MAX_VIDEO;
		$('btn-foto').disabled = foto >= MAX_FOTO;
		$('btn-galeria').disabled = foto >= MAX_FOTO;
		$('btn-video').disabled = video >= MAX_VIDEO;
		$('btn-video-galeria').disabled = video >= MAX_VIDEO;
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
	// Galeria: hili foto barak dala ida (to'o restu husi 5)
	$('btn-galeria').addEventListener('click', function () {
		S.ativu = Date.now();
		var restu = MAX_FOTO - nMedia('FOTO');
		KAM.galeria(restu).then(function (r) {
			var pasu = Promise.resolve();
			r.blobs.forEach(function (b) { pasu = pasu.then(function () { return raiMedia('FOTO', b); }); });
			return pasu.then(function () {
				if (r.liu) msg('Foto ' + r.liu + ' la tama: máximu ' + MAX_FOTO + ' kada kazu.', 'info');
			});
		}).catch(function (e) { msg(e.message); });
	});
	$('btn-video').addEventListener('click', function () {
		S.ativu = Date.now();
		KAM.video().then(function (b) { return raiMedia('VIDEO', b); }).catch(function (e) { msg(e.message); });
	});
	// Vídeo husi galeria (liu 60 s → hili parte no kota)
	var kotaFile = null;
	function tempu(s) { s = Math.round(s); return Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); }
	function kotaTaka() {
		var pv = $('kota-video');
		pv.pause(); if (pv.src) URL.revokeObjectURL(pv.src); pv.removeAttribute('src');
		kotaFile = null; $('video-kota').hidden = true; $('kota-progress').hidden = true;
		$('kota-ok').disabled = false; $('kota-hahu').disabled = false;
	}
	function kotaInfo() {
		var h = parseInt($('kota-hahu').value, 10), pv = $('kota-video');
		$('kota-info').textContent = tempu(h) + ' – ' + tempu(Math.min(h + KAM.VIDEO_MAX_S, pv.duration || h + KAM.VIDEO_MAX_S)) + ' (husi ' + tempu(pv.duration || 0) + ')';
		if (pv.readyState) pv.currentTime = h;
	}
	$('btn-video-galeria').addEventListener('click', function () {
		S.ativu = Date.now();
		KAM.videoGaleria().then(function (r) {
			if (!r) return;
			if (!r.presizaKota) return raiMedia('VIDEO', r.file);
			kotaFile = r.file;
			var pv = $('kota-video');
			pv.src = URL.createObjectURL(r.file);
			$('kota-hahu').max = Math.max(0, Math.floor(r.durasaun - KAM.VIDEO_MAX_S));
			$('kota-hahu').value = 0;
			pv.onloadedmetadata = kotaInfo;
			$('video-kota').hidden = false;
		}).catch(function (e) { msg(e.message); });
	});
	$('kota-hahu').addEventListener('input', kotaInfo);
	$('kota-kansela').addEventListener('click', kotaTaka);
	$('kota-ok').addEventListener('click', function () {
		if (!kotaFile) return;
		S.ativu = Date.now();
		var bar = $('kota-progress'), barra = bar.firstElementChild;
		bar.hidden = false; barra.style.width = '0%';
		this.disabled = true; $('kota-hahu').disabled = true; $('kota-video').pause();
		msg('Kota hela vídeo… Labele taka ekran ka muda app.', 'info');
		KAM.kota(kotaFile, parseInt($('kota-hahu').value, 10), function (p) {
			barra.style.width = Math.round(p * 100) + '%'; S.ativu = Date.now();
		}).then(function (blob) {
			kotaTaka();
			return raiMedia('VIDEO', blob);
		}).then(function () { msg('Vídeo kota no rai ona.', 'success'); })
			.catch(function (e) { kotaTaka(); msg(e.message || 'Vídeo la bele kota.'); });
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
		var rbr = {};
		KAMPU_RBR.forEach(function (c) { if (k[c] != null && k[c] !== '') rbr[c] = k[c]; });
		return Object.assign(rbr, {
			id: k.id, kria_iha: k.kria_iha, titulu: k.titulu, data_relatoriu: k.data_relatoriu,
			postu: k.postu, suku: k.suku, aldeia: k.aldeia,
			latitude: k.latitude, longitude: k.longitude, gps_akurasia: k.gps_akurasia,
			data_akontesimentu: k.data_akontesimentu, tipu_konflitu: k.tipu_konflitu, tipu_seluk: k.tipu_seluk,
			tipu_rai: k.tipu_rai, deskrisaun: k.deskrisaun, estragu: k.estragu, estragu_seluk: k.estragu_seluk,
			nesesidade: k.nesesidade, konsentimentu: k.konsentimentu, la_publika: !!k.la_publika, observasaun: k.observasaun,
			afetadu: temAfetadu ? [afe] : [], insidente: k.insidente ? [k.insidente] : [], ator: k.ator || [],
			poligon: polBidang(k).length ? SIBARPoligon.fc(polBidang(k)) : null,
			segimentu: k.segimentu || {}
		});
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
					return (r.legal ? LEGAL().sinkron(r) : sinkronKazu(r)).then(function (res) { if (res) ok++; else erru++; });
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

	// Funsaun ba smkre_legal.js (survei legál)
	window.SmkreApp = {
		S: S, $: $, esc: esc, msg: msg, hatudu: hatudu, hoje: hoje, dataTL: dataTL, api: api, apiJSON: apiJSON,
		erruLista: erruLista, baVaranda: baVaranda, listaLokal: listaLokal, sinkronHotu: sinkronHotu,
		permValidu: permValidu, opsaunSelect: opsaunSelect, limpaUrls: limpaUrls, pedeRelogin: pedeRelogin, GPS_MAX: GPS_MAX
	};

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
