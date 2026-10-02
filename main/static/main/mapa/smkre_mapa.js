/* SMKRE — kontrolu mapa Leaflet (gratis, lokál, la presiza CDN ka API key).
   Uza: SMKREMapa.baze(token) · .fullscreen(map) · .lokasaun(map, onFound) · .koordenada(map) · .sukat(map)
   Testu (lian) husi data-* iha elementu mapa: data-l-fullscreen, data-l-ha-u, data-l-sukat, data-l-hamoos, data-l-gps-erru */
(function () {
	'use strict';

	function lbl(map, k, def) { return (map.getContainer().dataset[k]) || def; }

	function butaun(map, ikone, titulu, onClick, pozisaun) {
		var c = L.control({ position: pozisaun || 'topleft' });
		c.onAdd = function () {
			var a = L.DomUtil.create('a', 'leaflet-bar smkre-map-btn');
			a.href = '#';
			a.title = titulu;
			a.setAttribute('role', 'button');
			a.setAttribute('aria-label', titulu);
			a.innerHTML = '<i class="fa ' + ikone + '"></i>';
			L.DomEvent.on(a, 'click', function (e) { L.DomEvent.preventDefault(e); L.DomEvent.stopPropagation(e); onClick(a); });
			L.DomEvent.disableClickPropagation(a);
			return a;
		};
		return c.addTo(map);
	}

	var SMKREMapa = {
		// Mapa baze: Street (OSM), Satélite (Esri), Mapbox (se iha token iha .env)
		baze: function (token) {
			var b = {
				'Street': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxNativeZoom: 19, maxZoom: 20, attribution: '&copy; OpenStreetMap' }),
				'Satélite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxNativeZoom: 18, maxZoom: 20, attribution: 'Tiles &copy; Esri' })
			};
			if (token) {
				var mb = function (estilu) {
					return L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/' + estilu + '/tiles/{z}/{x}/{y}?access_token=' + encodeURIComponent(token),
						{ tileSize: 512, zoomOffset: -1, maxNativeZoom: 19, maxZoom: 20, attribution: '&copy; Mapbox &copy; OpenStreetMap' });
				};
				b['Mapbox'] = mb('streets-v12');
				b['Satélite'] = mb('satellite-streets-v12');
			}
			return b;
		},

		// Ekran tomak (CSS; la presiza Fullscreen API)
		fullscreen: function (map) {
			var el = map.getContainer();
			return butaun(map, 'fa-expand', lbl(map, 'lFullscreen', 'Ekran tomak'), function (a) {
				var on = !el.classList.contains('smkre-map-full');
				el.classList.toggle('smkre-map-full', on);
				document.body.classList.toggle('smkre-map-full-body', on);
				a.querySelector('i').className = 'fa ' + (on ? 'fa-compress' : 'fa-expand');
				setTimeout(function () { map.invalidateSize(); }, 50);
			});
		},

		// GPS utilizador
		lokasaun: function (map, onFound) {
			var grupu = L.layerGroup().addTo(map);
			map.on('locationfound', function (e) {
				grupu.clearLayers();
				L.circle(e.latlng, { radius: e.accuracy, color: '#1e88e5', weight: 1, fillOpacity: 0.12, interactive: false }).addTo(grupu);
				L.circleMarker(e.latlng, { radius: 7, color: '#fff', weight: 3, fillColor: '#1e88e5', fillOpacity: 1 }).addTo(grupu);
				map.flyTo(e.latlng, Math.max(map.getZoom(), 17));
				if (onFound) onFound(e.latlng, e.accuracy);
			});
			map.on('locationerror', function () { window.alert(lbl(map, 'lGpsErru', 'GPS la hetan')); });
			return butaun(map, 'fa-crosshairs', lbl(map, 'lHaU', "Ha'u-nia fatin"), function () {
				map.locate({ enableHighAccuracy: true, timeout: 15000 });
			});
		},

		// Koordenada kursor (okos-karuk) — klik atu kopia
		koordenada: function (map) {
			var c = L.control({ position: 'bottomleft' });
			c.onAdd = function () {
				var d = L.DomUtil.create('div', 'smkre-map-coord');
				d.textContent = '—';
				map.on('mousemove', function (e) { d.textContent = e.latlng.lat.toFixed(6) + ', ' + e.latlng.lng.toFixed(6); });
				return d;
			};
			return c.addTo(map);
		},

		// Sukat distánsia: klik pontu sira; klik butaun fali atu remata/hamoos
		sukat: function (map) {
			var ativu = false, pontu = [], liña = null, grupu = L.layerGroup().addTo(map);
			function total() {
				var m = 0;
				for (var i = 1; i < pontu.length; i++) m += pontu[i - 1].distanceTo(pontu[i]);
				return m >= 1000 ? (m / 1000).toFixed(2) + ' km' : Math.round(m) + ' m';
			}
			function klik(e) {
				pontu.push(e.latlng);
				L.circleMarker(e.latlng, { radius: 4, color: '#d63c3c', fillOpacity: 1 }).addTo(grupu);
				if (liña) grupu.removeLayer(liña);
				liña = L.polyline(pontu, { color: '#d63c3c', weight: 3, dashArray: '6 6' }).addTo(grupu);
				if (pontu.length > 1) liña.bindTooltip(total(), { permanent: true, direction: 'top', className: 'smkre-map-sukat' }).openTooltip(e.latlng);
			}
			return butaun(map, 'fa-arrows-h', lbl(map, 'lSukat', 'Sukat distánsia'), function (a) {
				ativu = !ativu;
				a.classList.toggle('ativu', ativu);
				map.getContainer().style.cursor = ativu ? 'crosshair' : '';
				if (ativu) { pontu = []; liña = null; grupu.clearLayers(); map.on('click', klik); }
				else { map.off('click', klik); }
				map.fire('smkre:sukat', { ativu: ativu });
			});
		}
	};
	window.SMKREMapa = SMKREMapa;
})();
