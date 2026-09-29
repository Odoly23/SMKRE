/* SMKRE — main.js (la iha inline script: seguru ho CSP) */
(function () {
	'use strict';

	// ── Sidebar HP: hamburger loke / taka ──
	var ham = document.getElementById('btn-ham');
	var sidebar = document.getElementById('sidebar');
	var overlay = document.getElementById('overlay');
	function setSidebar(open) {
		if (!sidebar) return;
		sidebar.classList.toggle('active', open);
		if (overlay) overlay.classList.toggle('active', open);
		sidebar.setAttribute('aria-hidden', open ? 'false' : 'true');
		if (ham) ham.setAttribute('aria-expanded', open ? 'true' : 'false');
	}
	if (ham) ham.addEventListener('click', function () { setSidebar(!sidebar.classList.contains('active')); });
	if (overlay) overlay.addEventListener('click', function () { setSidebar(false); });
	document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setSidebar(false); });

	// ── Navbar: menu ne'ebé la kabe muda ba "Seluk" (la iha tabrakan ho logo / notifikasaun) ──
	var navLinks = document.querySelector('.nav-links');
	var navMore = document.getElementById('nav-more');
	var navMenu = document.getElementById('nav-more-menu');
	function fitNav() {
		if (!navLinks || !navMore) return;
		var items = Array.prototype.slice.call(navLinks.children);
		items.forEach(function (li) { li.hidden = false; });
		navMenu.textContent = '';
		navMore.hidden = true;
		navMore.classList.remove('active');
		if (window.innerWidth < 992) return;                       // HP: hamburger + sidebar
		var sobra = function () { return navLinks.scrollWidth > navLinks.clientWidth + 1; };
		if (!sobra()) return;
		navMore.hidden = false;                                    // "Seluk" okupa fatin → sukat fali
		// Muda husi ikus ba oin; pájina ativa hela iha liña (se bele)
		var lista = items.slice().reverse();
		var kandidatu = lista.filter(function (li) { return !li.classList.contains('active'); }).concat(lista.filter(function (li) { return li.classList.contains('active'); }));
		var subar = [];
		for (var i = 0; i < kandidatu.length && sobra(); i++) {
			kandidatu[i].hidden = true;
			subar.push(kandidatu[i]);
		}
		items.forEach(function (li) {
			if (subar.indexOf(li) < 0) return;
			var a = li.querySelector('a').cloneNode(true);
			a.className = 'dropdown-item' + (li.classList.contains('active') ? ' active' : '');
			navMenu.appendChild(a);
			if (li.classList.contains('active')) navMore.classList.add('active');
		});
	}
	var navTimer = null;
	window.addEventListener('resize', function () { clearTimeout(navTimer); navTimer = setTimeout(fitNav, 120); });
	fitNav();
	if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitNav);     // font Lato karrega → sukat fali

	// ── Status koneksaun: Online / Offline ──
	var net = document.getElementById('net-status');
	function updateNet() {
		if (!net) return;
		var on = navigator.onLine;
		net.classList.toggle('online', on);
		net.classList.toggle('offline', !on);
		net.querySelector('span').textContent = on ? net.dataset.on : net.dataset.off;
	}
	window.addEventListener('online', updateNet);
	window.addEventListener('offline', updateNet);
	updateNet();

	// ── Konfirmasaun antes aksaun importante (form.js-confirm) ──
	document.querySelectorAll('form.js-confirm').forEach(function (f) {
		f.addEventListener('submit', function (e) {
			if (!window.confirm(f.dataset.confirm || 'Ita-boot iha serteza?')) e.preventDefault();
		});
	});

	// ── Butaun aksaun kazu (Verifika / Aprova / Rejeita / Kansela): konfirma + razaun ──
	document.querySelectorAll('form.js-action').forEach(function (f) {
		f.querySelectorAll('button[data-action]').forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				var nota = f.querySelector('textarea[name=nota]');
				if (btn.dataset.needNota && (!nota || nota.value.trim().length < 5)) {
					e.preventDefault();
					window.alert(f.dataset.needNota);
					if (nota) nota.focus();
					return;
				}
				if (!window.confirm(f.dataset['confirm' + btn.dataset.action.charAt(0).toUpperCase() + btn.dataset.action.slice(1)] || '?')) e.preventDefault();
			});
		});
	});

	// ── Filtru tabela simples (input.js-filter data-target="#tbl") ──
	document.querySelectorAll('.js-filter').forEach(function (inp) {
		var table = document.querySelector(inp.dataset.target);
		if (!table) return;
		inp.addEventListener('input', function () {
			var q = inp.value.toLowerCase();
			table.querySelectorAll('tbody tr').forEach(function (tr) {
				tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
			});
		});
	});

	// ── Input file (crispy bootstrap4): hatudu naran file ──
	document.querySelectorAll('.custom-file-input').forEach(function (inp) {
		inp.addEventListener('change', function (e) {
			var names = Array.prototype.map.call(e.target.files, function (f) { return f.name; }).join(', ');
			var label = inp.parentNode.querySelector('.custom-file-label');
			if (label) label.textContent = names || '---';
		});
	});

	// ── PWA: registu service worker ──
	if ('serviceWorker' in navigator && document.body.dataset.sw) {
		window.addEventListener('load', function () {
			navigator.serviceWorker.register(document.body.dataset.sw, { scope: '/' }).catch(function () {});
		});
	}
})();
