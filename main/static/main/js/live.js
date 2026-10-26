/* SIBAR-RbR Live — ekran boot: atualiza kada segundu 30, ekran tomak, ekran la toba (Wake Lock). */
(function () {
	'use strict';
	var B = document.body.dataset, T = window.LV_T || {};
	var URL_DADUS = B.url, SEG = parseInt(B.seg, 10) || 30, ROT_SEG = 15;
	var KOR = { brand: '#1FB58F', ink: '#EAF3EF', ink2: '#A9C2B8', mute: '#6F8C81', linha: '#21423A', pnl: '#10241E', warn: '#FAB219', krit: '#E04848' };
	var LORON = ['Domingu', 'Segunda', 'Tersa', 'Kuarta', 'Kinta', 'Sesta', 'Sábadu'];
	var FULAN = ['Janeiru', 'Fevereiru', 'Marsu', 'Abríl', 'Maiu', 'Juñu', 'Jullu', 'Agostu', 'Setembru', 'Outubru', 'Novembru', 'Dezembru'];
	var S = { d: null, kpi: {}, vistu: {}, primeiru: true, rot: 0, ultimu: null };

	function $(id) { return document.getElementById(id); }
	function esc(t) { var x = document.createElement('div'); x.textContent = t == null ? '' : String(t); return x.innerHTML; }
	function num(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }

	// ── Relójiu (oras Dili) ──
	function dili() {
		var p = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Dili', year: 'numeric', month: 'numeric', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).formatToParts(new Date());
		var o = {}; p.forEach(function (x) { o[x.type] = x.value; });
		var wd = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(o.weekday);
		return { oras: o.hour + ':' + o.minute, seg: o.second, data: LORON[wd] + ', ' + parseInt(o.day, 10) + ' ' + FULAN[parseInt(o.month, 10) - 1] + ' ' + o.year, h: parseInt(o.hour, 10), m: parseInt(o.minute, 10) };
	}
	function relojiu() {
		var d = dili();
		$('oras').textContent = d.oras;
		$('data').textContent = d.data;
		if (d.h === 3 && d.m === 0 && d.seg === '00') location.reload();      // kada loron 03:00: karrega versaun foun
	}
	setInterval(relojiu, 1000); relojiu();

	// ── Highcharts tema metan ──
	Highcharts.setOptions({
		chart: { backgroundColor: 'transparent', style: { fontFamily: 'Lato, Arial, sans-serif' }, spacing: [6, 6, 6, 6], animation: { duration: 800 } },
		title: { text: null }, credits: { enabled: false }, legend: { enabled: false }, exporting: { enabled: false },
		colors: [KOR.brand],
		xAxis: { lineColor: KOR.linha, tickColor: KOR.linha, labels: { style: { color: KOR.ink2, fontSize: '1.45vh' } } },
		yAxis: { gridLineColor: KOR.linha, title: { text: null }, labels: { style: { color: KOR.mute, fontSize: '1.3vh' } }, allowDecimals: false },
		tooltip: { backgroundColor: '#153027', borderColor: KOR.linha, style: { color: KOR.ink, fontSize: '1.5vh' } },
		plotOptions: { series: { animation: { duration: 900 } } },
		accessibility: { enabled: false },
		lang: { thousandsSep: '.', decimalPoint: ',' }
	});

	var trend = Highcharts.chart('ch-trend', {
		chart: { type: 'area' },
		xAxis: { categories: [] },
		yAxis: { min: 0 },
		plotOptions: { area: { lineWidth: 2, marker: { radius: 4, fillColor: KOR.brand, lineColor: KOR.pnl, lineWidth: 2 },
			fillColor: { linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 }, stops: [[0, 'rgba(31,181,143,.38)'], [1, 'rgba(31,181,143,0)']] } } },
		tooltip: { pointFormat: '<b>{point.y}</b> ' + T.kazu },
		series: [{ name: T.kazu, data: [], dataLabels: { enabled: true, style: { color: KOR.ink, fontSize: '1.5vh', textOutline: 'none' },
			filter: { property: 'index', operator: '>=', value: 11 } } }]
	});

	// ── Painel rotativu: munisípiu / tipu / status kazu ──
	var ROT = [
		{ titulu: '<i class="fa fa-map-marker"></i> ' + T.mun, dadus: function (d) { return d.mun.slice().sort(function (a, b) { return b.n - a.n; }).slice(0, 8); } },
		{ titulu: '<i class="fa fa-tags"></i> ' + T.tipu, dadus: function (d) { return d.tipu.slice(0, 6); } },
		{ titulu: '<i class="fa fa-flag"></i> ' + T.status, dadus: function (d) { return d.status_kazu; } }
	];
	var rotChart = null;
	function rotaRender() {
		if (!S.d) return;
		var r = ROT[S.rot], lista = r.dadus(S.d);
		$('rot-titulu').innerHTML = r.titulu;
		$('rot-dots').innerHTML = ROT.map(function (_x, i) { return '<i class="' + (i === S.rot ? 'on' : '') + '"></i>'; }).join('');
		if (rotChart) rotChart.destroy();
		rotChart = Highcharts.chart('ch-rot', {
			chart: { type: 'bar' },
			xAxis: { categories: lista.map(function (x) { return x.name; }), labels: { style: { color: KOR.ink2, fontSize: '1.4vh', textOverflow: 'ellipsis' }, x: -6 } },
			yAxis: { visible: false },
			plotOptions: { bar: { borderRadius: 4, borderWidth: 0, pointPadding: 0.12, groupPadding: 0.06,
				dataLabels: { enabled: true, style: { color: KOR.ink, fontSize: '1.45vh', textOutline: 'none' } } } },
			tooltip: { pointFormat: '<b>{point.y}</b> ' + T.kazu },
			series: [{ name: T.kazu, data: lista.map(function (x) { return x.n; }) }]
		});
	}
	setInterval(function () { S.rot = (S.rot + 1) % ROT.length; rotaRender(); }, ROT_SEG * 1000);

	// ── Mapa (fronteira munisípiu, la presiza tile internet) ──
	var mapa = L.map('mapa', { zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false,
		doubleClickZoom: false, boxZoom: false, keyboard: false, touchZoom: false, zoomSnap: 0.1 });
	mapa.createPane('pontu'); mapa.getPane('pontu').style.zIndex = 650;
	var munLayer = null, labelLayer = L.layerGroup().addTo(mapa), pinLayer = L.layerGroup().addTo(mapa);
	fetch(B.geojson).then(function (r) { return r.json(); }).then(function (g) {
		munLayer = L.geoJSON(g, { style: function () { return { color: '#2C5A4E', weight: 1, fillColor: '#1A3A31', fillOpacity: 1 }; } }).addTo(mapa);
		mapa.fitBounds(munLayer.getBounds(), { padding: [12, 12] });
		window.addEventListener('resize', function () { mapa.invalidateSize(); mapa.fitBounds(munLayer.getBounds(), { padding: [12, 12] }); });
		if (S.d) mapaRender(S.d);
	});
	function mistura(t) {
		// #1A3A31 → #1FB58F (sequensiál ida, kór ida)
		var a = [26, 58, 49], b = [31, 181, 143];
		return 'rgb(' + a.map(function (v, i) { return Math.round(v + (b[i] - v) * t); }).join(',') + ')';
	}
	function mapaRender(d) {
		if (!munLayer) return;
		var por = {}, max = 1;
		d.mun.forEach(function (m) { por[m.code] = m; max = Math.max(max, m.n); });
		$('esk-max').textContent = max;
		labelLayer.clearLayers();
		munLayer.eachLayer(function (l) {
			var m = por[l.feature.properties.code] || { n: 0, name: l.feature.properties.name };
			l.setStyle({ fillColor: mistura(Math.sqrt(m.n / max)) });
			var c = l.getBounds().getCenter();
			L.marker(c, { interactive: false, icon: L.divIcon({ className: 'mun-label', html: esc(m.name) + ' <b>' + m.n + '</b>', iconSize: null }) }).addTo(labelLayer);
		});
		pinLayer.clearLayers();
		d.pontu.slice().reverse().forEach(function (p) {
			if (p.urjente || p.foun) {
				var cls = 'pin ' + (p.urjente ? 'pin-u' : 'pin-foun') + (p.foun ? ' pin-pulsu' : '');
				var sz = p.urjente ? 14 : 12;
				L.marker([p.lat, p.lng], { pane: 'pontu', icon: L.divIcon({ className: cls, iconSize: [sz, sz] }) })
					.bindTooltip(esc(p.kode) + ' · ' + esc(p.fatin), { className: 'lv-tip' }).addTo(pinLayer);
			} else {
				L.circleMarker([p.lat, p.lng], { pane: 'pontu', radius: 4, color: KOR.pnl, weight: 2, fillColor: KOR.ink, fillOpacity: 0.9 })
					.bindTooltip(esc(p.kode) + ' · ' + esc(p.fatin), { className: 'lv-tip' }).addTo(pinLayer);
			}
		});
	}

	// ── KPI ho animasaun ──
	function konta(el, de, ba) {
		var t0 = performance.now(), dur = 1100;
		(function pasu(t) {
			var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
			el.textContent = num(de + (ba - de) * e);
			if (k < 1) requestAnimationFrame(pasu);
		})(t0);
	}
	function kpiRender(kpi) {
		document.querySelectorAll('[data-k]').forEach(function (el) {
			var k = el.dataset.k, uluk = S.kpi[k], foun = kpi[k] || 0;
			if (uluk === undefined) { konta(el, 0, foun); return; }
			if (uluk === foun) return;
			konta(el, uluk, foun);
			var box = el.closest('.kpi');
			if (box && el.classList.contains('kpi-n')) {
				box.classList.add('muda'); setTimeout(function () { box.classList.remove('muda'); }, 2500);
				var dl = document.createElement('span'); dl.className = 'delta'; dl.textContent = (foun > uluk ? '+' : '') + (foun - uluk);
				box.appendChild(dl); setTimeout(function () { dl.remove(); }, 4200);
			}
		});
		S.kpi = kpi;
		var dif = kpi.semana - kpi.semana_kotuk;
		$('semana').innerHTML = T.semana + ': <b>' + kpi.semana + '</b> ' + T.kazu + ' <span class="' + (dif >= 0 ? 'up' : 'down') + '"><i class="fa fa-caret-' + (dif >= 0 ? 'up' : 'down') + '"></i> ' + Math.abs(dif) + '</span>';
		$('semana').title = T.semanaKotuk + ': ' + kpi.semana_kotuk;
	}

	// ── Eviksaun (painel vertikál): Lae / Sin kór tuir signifikadu ──
	var EV_CHARTS = {};
	function evKor(q, code) {
		var aat = q === 'forsa' ? 'SIN' : 'LAE', diak = q === 'forsa' ? 'LAE' : 'SIN';
		return code === aat ? KOR.krit : (code === diak ? KOR.brand : KOR.mute);
	}
	function evikRender(ev) {
		if (!ev || !$('ch-ev-forsa')) return;
		document.querySelectorAll('[data-e]').forEach(function (el) { el.textContent = num(ev[el.dataset.e] || 0); });
		['konsultasaun', 'notifikasaun', 'forsa'].forEach(function (q) {
			var lista = ev[q] || [];
			var dadus = lista.map(function (x) { return { y: x.n, color: evKor(q, x.code) }; });
			var cat = lista.map(function (x) { return x.name; });
			if (EV_CHARTS[q] && EV_CHARTS[q].series[0].data.length === dadus.length) {
				EV_CHARTS[q].xAxis[0].setCategories(cat, false);
				EV_CHARTS[q].series[0].setData(dadus, true);
				return;
			}
			if (EV_CHARTS[q]) EV_CHARTS[q].destroy();
			EV_CHARTS[q] = Highcharts.chart('ch-ev-' + q, {
				chart: { type: 'bar' },
				xAxis: { categories: cat, labels: { style: { color: KOR.ink2, fontSize: '1.4vh' }, x: -6 } },
				yAxis: { visible: false },
				plotOptions: { bar: { borderRadius: 4, borderWidth: 0, pointPadding: 0.08, groupPadding: 0.04,
					dataLabels: { enabled: true, style: { color: KOR.ink, fontSize: '1.5vh', textOutline: 'none' } } } },
				tooltip: { pointFormat: '<b>{point.y}</b> ' + T.kazu },
				series: [{ name: T.kazu, data: dadus }]
			});
		});
	}

	// ── Atividade no prazu ──
	var IKON = { foun: 'fa-plus', ok: 'fa-check', alerta: 'fa-undo', info: 'fa-street-view', legal: 'fa-balance-scale' };
	function liuBa(iso) {
		var s = (Date.now() - new Date(iso).getTime()) / 1000;
		if (s < 90) return T.agora;
		if (s < 3600) return Math.round(s / 60) + ' ' + T.min;
		if (s < 86400) return Math.round(s / 3600) + ' ' + T.oras;
		return Math.round(s / 86400) + ' ' + T.loron;
	}
	function ativRender(lista) {
		// Lista atividade la hatudu tan (painel eviksaun); kazu foun → toast nafatin
		var el = $('atividade') || document.createElement('ul');
		if (!lista.length) { el.innerHTML = '<li class="vaziu">' + esc(T.laAtiv) + '</li>'; return; }
		var foun = [];
		el.innerHTML = lista.map(function (e) {
			var key = e.tempu + e.kode + e.testu, novu = !S.primeiru && !S.vistu[key];
			if (novu) foun.push(e);
			S.vistu[key] = 1;
			return '<li class="' + (novu ? 'foun-li' : '') + '"><span class="ik ' + e.tipu + '"><i class="fa ' + (IKON[e.tipu] || 'fa-circle') + '"></i></span>' +
				'<div class="tx"><div class="t1">' + esc(e.testu) + '</div><div class="t2">' + esc(e.kode) + (e.fatin ? ' · ' + esc(e.fatin) : '') + ' · ' + liuBa(e.tempu) + '</div></div></li>';
		}).join('');
		var kazuFoun = foun.filter(function (e) { return e.tipu === 'foun'; })[0];
		if (kazuFoun) toast('<i class="fa fa-bell"></i> ' + esc(T.foun) + ' · ' + esc(kazuFoun.kode) + ' · ' + esc(kazuFoun.fatin));
	}
	function prazuRender(lista) {
		var el = $('prazu');
		if (!el) return;
		if (!lista.length) { el.innerHTML = '<li class="vaziu">' + esc(T.laPrazu) + '</li>'; return; }
		el.innerHTML = lista.map(function (p) {
			var cls = p.loron < 0 ? 'krit' : (p.loron <= 3 ? 'warn' : ''), dt = p.data.split('-');
			var txt = p.loron < 0 ? '<i class="fa fa-exclamation-circle"></i> ' + T.prazuLiu : (p.loron === 0 ? T.prazuOhin : p.loron + ' ' + T.prazuLoron);
			return '<li><div style="min-width:0"><div class="p1">' + esc(p.kode) + '</div><div class="p2">' + esc(p.tipu) + ' · ' + dt[2] + '/' + dt[1] + '/' + dt[0] + '</div></div><span class="badge ' + cls + '">' + txt + '</span></li>';
		}).join('');
	}
	function toast(html) {
		var t = $('toast'); t.innerHTML = html; t.hidden = false;
		t.style.animation = 'none'; void t.offsetWidth; t.style.animation = '';
		clearTimeout(t._h); t._h = setTimeout(function () { t.hidden = true; }, 6000);
	}

	// ── Karrega dadus ──
	function estadu(ok, testu) {
		var e = $('estadu');
		e.classList.toggle('offline', !ok);
		e.querySelector('span').textContent = ok ? 'LIVE' : 'OFFLINE';
		$('atualiza').textContent = testu;
	}
	function banner(testu) {
		var b = document.querySelector('.erru-banner');
		if (!testu) { if (b) b.remove(); return; }
		if (!b) { b = document.createElement('div'); b.className = 'erru-banner'; document.body.appendChild(b); }
		b.textContent = testu;
	}
	function karrega() {
		var ctl = window.AbortController ? new AbortController() : null;
		var tm = setTimeout(function () { if (ctl) ctl.abort(); }, 15000);
		fetch(URL_DADUS, { credentials: 'same-origin', cache: 'no-store', headers: { Accept: 'application/json' }, signal: ctl ? ctl.signal : undefined, redirect: 'manual' })
			.then(function (r) {
				clearTimeout(tm);
				if (r.status === 404) { banner(T.kansela); throw new Error('kansela'); }
				if (r.type === 'opaqueredirect' || r.status === 403 || r.status === 302) { banner(T.sesaun); throw new Error('sesaun'); }
				if (!r.ok) throw new Error('server');
				return r.json();
			})
			.then(function (d) {
				banner(null);
				S.d = d;
				kpiRender(d.kpi);
				trend.xAxis[0].setCategories(d.fulan.map(function (f) { return f.label; }), false);
				trend.series[0].setData(d.fulan.map(function (f) { return f.n; }), true, { duration: 900 });
				mapaRender(d);
				ativRender(d.atividade);
				prazuRender(d.prazu);
				evikRender(d.evik);
				if (S.primeiru) rotaRender();
				S.primeiru = false;
				S.ultimu = dili().oras + ':' + dili().seg;
				estadu(true, T.atualiza + ' ' + S.ultimu);
			})
			.catch(function () { clearTimeout(tm); estadu(false, T.offline + ' ' + (S.ultimu || '-')); });
	}
	karrega();
	setInterval(karrega, SEG * 1000);

	// ── Ekran tomak + ekran la toba ──
	var lock = null;
	function moris() {
		if (!('wakeLock' in navigator) || document.visibilityState !== 'visible') return;
		navigator.wakeLock.request('screen').then(function (l) {
			lock = l; $('kordaun').hidden = false;
			l.addEventListener('release', function () { $('kordaun').hidden = true; });
		}).catch(function () { $('kordaun').hidden = true; });
	}
	document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && (!lock || lock.released)) moris(); });
	function tomak() {
		var el = document.documentElement;
		var f = el.requestFullscreen || el.webkitRequestFullscreen;
		if (f) { try { var pr = f.call(el); if (pr && pr.catch) pr.catch(function () {}); } catch (e) { /* browser la permite */ } }
	}
	function ehTomak() { return !!(document.fullscreenElement || document.webkitFullscreenElement) || (window.innerHeight >= screen.height - 2 && window.innerWidth >= screen.width - 2); }
	function hahu() { $('hahu').hidden = true; tomak(); moris(); }
	$('btn-hahu').addEventListener('click', hahu);
	$('btn-tomak').addEventListener('click', function () { tomak(); moris(); });
	document.addEventListener('fullscreenchange', function () { $('btn-tomak').hidden = ehTomak(); });
	// Browser iha modu kiosk (ekran tomak ona) ka ?kiosk=1 → la presiza klik
	if (ehTomak() || /[?&]kiosk=1/.test(location.search)) { $('hahu').hidden = true; moris(); }
	else { $('btn-tomak').hidden = false; }
	moris();
	window.addEventListener('keydown', function (e) { if (e.key === 'f' || e.key === 'F') tomak(); });

	// Kursór subar bainhira la uza segundu 3
	var kt = null;
	function kursor() { document.body.classList.remove('kursor-subar'); clearTimeout(kt); kt = setTimeout(function () { document.body.classList.add('kursor-subar'); }, 3000); }
	document.addEventListener('mousemove', kursor); kursor();
})();
