/* SIBAR-RbR Poligon — kalkula luan / keliling / naruk / lebar ho Turf.js (lokál, servisu offline).
   Uza iha detalla kazu (Leaflet-Geoman) no app offline (la'o haleu rai ho GPS).
   Server kalkula fali ho rumus hanesan (kazu/poligon.py) molok rai. */
var SIBARPoligon = (function () {
	'use strict';
	var M2_HA = 10000;

	function fc(features) { return turf.featureCollection(features || []); }

	// Retángulu minimu rotadu (metru lokál) → naruk (sisi boot) no lebar (sisi kiik)
	function naruk_lebar(poly) {
		var c = turf.centroid(poly).geometry.coordinates;
		var kx = Math.PI / 180 * 6371008.8 * Math.cos(c[1] * Math.PI / 180), ky = Math.PI / 180 * 6371008.8;
		var hull = turf.convex(turf.explode(poly)) || poly;
		var pts = hull.geometry.coordinates[0].map(function (p) { return [(p[0] - c[0]) * kx, (p[1] - c[1]) * ky]; });
		var diak = null;
		for (var i = 0; i < pts.length - 1; i++) {
			var dx = pts[i + 1][0] - pts[i][0], dy = pts[i + 1][1] - pts[i][1], len = Math.hypot(dx, dy);
			if (!len) continue;
			var ux = dx / len, uy = dy / len, minA = Infinity, maxA = -Infinity, minB = Infinity, maxB = -Infinity;
			pts.forEach(function (p) {
				var a = p[0] * ux + p[1] * uy, b = -p[0] * uy + p[1] * ux;
				minA = Math.min(minA, a); maxA = Math.max(maxA, a); minB = Math.min(minB, b); maxB = Math.max(maxB, b);
			});
			var w = maxA - minA, h = maxB - minB;
			if (!diak || w * h < diak.area) diak = { area: w * h, naruk: Math.max(w, h), lebar: Math.min(w, h) };
		}
		return diak || { naruk: 0, lebar: 0 };
	}

	function metrika(poly) {
		var nl = naruk_lebar(poly);
		return {
			luan_m2: turf.area(poly),
			keliling_m: turf.length(turf.polygonToLine(poly), { units: 'meters' }),
			naruk_m: nl.naruk, lebar_m: nl.lebar
		};
	}

	// Bidang hotu → metrika kada bidang + luan total (union: sobrepoin la konta dala rua)
	function kalkula(features) {
		var bidang = features.map(function (f) { return metrika(f); });
		var total = 0;
		if (features.length === 1) total = bidang[0].luan_m2;
		else if (features.length > 1) {
			try { total = turf.area(turf.union(fc(features))); }
			catch (e) { total = bidang.reduce(function (s, b) { return s + b.luan_m2; }, 0); }
		}
		return { bidang: bidang, luan_m2: total, keliling_m: bidang.reduce(function (s, b) { return s + b.keliling_m; }, 0) };
	}

	// Liña kruza malu (poligon la validu)?
	function kruza(poly) {
		try { return turf.kinks(poly).features.length > 0; } catch (e) { return false; }
	}

	function num(v, d) { return v.toLocaleString('pt-PT', { minimumFractionDigits: d, maximumFractionDigits: d }); }
	function luan(m2) { return num(m2, m2 < 100 ? 1 : 0) + ' m² · ' + num(m2 / M2_HA, m2 < M2_HA ? 4 : 2) + ' ha'; }
	function metru(m) { return m >= 1000 ? num(m / 1000, 2) + ' km' : num(m, 1) + ' m'; }

	return { kalkula: kalkula, metrika: metrika, kruza: kruza, luan: luan, metru: metru, fc: fc };
})();
