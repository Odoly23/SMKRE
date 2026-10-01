/* Portal Públiku SMKRE — mapa + gráfiku interativu (filtru krúzadu).
   Klik barra / munisípiu iha mapa → filtru → KPI, mapa no gráfiku hotu atualiza.
   Dadus husi /api/portal/estatistika/ (agregadu, anónimu; 1–2 = "< 3"). */
(function () {
	'use strict';
	var CFG = document.getElementById('portal-cfg').dataset;
	var T = JSON.parse(document.getElementById('portal-lang').textContent);

	// ── Kór (validadu: scripts/validate_palette.js) ──
	var K = {
		serie: '#0E8A68',        // seriu ida (gráfiku barra)
		fade: '#a9d8c7',         // barra la hili bainhira iha filtru
		subar: '#c3c2b7',        // "< 3" (neutru)
		mane: '#2a78d6', feto: '#eb6834',
		ink: '#0b0b0b', ink2: '#52514e', muted: '#898781', grid: '#e1e0d9', surface: '#ffffff'
	};
	// Mapa (sekuensiál, kór ida: teal naroman → metin)
	var BIN = [[20, '#0b6b50'], [10, '#1f9a74'], [5, '#5fbf9f'], [1, '#a3dcc8'], [0, '#eef3f1']];

	var F = { munisipiu: '', tipu: '', tinan: '' };
	var DADUS = null;
	var charts = {};

	function $(id) { return document.getElementById(id); }
	function esc(t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
	function fmt(n) { return n == null ? '–' : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
	function reduzMovimentu() { return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; }

	// ── Menu HP ──
	$('p-ham').addEventListener('click', function () {
		var ul = $('p-links'), aberto = ul.classList.toggle('open');
		this.setAttribute('aria-expanded', aberto);
	});
	document.querySelectorAll('#p-links a[href^="#"]').forEach(function (a) {
		a.addEventListener('click', function () { $('p-links').classList.remove('open'); });
	});

	// ── Filtru ──
	function leeURL() {
		var q = new URLSearchParams(window.location.search);
		F.munisipiu = q.get('munisipiu') || '';
		F.tipu = q.get('tipu') || '';
		F.tinan = q.get('tinan') || '';
	}

	function hakerekURL() {
		var q = new URLSearchParams();
		Object.keys(F).forEach(function (k) { if (F[k]) q.set(k, F[k]); });
		var s = q.toString();
		var url = window.location.pathname + (s ? '?' + s : '');
		history.replaceState(null, '', url + window.location.hash);
		// Troka lian (bandeira) → fila ba pájina ho filtru hanesan
		document.querySelectorAll('.p-lian input[name="next"]').forEach(function (i) { i.value = url; });
	}

	function hili(k, v) {
		F[k] = String(F[k]) === String(v) ? '' : String(v);   // klik fali = hamoos
		sinkronizaSelect();
		karrega();
	}

	function sinkronizaSelect() {
		$('f-munisipiu').value = F.munisipiu;
		$('f-tipu').value = F.tipu;
		$('f-tinan').value = F.tinan;
	}

	['munisipiu', 'tipu', 'tinan'].forEach(function (k) {
		$('f-' + k).addEventListener('change', function () { F[k] = this.value; karrega(); });
	});
	$('btn-reset').addEventListener('click', function () {
		F = { munisipiu: '', tipu: '', tinan: '' };
		sinkronizaSelect();
		karrega();
	});

	function chips() {
		var box = $('chips');
		box.textContent = '';
		var nomes = {
			munisipiu: [T.munisipiu, $('f-munisipiu').selectedOptions[0]],
			tipu: [T.tipu, $('f-tipu').selectedOptions[0]],
			tinan: [T.tinan, $('f-tinan').selectedOptions[0]]
		};
		Object.keys(F).forEach(function (k) {
			if (!F[k]) return;
			var b = document.createElement('button');
			b.type = 'button';
			b.className = 'p-chip';
			var opt = nomes[k][1];
			b.textContent = nomes[k][0] + ': ' + (opt ? opt.textContent : F[k]) + ' ';
			var x = document.createElement('i');
			x.className = 'fa fa-times';
			b.appendChild(x);
			b.setAttribute('aria-label', T.klik_hamoos);
			b.addEventListener('click', function () { F[k] = ''; sinkronizaSelect(); karrega(); });
			box.appendChild(b);
		});
	}

	// ── Karrega dadus (frame hela, opasidade menus durante karrega) ──
	function karrega() {
		hakerekURL();
		chips();
		document.body.classList.add('p-loading');
		var q = new URLSearchParams();
		Object.keys(F).forEach(function (k) { if (F[k]) q.set(k, F[k]); });
		fetch(CFG.api + '?' + q.toString(), { headers: { Accept: 'application/json' } })
			.then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
			.then(function (d) {
				DADUS = d;
				tinanOpsaun(d.tinan);
				kpi(d.kpi);
				$('atualiza').textContent = d.atualiza || '–';
				grafikuMunisipiu(d.munisipiu);
				grafikuTipu(d.tipu);
				grafikuTinan(d.tinan);
				grafikuAfetadu(d.afetadu);
				grafikuSuku(d);
				mapaEstilu();
			})
			.catch(function () { /* la iha koneksaun: hela ho dadus uluk */ })
			.then(function () { document.body.classList.remove('p-loading'); chips(); });
	}

	function tinanOpsaun(lista) {
		var sel = $('f-tinan'), atual = F.tinan;
		var tinan = lista.map(function (t) { return String(t.tinan); });
		if (atual && tinan.indexOf(atual) < 0) tinan.push(atual);
		tinan.sort().reverse();
		while (sel.options.length > 1) sel.remove(1);
		tinan.forEach(function (y) { var o = new Option(y, y); sel.add(o); });
		sel.value = atual;
	}

	// ── KPI (animasaun konta) ──
	function kpi(d) {
		var val = { total: d.total.n, uma_kain: d.uma_kain, ema: d.ema, munisipiu: d.munisipiu };
		document.querySelectorAll('[data-kpi]').forEach(function (el) {
			var k = el.dataset.kpi, fim = val[k];
			if (k === 'total' && d.total.n == null) { el.textContent = d.total.label; return; }
			if (fim == null) { el.textContent = '–'; el.title = T.subar; return; }
			el.title = '';
			if (reduzMovimentu()) { el.textContent = fmt(fim); return; }
			var inisiu = parseInt(String(el.dataset.v || 0), 10) || 0, t0 = null;
			el.dataset.v = fim;
			function pasu(t) {
				if (!t0) t0 = t;
				var p = Math.min(1, (t - t0) / 700);
				el.textContent = fmt(Math.round(inisiu + (fim - inisiu) * (1 - Math.pow(1 - p, 3))));
				if (p < 1) requestAnimationFrame(pasu);
			}
			requestAnimationFrame(pasu);
		});
	}

	// ── Highcharts: estilu komún ──
	Highcharts.setOptions({
		lang: T.highcharts,
		credits: { enabled: false },
		colors: [K.serie],
		chart: { style: { fontFamily: 'Lato, system-ui, sans-serif' }, backgroundColor: 'transparent', spacing: [34, 8, 8, 4] },
		title: { text: null },
		legend: { enabled: false, itemStyle: { color: K.ink2, fontWeight: '400' } },
		xAxis: { lineColor: K.grid, tickLength: 0, labels: { style: { color: K.ink2, fontSize: '12px' } } },
		yAxis: { title: { text: null }, gridLineColor: K.grid, allowDecimals: false, labels: { style: { color: K.muted } } },
		tooltip: { backgroundColor: '#ffffff', borderColor: 'rgba(11,11,11,0.10)', borderRadius: 8, shadow: true, style: { color: K.ink } },
		plotOptions: {
			series: { animation: { duration: reduzMovimentu() ? 0 : 500 }, cursor: 'pointer', states: { hover: { brightness: 0.08 }, inactive: { opacity: 1 } } },
			bar: { borderRadius: 4, borderWidth: 0, pointPadding: 0.08, groupPadding: 0.06 },
			column: { borderRadius: 4, borderWidth: 0, pointPadding: 0.08, groupPadding: 0.06 }
		},
		exporting: { fallbackToExportServer: false, buttons: { contextButton: { menuItems: ['viewFullscreen', 'printChart', 'separator', 'downloadPNG', 'downloadPDF', 'downloadCSV', 'viewData'] } } }
	});

	// Pontu ho "< 3": barra neutru badak (valór minimu 1, la hatudu númeru loos), label "< 3"
	function pontu(item, nome, ativu) {
		var subar = item.n == null;
		return {
			name: nome, y: subar ? 1 : item.n, label: item.label, subar: subar,
			color: subar ? K.subar : (ativu === false ? K.fade : K.serie)
		};
	}

	function tooltipKazu() {
		return '<span style="font-size:15px;font-weight:700">' + this.point.label + '</span> ' + T.kazu +
			'<br><span style="color:' + K.ink2 + '">' + esc(this.point.name) + '</span>' +
			(this.point.subar ? '<br><span style="color:' + K.muted + '">' + T.subar + '</span>' : '') +
			'<br><span style="color:' + K.muted + ';font-size:11px">' + T.klik + '</span>';
	}

	function barLabels() {
		return { enabled: true, formatter: function () { return this.point.label; }, style: { color: K.ink2, fontWeight: '700', textOutline: 'none' } };
	}

	function graficu(id, opt) {
		if (charts[id]) { charts[id].update(opt, true, true); return charts[id]; }
		charts[id] = Highcharts.chart(id, opt);
		return charts[id];
	}

	function grafikuMunisipiu(lista) {
		var items = lista.slice().sort(function (a, b) { return (b.n == null ? 1.5 : b.n) - (a.n == null ? 1.5 : a.n); });
		var dados = items.map(function (m) {
			var p = pontu(m, m.name, F.munisipiu ? m.code === F.munisipiu : undefined);
			p.code = m.code;
			return p;
		});
		graficu('chart-munisipiu', {
			chart: { type: 'bar' },
			xAxis: { categories: items.map(function (m) { return m.name; }) },
			yAxis: { visible: false },
			tooltip: { formatter: tooltipKazu, useHTML: false },
			series: [{ name: T.kazu, data: dados, dataLabels: barLabels(),
				point: { events: { click: function () { hili('munisipiu', this.code); } } } }]
		});
	}

	function grafikuTipu(lista) {
		var dados = lista.map(function (t) {
			var p = pontu(t, t.name, F.tipu ? String(t.id) === F.tipu : undefined);
			p.tipu = t.id;
			return p;
		});
		graficu('chart-tipu', {
			chart: { type: 'bar' },
			xAxis: { categories: lista.map(function (t) { return t.name; }) },
			yAxis: { visible: false },
			tooltip: { formatter: tooltipKazu },
			series: [{ name: T.kazu, data: dados, dataLabels: barLabels(),
				point: { events: { click: function () { hili('tipu', this.tipu); } } } }]
		});
	}

	function grafikuTinan(lista) {
		var dados = lista.map(function (t) {
			var p = pontu(t, String(t.tinan), F.tinan ? String(t.tinan) === F.tinan : undefined);
			p.tinan = t.tinan;
			return p;
		});
		graficu('chart-tinan', {
			chart: { type: 'column' },
			xAxis: { categories: lista.map(function (t) { return String(t.tinan); }) },
			yAxis: { visible: true },
			tooltip: { formatter: tooltipKazu },
			series: [{ name: T.kazu, data: dados, dataLabels: barLabels(),
				point: { events: { click: function () { hili('tinan', this.tinan); } } } }]
		});
	}

	function grafikuAfetadu(lista) {
		graficu('chart-afetadu', {
			chart: { type: 'bar' },
			legend: { enabled: true, align: 'left', verticalAlign: 'top', symbolRadius: 2 },
			xAxis: { categories: lista.map(function (m) { return m.name; }) },
			yAxis: { visible: true, reversedStacks: false },
			tooltip: {
				shared: true, formatter: function () {
					var m = lista[this.points[0].point.index];
					return '<b>' + esc(m.name) + '</b><br>' +
						'<span style="color:' + K.mane + '">▬</span> ' + T.mane + ': <b>' + fmt(m.mane) + '</b><br>' +
						'<span style="color:' + K.feto + '">▬</span> ' + T.feto + ': <b>' + fmt(m.feto) + '</b><br>' +
						T.labarik + ': <b>' + fmt(m.labarik) + '</b> · ' + T.uma_kain + ': <b>' + fmt(m.uma_kain) + '</b>' +
						'<br><span style="color:' + K.muted + ';font-size:11px">' + T.klik + '</span>';
				}
			},
			plotOptions: { bar: { stacking: 'normal', borderWidth: 2, borderColor: K.surface } },
			series: [
				{ name: T.mane, color: K.mane, data: lista.map(function (m) { return { y: m.mane, code: m.code }; }) },
				{ name: T.feto, color: K.feto, data: lista.map(function (m) { return { y: m.feto, code: m.code }; }) }
			].map(function (s) { s.point = { events: { click: function () { hili('munisipiu', this.code); } } }; return s; })
		});
	}

	// Painel mapa: kazu tuir suku (bainhira hili munisípiu)
	function grafikuSuku(d) {
		var mun = d.munisipiu.filter(function (m) { return m.code === F.munisipiu; })[0];
		$('painel-titulu').textContent = mun ? mun.name : T.timor;
		if (!mun) {
			$('painel-sub').textContent = T.suku_hili;
			if (charts['chart-suku']) { charts['chart-suku'].destroy(); delete charts['chart-suku']; }
			$('chart-suku').textContent = '';
			return;
		}
		$('painel-sub').textContent = mun.label + ' ' + T.kazu + ' · ' + T.suku;
		var el = $('chart-suku');
		el.style.height = Math.max(160, d.suku.length * 34 + 40) + 'px';
		if (charts['chart-suku']) { charts['chart-suku'].destroy(); delete charts['chart-suku']; }
		if (!d.suku.length) { el.textContent = T.la_iha; return; }
		charts['chart-suku'] = Highcharts.chart('chart-suku', {
			chart: { type: 'bar' },
			exporting: { enabled: false },
			xAxis: { categories: d.suku.map(function (s) { return s.name; }) },
			yAxis: { visible: false },
			tooltip: { formatter: tooltipKazu },
			plotOptions: { series: { cursor: 'default' } },
			series: [{ name: T.kazu, data: d.suku.map(function (s) { return pontu(s, s.name); }), dataLabels: barLabels() }]
		});
	}

	// ── Mapa: baze (Street / Mapbox / Satélite) + Hotspot (total kada munisípiu) + kór munisípiu ──
	// Portal hatudu dadus agregadu deit — la iha pontu kazu ida-idak (privasidade).
	var mapa = L.map('p-mapa', { zoomControl: true, scrollWheelZoom: false, attributionControl: true }).setView([-8.85, 125.8], 8);
	var baze = {};
	baze[T.street] = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap' });
	if (CFG.mapbox) {
		// Token Mapbox husi .env (MAPBOX_TOKEN) — la hakerek iha kódigu
		var mapbox = function (estilu) {
			return L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/' + estilu + '/tiles/{z}/{x}/{y}?access_token=' + encodeURIComponent(CFG.mapbox), {
				maxZoom: 18, tileSize: 512, zoomOffset: -1,
				attribution: '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; OpenStreetMap'
			});
		};
		baze['Mapbox'] = mapbox('streets-v12');
		baze[T.satelite] = mapbox('satellite-streets-v12');
	} else {
		baze[T.satelite] = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Tiles &copy; Esri' });
	}
	if (navigator.onLine) baze[CFG.mapbox ? 'Mapbox' : T.street].addTo(mapa);
	var fronteira = null;
	var hotspot = L.layerGroup().addTo(mapa);

	function kor(m) {
		if (!m) return BIN[BIN.length - 1][1];
		var n = m.n == null ? 1 : m.n;
		for (var i = 0; i < BIN.length; i++) { if (n >= BIN[i][0] && (BIN[i][0] > 0 || n === 0)) return BIN[i][1]; }
		return BIN[BIN.length - 1][1];
	}

	function munDadus(code) {
		return DADUS ? DADUS.munisipiu.filter(function (m) { return m.code === code; })[0] : null;
	}

	// Hotspot: círculo ho total kada munisípiu. Klik → filtru munisípiu (zoom + kazu tuir suku).
	function hotspotDesenha() {
		hotspot.clearLayers();
		if (!fronteira || !DADUS) return;
		fronteira.eachLayer(function (l) {
			var f = l.feature.properties, m = munDadus(f.code);
			if (!m || m.n === 0) return;
			var n = m.n == null ? 1 : m.n;                    // "< 3": kí'ik liu
			var raiu = 14 + Math.sqrt(n) * 5;
			var sentru = l.getBounds().getCenter();
			var hiliAtu = F.munisipiu === f.code;
			var c = L.circleMarker(sentru, { radius: raiu, color: hiliAtu ? K.ink : '#ffffff', weight: hiliAtu ? 3 : 2,
				fillColor: kor(m), fillOpacity: 0.92 }).addTo(hotspot);
			var naroman = n < 5;                              // kór naroman → letra metin (kontraste)
			var lbl = L.marker(sentru, { icon: L.divIcon({ className: 'p-hot-label' + (naroman ? ' p-hot-escuro' : ''), html: esc(m.label), iconSize: [44, 18] }), keyboard: false }).addTo(hotspot);
			[c, lbl].forEach(function (x) {
				x.bindTooltip('<b>' + esc(f.name) + '</b><br>' + esc(m.label) + ' ' + esc(T.kazu) + '<br><small>' + esc(T.klik_hotspot) + '</small>', { direction: 'top' });
				x.on('click', function () { hili('munisipiu', f.code); });
			});
		});
	}

	function mapaEstilu() {
		if (!fronteira) return;
		fronteira.setStyle(function (f) {
			var hili = F.munisipiu === f.properties.code;
			return { color: hili ? '#0b0b0b' : '#ffffff', weight: hili ? 3 : 1.2, fillColor: kor(munDadus(f.properties.code)), fillOpacity: navigator.onLine ? 0.78 : 0.95 };
		});
		if (F.munisipiu) {
			fronteira.eachLayer(function (l) { if (l.feature.properties.code === F.munisipiu) { l.bringToFront(); mapa.fitBounds(l.getBounds(), { padding: [30, 30], maxZoom: 10 }); } });
		} else {
			mapa.fitBounds(fronteira.getBounds(), { padding: [10, 10] });
		}
		hotspotDesenha();                                 // ikus: círculo iha leten munisípiu hili
	}

	fetch(CFG.geojson).then(function (r) { return r.json(); }).then(function (geo) {
		fronteira = L.geoJSON(geo, {
			onEachFeature: function (f, layer) {
				layer.bindTooltip(function () {
					var m = munDadus(f.properties.code);
					var div = document.createElement('div');
					var b = document.createElement('b'); b.textContent = f.properties.name; div.appendChild(b);
					div.appendChild(document.createElement('br'));
					div.appendChild(document.createTextNode((m ? m.label : '0') + ' ' + T.kazu));
					return div;
				}, { sticky: true });
				layer.on('click', function () { hili('munisipiu', f.properties.code); });
				layer.on('mouseover', function () { layer.setStyle({ weight: 3, color: '#0b0b0b' }); });
				layer.on('mouseout', function () { mapaEstilu(); });
			}
		}).addTo(mapa);
		mapa.removeLayer(hotspot); hotspot.addTo(mapa);    // hotspot iha leten fronteira (klik)
		var overlay = {};
		overlay[T.hotspot] = hotspot;
		overlay[T.kor_munisipiu] = fronteira;
		L.control.layers(baze, overlay, { collapsed: window.innerWidth < 768 }).addTo(mapa);
		mapaEstilu();
	});

	// Lejenda mapa (iha painel)
	(function () {
		var box = $('legend-mapa');
		var t = document.createElement('b'); t.textContent = T.legenda; box.appendChild(t);
		var etiketa = ['20+', '10–19', '5–9', '1–4', '0'];
		BIN.forEach(function (b, i) {
			var row = document.createElement('div');
			var sw = document.createElement('i'); sw.style.background = b[1]; row.appendChild(sw);
			row.appendChild(document.createTextNode(etiketa[i]));
			box.appendChild(row);
		});
	})();

	leeURL();
	sinkronizaSelect();
	karrega();
})();
