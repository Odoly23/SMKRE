/* SIBAR-RbR landing públiku: dadus hotu husi API públiku (/api/portal/estatistika/) — agregadu no anónimu.
   Layout hanesan ekran Live, tema naroman. Atualiza kada minutu 5. */
(function () {
	'use strict';
	var CFG = document.getElementById('portal-cfg').dataset;
	var T = JSON.parse(document.getElementById('portal-lang').textContent || '{}');
	var KOR = { green: '#1A4D2E', brand: '#0E8A68', earth: '#8B3A2B', mute: '#A8A29E', ink: '#1C1917', ink2: '#44403C', linha: '#E7E1D6' };
	var ATUALIZA_MIN = 5;
	var S = { kpi: {}, d: null };

	function $(id) { return document.getElementById(id); }
	function esc(t) { var x = document.createElement('div'); x.textContent = t == null ? '' : String(t); return x.innerHTML; }
	function num(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
	// valór husi API: {n, label} (n=null → "< 3") ka númeru simples ka null
	function valor(v) {
		if (v == null) return { n: null, label: '–' };
		if (typeof v === 'object') return { n: v.n, label: v.label };
		return { n: v, label: num(v) };
	}

	// ── Relójiu (oras Dili) ──
	(function () {
		var g = $('relojiu-tk');
		if (g) {
			var h = '';
			for (var i = 0; i < 60; i++) {
				var boot = i % 5 === 0;
				h += '<line class="tk' + (boot ? ' tk5' : '') + '" x1="50" y1="' + (boot ? 5 : 6) + '" x2="50" y2="' + (boot ? 13 : 9) + '" transform="rotate(' + (i * 6) + ' 50 50)"/>';
			}
			g.innerHTML = h;
		}
	})();
	function dili() {
		var p = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Dili', year: 'numeric', month: 'numeric', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date());
		var o = {}; p.forEach(function (x) { o[x.type] = x.value; });
		var wd = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(o.weekday);
		return { loron: (T.loron || [])[wd] || '', data: parseInt(o.day, 10) + ' ' + ((T.fulan || [])[parseInt(o.month, 10) - 1] || '') + ' ' + o.year, oras: o.hour + ':' + o.minute };
	}
	function relojiu() {
		var d = dili();
		$('loron').textContent = d.loron; $('data').textContent = d.data; $('oras').textContent = d.oras;
	}
	var JR = { o: $('jarum-oras'), m: $('jarum-min'), s: $('jarum-seg') };
	function jarum() {
		var t = new Date(Date.now() + 9 * 3600000);
		var s = t.getUTCSeconds() + t.getUTCMilliseconds() / 1000, m = t.getUTCMinutes() + s / 60, h = (t.getUTCHours() % 12) + m / 60;
		JR.s.setAttribute('transform', 'rotate(' + (s * 6) + ' 50 50)');
		JR.m.setAttribute('transform', 'rotate(' + (m * 6) + ' 50 50)');
		JR.o.setAttribute('transform', 'rotate(' + (h * 30) + ' 50 50)');
		requestAnimationFrame(jarum);
	}
	if ($('loron')) { relojiu(); setInterval(relojiu, 1000); }
	if (JR.s && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) requestAnimationFrame(jarum);

	// ── Highcharts tema naroman ──
	Highcharts.setOptions({
		chart: { backgroundColor: 'transparent', style: { fontFamily: 'Lato, Arial, sans-serif' }, spacing: [6, 6, 6, 6] },
		title: { text: null }, credits: { enabled: false }, legend: { enabled: false }, exporting: { enabled: false },
		colors: [KOR.brand],
		xAxis: { lineColor: KOR.linha, tickColor: KOR.linha, labels: { style: { color: KOR.ink2, fontSize: '12px' } } },
		yAxis: { gridLineColor: KOR.linha, title: { text: null }, labels: { style: { color: KOR.mute, fontSize: '11px' } }, allowDecimals: false, min: 0 },
		tooltip: { backgroundColor: '#fff', borderColor: KOR.linha, style: { color: KOR.ink, fontSize: '12px' } },
		accessibility: { enabled: false },
		lang: { thousandsSep: '.', decimalPoint: ',', noData: T.la_iha }
	});
	// pontu barra: y = n (ka 0 bainhira subar); label = "< 3" / númeru
	function pontu(lista, kor) {
		return lista.map(function (x) { return { y: x.n == null ? 0 : x.n, label: x.label, color: kor ? kor(x) : undefined }; });
	}
	var dl = { enabled: true, format: '{point.label}', style: { color: KOR.ink, fontSize: '12px', textOutline: 'none' } };
	var tipBarra = { pointFormat: '<b>{point.label}</b> ' + (T.kazu || '') };

	function barra(id, cat, dadus, h) {
		var larg = Math.max(90, Math.round(($(id).clientWidth || 300) * 0.4));
		return Highcharts.chart(id, {
			chart: { type: 'bar', height: h || null },
			xAxis: { categories: cat, labels: { x: -6, style: { color: KOR.ink2, fontSize: '12px', width: larg + 'px', textOverflow: 'ellipsis', lineClamp: 2 } } },
			yAxis: { visible: false },
			plotOptions: { bar: { borderRadius: 4, borderWidth: 0, pointPadding: 0.1, groupPadding: 0.05, dataLabels: dl } },
			tooltip: tipBarra,
			series: [{ name: T.kazu, data: dadus }]
		});
	}

	// ── Mapa (fronteira munisípiu, la presiza tile internet; la iha pontu kazu) ──
	var mapa = L.map('mapa', { zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false,
		doubleClickZoom: false, boxZoom: false, keyboard: false, touchZoom: false, tap: false, zoomSnap: 0.1 });
	var munLayer = null, labelLayer = L.layerGroup().addTo(mapa);
	fetch(CFG.geojson).then(function (r) { return r.json(); }).then(function (g) {
		munLayer = L.geoJSON(g, { style: function () { return { color: '#B8C9BF', weight: 1, fillColor: '#F1F5F2', fillOpacity: 1 }; } }).addTo(mapa);
		mapaHadia();
		window.addEventListener('resize', mapaHadia);
		if (S.d) mapaRender(S.d);
	}).catch(function () { /* mapa la karrega: painel seluk la'o nafatin */ });
	function mapaHadia() {
		var el = $('mapa');
		if (!munLayer || !el.clientWidth || !el.clientHeight) return;
		try { mapa.invalidateSize(); mapa.fitBounds(munLayer.getBounds(), { padding: [10, 10] }); } catch (e) { /* layout seidauk prontu */ }
	}
	function mistura(t) {
		// #E3EFE9 → #0E8A68 (sequensiál, kór ida)
		var a = [227, 239, 233], b = [14, 138, 104];
		return 'rgb(' + a.map(function (v, i) { return Math.round(v + (b[i] - v) * t); }).join(',') + ')';
	}
	function mapaRender(d) {
		if (!munLayer) return;
		var por = {}, max = 1;
		d.munisipiu.forEach(function (m) { por[m.code] = m; if (m.n) max = Math.max(max, m.n); });
		$('esk-max').textContent = num(max);
		labelLayer.clearLayers();
		var label = $('mapa').clientWidth >= 600;          // HP: label tumpuk malu → lista okos mapa
		munLayer.eachLayer(function (l) {
			var p = l.feature.properties, m = por[p.code] || { n: 0, label: '0', name: p.name };
			var n = m.n == null ? 1 : m.n;          // "< 3": kór naroman liu
			l.setStyle({ fillColor: n ? mistura(Math.sqrt(n / max)) : '#F1F5F2' });
			l.bindTooltip(esc(m.name || p.name) + ': <b>' + esc(m.label) + '</b> ' + esc(T.kazu), { sticky: true });
			if (!label) return;
			var c = l.getBounds().getCenter();
			L.marker(c, { interactive: false, icon: L.divIcon({ className: 'mun-label', html: esc(m.name || p.name) + ' <b>' + esc(m.label) + '</b>', iconSize: null }) }).addTo(labelLayer);
		});
	}

	// lista munisípiu (HP): boot → ki'ik
	function munListaRender(d) {
		var el = $('mun-lista');
		if (!el) return;
		el.innerHTML = d.munisipiu.slice().sort(function (a, b) { return (b.n == null ? 1 : b.n) - (a.n == null ? 1 : a.n); })
			.map(function (m) { return '<li class="' + (m.n === 0 ? 'zero' : '') + '">' + esc(m.name) + ' <b>' + esc(m.label) + '</b></li>'; }).join('');
	}

	// ── KPI ho animasaun konta ──
	function konta(el, de, ba) {
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = num(ba); return; }
		var t0 = performance.now(), dur = 1000;
		(function pasu(t) {
			var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
			el.textContent = num(de + (ba - de) * e);
			if (k < 1) requestAnimationFrame(pasu);
		})(t0);
	}
	function kpiRender(d) {
		var ev = d.eviksaun || {};
		var kpi = { total: valor(d.kpi.total), munisipiu: valor(d.kpi.munisipiu), uma_kain: valor(d.kpi.uma_kain),
			ema: valor(d.kpi.ema), eviksaun: valor(ev.total), evik_uma: valor(ev.uma_kain) };
		document.querySelectorAll('[data-k]').forEach(function (el) {
			var v = kpi[el.dataset.k];
			if (!v) return;
			if (v.n == null) { el.textContent = v.label; return; }
			var uluk = S.kpi[el.dataset.k];
			konta(el, uluk && uluk.n != null ? uluk.n : 0, v.n);
		});
		S.kpi = kpi;
		var top = d.tipu.filter(function (t) { return t.n; }).sort(function (a, b) { return b.n - a.n; })[0];
		$('tipu-top').textContent = top ? top.name : '–';
		$('tipu-top-n').innerHTML = top ? '<b>' + esc(top.label) + '</b> ' + esc(T.kazu) : '&nbsp;';
	}

	// ── Gráfiku ──
	var CH = {};
	function tinanRender(lista) {
		var cat = lista.map(function (x) { return String(x.tinan); }), dadus = pontu(lista);
		if (CH.tinan) { CH.tinan.xAxis[0].setCategories(cat, false); CH.tinan.series[0].setData(dadus, true); return; }
		CH.tinan = Highcharts.chart('ch-tinan', {
			chart: { type: 'column' },
			xAxis: { categories: cat },
			plotOptions: { column: { borderRadius: 4, borderWidth: 0, color: KOR.brand, dataLabels: dl } },
			tooltip: tipBarra,
			series: [{ name: T.kazu, data: dadus }]
		});
	}
	function tipuRender(lista) {
		var l = lista.filter(function (t) { return t.n !== 0; }).sort(function (a, b) { return (b.n || 0) - (a.n || 0); });
		if (CH.tipu) CH.tipu.destroy();
		CH.tipu = barra('ch-tipu', l.map(function (t) { return t.name; }), pontu(l));
	}
	function evKor(q) {
		var aat = q === 'forsa' ? 'SIN' : 'LAE', diak = q === 'forsa' ? 'LAE' : 'SIN';
		return function (x) { return x.code === aat ? KOR.earth : (x.code === diak ? KOR.brand : KOR.mute); };
	}
	function evikRender(ev) {
		var iha = ev && ev.konsultasaun && ev.konsultasaun.length;
		$('evik-vaziu').hidden = !!iha;
		['konsultasaun', 'notifikasaun', 'forsa'].forEach(function (q) {
			var box = $('ch-ev-' + q).parentNode;
			box.hidden = !iha;
			if (!iha) return;
			if (CH['ev' + q]) CH['ev' + q].destroy();
			CH['ev' + q] = barra('ch-ev-' + q, ev[q].map(function (x) { return x.name; }), pontu(ev[q], evKor(q)));
		});
	}

	// ── Karrega dadus husi API ──
	function estadu(ok, d) {
		var e = $('estadu');
		e.innerHTML = ok
			? '<i class="fa fa-circle"></i> ' + (d.atualiza ? esc(T.dadus_ikus) + ': ' + esc(d.atualiza) : esc(T.atualiza) + ' ' + esc(dili().oras))
			: '<i class="fa fa-exclamation-triangle"></i> ' + esc(T.offline);
	}
	function karrega() {
		var ctl = window.AbortController ? new AbortController() : null;
		var tm = setTimeout(function () { if (ctl) ctl.abort(); }, 20000);
		fetch(CFG.api, { credentials: 'same-origin', headers: { Accept: 'application/json' }, signal: ctl ? ctl.signal : undefined })
			.then(function (r) { clearTimeout(tm); if (!r.ok) throw new Error('server'); return r.json(); })
			.then(function (d) {
				S.d = d;
				// painel ida-idak separadu: erru iha painel ida la para painel seluk
				[function () { kpiRender(d); }, function () { mapaRender(d); }, function () { munListaRender(d); }, function () { tinanRender(d.tinan || []); },
				 function () { tipuRender(d.tipu || []); }, function () { evikRender(d.eviksaun); }
				].forEach(function (f) { try { f(); } catch (e) { if (window.console) console.error(e); } });
				estadu(true, d);
			})
			.catch(function () { clearTimeout(tm); estadu(false); });
	}
	karrega();
	setInterval(karrega, ATUALIZA_MIN * 60000);
})();
