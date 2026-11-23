/* SIBAR-RbR — Sekretariadu (online): hili fatin kazu iha mapa duké GPS automátiku.
   Klik mapa ka dada marka → #id_latitude / #id_longitude; akurasia mamuk (la'ós GPS HP).
   Hili munisípiu → mapa ba munisípiu ne'e. Konfigurasaun: #gps-mapa-cfg + json #mun-pontu. */
(function () {
	'use strict';
	var cfg = document.getElementById('gps-mapa-cfg'), box = document.querySelector('.gps-box');
	if (!cfg || !box || !window.L) return;
	var lat = document.getElementById('id_latitude'), lng = document.getElementById('id_longitude'),
		akur = document.getElementById('id_gps_akurasia'), msg = document.getElementById('gps-msg'),
		btn = document.getElementById('btn-gps'), mun = document.getElementById('id_munisipiu');
	var pontu = {};
	try { pontu = JSON.parse(document.getElementById('mun-pontu').textContent) || {}; } catch (e) { pontu = {}; }
	if (btn) btn.hidden = true;                                 // la iha GPS automátiku online
	if (msg) msg.textContent = cfg.dataset.lHili;

	var div = document.createElement('div');
	div.id = 'gps-mapa';
	div.className = 'gps-mapa mt-2';
	div.dataset.lFullscreen = cfg.dataset.lFullscreen;
	box.appendChild(div);

	var baze = SMKREMapa.baze(cfg.dataset.mapbox || '');
	var map = L.map(div, { layers: [baze['Street']], zoomControl: true }).setView([-8.80, 125.90], 8);
	L.control.layers(baze, null, { position: 'topright' }).addTo(map);
	SMKREMapa.fullscreen(map);
	var marka = null;

	function rai(ll) {
		lat.value = ll.lat.toFixed(6);
		lng.value = ll.lng.toFixed(6);
		if (akur) akur.value = '';                              // hili iha mapa: la iha akurasia GPS
		if (msg) { msg.classList.add('text-rbr'); msg.textContent = cfg.dataset.lOk + ' (' + lat.value + ', ' + lng.value + ')'; }
	}
	function tau(ll, zoom) {
		if (!marka) {
			marka = L.marker(ll, { draggable: true }).addTo(map);
			marka.on('dragend', function () { rai(marka.getLatLng()); });
		} else marka.setLatLng(ll);
		if (zoom) map.setView(ll, zoom);
	}
	map.on('click', function (e) { tau(e.latlng); rai(e.latlng); });

	if (lat.value && lng.value) tau(L.latLng(+lat.value, +lng.value), 15);   // edita: fatin uluk
	else if (mun && pontu[mun.value]) map.setView(pontu[mun.value], 11);
	if (mun) mun.addEventListener('change', function () {
		if (pontu[mun.value] && !marka) map.setView(pontu[mun.value], 11);
		else if (pontu[mun.value]) map.panTo(pontu[mun.value]);
	});
	setTimeout(function () { map.invalidateSize(); }, 300);
})();
