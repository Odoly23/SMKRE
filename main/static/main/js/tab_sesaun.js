/* SIBAR-RbR — tab ida-idak tenke login: ID tab iha sessionStorage (la fahe ho tab foun / link kopia).
   Meta <meta name="sibar-tab" content="id1,id2" data-login="/Tama-Lai/"> husi servidor (ID tab válidu iha sesaun).
   Hafoin login: URL ho ?_tab=<id> → rai iha tab ne'e, hamoos husi URL. ID la iha / la válidu → pájina login (tab). */
(function () {
	'use strict';
	var m = document.querySelector('meta[name="sibar-tab"]');
	if (!m) return;
	var ids = (m.getAttribute('content') || '').split(',').filter(Boolean);
	var u = new URL(window.location.href);
	if (u.pathname === m.getAttribute('data-login')) return;       // pájina login rasik: la verifika (evita loop)
	var t = u.searchParams.get('_tab');
	var s = null;
	try {
		if (t) {
			sessionStorage.setItem('sibar_tab', t);
			u.searchParams.delete('_tab');
			history.replaceState(null, '', u.pathname + u.search + u.hash);
		}
		s = sessionStorage.getItem('sibar_tab');
	} catch (e) { return; }                 // browser blokeia sessionStorage: la bloka servisu
	if (!s || ids.indexOf(s) < 0) {
		document.documentElement.style.visibility = 'hidden';
		window.location.replace(m.getAttribute('data-login') + '?tab=1&next=' + encodeURIComponent(u.pathname + u.search));
	}
})();
