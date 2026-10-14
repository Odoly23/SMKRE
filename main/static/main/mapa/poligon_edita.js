/* SIBAR-RbR — Poligon rai iha detalla kazu.
   Haree: bidang hotu + luan/keliling/naruk/lebar (Turf.js). Edita (Leaflet-Geoman): kria, dada pontu, hamoos.
   Rai: POST GeoJSON → server valida no kalkula fali (kazu/poligon.py). */
(function () {
	'use strict';
	var el = document.getElementById('mapa-poligon');
	if (!el) return;
	var D = el.dataset, edita = !!D.edita, P = SIBARPoligon;
	var $ = function (id) { return document.getElementById(id); };
	var dadus = JSON.parse($('poligon-dadus').textContent || 'null');

	var baze = SMKREMapa.baze(D.mapbox);
	var lat = parseFloat(D.lat), lng = parseFloat(D.lng), iha = !isNaN(lat) && !isNaN(lng);
	var map = L.map(el, { center: iha ? [lat, lng] : [-8.75, 125.9], zoom: iha ? 17 : 9, maxZoom: 20,
		layers: [navigator.onLine ? baze['Satélite'] : L.layerGroup()] });
	L.control.layers(baze, {}, { collapsed: true }).addTo(map);
	L.control.scale({ imperial: false }).addTo(map);
	SMKREMapa.fullscreen(map);
	SMKREMapa.lokasaun(map);
	SMKREMapa.koordenada(map);
	if (iha) L.marker([lat, lng], { icon: L.icon({ iconUrl: D.ikon, shadowUrl: D.sombra, iconSize: [25, 41], iconAnchor: [12, 41], shadowSize: [41, 41] }), interactive: false }).addTo(map);

	var grupu = L.featureGroup().addTo(map);
	var ESTILU = { color: '#0E8A68', weight: 3, fillColor: '#16B78A', fillOpacity: 0.25 };

	function aumenta(feature) {
		L.geoJSON(feature, { style: ESTILU }).eachLayer(function (l) { liga(l); grupu.addLayer(l); });
	}
	function karga(fc) {
		grupu.clearLayers();
		((fc && fc.features) || []).forEach(aumenta);
		if (grupu.getLayers().length) map.fitBounds(grupu.getBounds(), { padding: [30, 30], maxZoom: 19 });
		atualiza(false);
	}

	// Bidang hotu → GeoJSON (anel taka) · la konta layer ne'ebé Geoman hasai
	function features() {
		return grupu.getLayers().filter(function (l) { return l.toGeoJSON; }).map(function (l) {
			var f = l.toGeoJSON(); f.properties = {}; return f;
		}).filter(function (f) { return f.geometry && f.geometry.type === 'Polygon'; });
	}

	function atualiza(muda) {
		var fs = features(), r = P.kalkula(fs), tb = $('poligon-tabela').tBodies[0], kruza = false;
		tb.innerHTML = '';
		grupu.getLayers().forEach(function (l, i) {
			var f = fs[i], m = r.bidang[i];
			if (!f || !m) return;
			var k = P.kruza(f); kruza = kruza || k;
			l.setStyle(k ? { color: '#d63c3c', fillColor: '#d63c3c' } : ESTILU);
			l.unbindTooltip().bindTooltip(D.lBidang + ' ' + (i + 1) + ': ' + P.luan(m.luan_m2), { permanent: true, direction: 'center', className: 'poligon-label' });
			var tr = tb.insertRow();
			tr.innerHTML = '<td>' + (i + 1) + (k ? ' <i class="fa fa-exclamation-triangle text-danger" title="' + D.lKruza + '"></i>' : '') + '</td><td>' + P.luan(m.luan_m2) +
				'</td><td>' + P.metru(m.keliling_m) + '</td><td>' + P.metru(m.naruk_m) + ' × ' + P.metru(m.lebar_m) + '</td>';
		});
		$('poligon-total').textContent = fs.length ? P.luan(r.luan_m2) : '—';
		$('poligon-keliling').textContent = fs.length ? P.metru(r.keliling_m) : '—';
		$('poligon-mamuk').hidden = fs.length > 0;
		$('poligon-tabela').hidden = !fs.length;
		if (edita) {
			$('poligon-rai').disabled = !muda || kruza;
			$('poligon-kansela').disabled = !muda;
			status(kruza ? D.lKruza : '', kruza ? 'text-danger' : '');
		}
	}
	function status(t, kls) { var s = $('poligon-status'); s.className = 'small mb-1 ' + (kls || 'text-muted'); s.textContent = t; }

	function liga(l) {
		if (!edita) return;
		l.on('pm:edit pm:markerdrag pm:vertexadded pm:vertexremoved pm:dragend', function () { atualiza(true); });
	}

	if (edita) {
		var lian = (D.lian || 'pt').slice(0, 2);
		map.pm.setLang(lian === 'te' ? 'pt' : lian);
		map.pm.addControls({ position: 'topleft', drawMarker: false, drawCircleMarker: false, drawPolyline: false, drawRectangle: true,
			drawCircle: false, drawText: false, cutPolygon: false, rotateMode: false, drawPolygon: true, editMode: true, dragMode: true, removalMode: true });
		map.pm.setGlobalOptions({ allowSelfIntersection: false, snappable: true, snapDistance: 15, pathOptions: ESTILU, layerGroup: grupu });
		map.on('pm:create', function (e) { e.layer.setStyle(ESTILU); liga(e.layer); if (!grupu.hasLayer(e.layer)) grupu.addLayer(e.layer); atualiza(true); });
		map.on('pm:remove', function (e) { grupu.removeLayer(e.layer); atualiza(true); });

		$('poligon-kansela').addEventListener('click', function () { map.pm.disableGlobalEditMode(); karga(dadus); status(''); });
		$('poligon-rai').addEventListener('click', function () {
			var fs = features(), btn = this;
			if (!fs.length && !window.confirm(D.lHamoos)) return;
			btn.disabled = true;
			fetch(D.url, {
				method: 'POST', credentials: 'same-origin',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': D.csrf },
				body: JSON.stringify({ poligon: fs.length ? P.fc(fs) : null })
			}).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); }).then(function (r) {
				if (!r.ok) { status(r.j.erru || D.lErru, 'text-danger'); btn.disabled = false; return; }
				map.pm.disableGlobalEditMode();
				dadus = r.j.poligon; karga(dadus);
				var rl = $('detalla-rai-luan');
				if (rl && r.j.rai_luan) rl.firstChild.textContent = r.j.rai_luan + ' ' + r.j.rai_luan_unidade + ' ';
				status(D.lRaiOna + (r.j.luan_m2 ? ' ' + P.luan(parseFloat(r.j.luan_m2)) : ''), 'text-success');
			}).catch(function () { status(D.lErru, 'text-danger'); btn.disabled = false; });
		});
	}
	karga(dadus);
})();
