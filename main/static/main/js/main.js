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
