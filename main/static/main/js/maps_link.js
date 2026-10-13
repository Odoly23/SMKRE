/* Lee koordenada husi link Google Maps (pindrop) ka testu "-8.55, 125.57".
   Formatu: .../!3d-8.55!4d125.57 · ?q=-8.55,125.57 · ll= · query= · /@-8.55,125.57,17z
   Link badak (maps.app.goo.gl) la bele lee iha browser: loke link no kopia link naruk. */
var SMKREMapsLink = (function () {
	'use strict';
	var TL = { lat: [-9.6, -8.1], lng: [124.0, 127.4] };
	var padraun = [
		/!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/,                       // pin (place)
		/[?&](?:q|ll|query|destination)=(-?\d+(?:\.\d+)?)(?:,|%2C)\s*(-?\d+(?:\.\d+)?)/i,
		/@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/,                            // sentru mapa
		/^\s*(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)\s*$/               // testu koordenada
	];
	function lee(testu) {
		testu = (testu || '').trim();
		if (!testu) return { erru: '' };
		if (/goo\.gl|maps\.app/i.test(testu)) return { erru: 'badak' };
		for (var i = 0; i < padraun.length; i++) {
			var m = testu.match(padraun[i]);
			if (m) {
				var lat = parseFloat(m[1]), lng = parseFloat(m[2]);
				if (lat >= TL.lat[0] && lat <= TL.lat[1] && lng >= TL.lng[0] && lng <= TL.lng[1]) {
					return { lat: +lat.toFixed(6), lng: +lng.toFixed(6) };
				}
				return { erru: 'liur' };
			}
		}
		return { erru: 'la_hetan' };
	}
	return { lee: lee };
})();
