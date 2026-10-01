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

	// ── Modal konfirmasaun (Bootstrap) ──
	// konfirma({titulu, mensajen, kor, ikon, label, presizaNota}, okCallback(nota))
	var modal = document.getElementById('modal-konfirma');
	function konfirma(opt, ok) {
		if (!modal || !window.jQuery) {                      // fallback: browser la iha modal
			var nota = opt.presizaNota ? window.prompt(opt.mensajen) : '';
			if (opt.presizaNota ? (nota && nota.trim().length >= 5) : window.confirm(opt.mensajen)) ok(nota || '');
			return;
		}
		var kor = opt.kor || 'rbr';
		var btnOk = modal.querySelector('.mk-ok');
		var boxNota = modal.querySelector('.mk-nota');
		var inpNota = modal.querySelector('#mk-nota-input');
		modal.querySelector('.mk-ikon').className = 'mk-ikon mk-' + kor;
		modal.querySelector('.mk-ikon i').className = 'fa ' + (opt.ikon || 'fa-question');
		modal.querySelector('.modal-title').textContent = opt.titulu || modal.dataset.titulu;
		modal.querySelector('.mk-mensajen').textContent = opt.mensajen || '';
		btnOk.className = 'btn px-4 mk-ok btn-' + kor;
		btnOk.querySelector('i').className = 'fa ' + (opt.ikon || 'fa-check');
		btnOk.querySelector('span').textContent = opt.label || 'OK';
		btnOk.disabled = false;
		boxNota.hidden = !opt.presizaNota;
		inpNota.value = '';
		inpNota.classList.remove('is-invalid');

		btnOk.onclick = function () {
			var nota = inpNota.value.trim();
			if (opt.presizaNota && nota.length < 5) {
				inpNota.classList.add('is-invalid');
				modal.querySelector('.invalid-feedback').textContent = modal.dataset.notaErru;
				inpNota.focus();
				return;
			}
			btnOk.disabled = true;                           // evita klik dala rua
			ok(nota);
		};
		jQuery(modal).off('shown.bs.modal').on('shown.bs.modal', function () {
			(opt.presizaNota ? inpNota : btnOk).focus();
		}).modal('show');
	}
	window.konfirma = konfirma;

	// Aksaun importante seluk (form.js-confirm data-confirm="…")
	document.querySelectorAll('form.js-confirm').forEach(function (f) {
		f.addEventListener('submit', function (e) {
			if (f.dataset.konfirmadu) return;
			e.preventDefault();
			var btn = f.querySelector('[type=submit]');
			var perigu = btn && /danger/.test(btn.className);
			konfirma({
				mensajen: f.dataset.confirm, kor: perigu ? 'danger' : 'rbr',
				ikon: perigu ? 'fa-exclamation' : 'fa-question', label: btn ? btn.textContent.trim() : 'OK'
			}, function () { f.dataset.konfirmadu = '1'; f.submit(); });
		});
	});

	// Butaun aksaun kazu (Verifika / Aprova / Remata / Rejeita / Kansela)
	document.querySelectorAll('form.js-action').forEach(function (f) {
		f.querySelectorAll('button[data-action]').forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				e.preventDefault();
				var d = btn.dataset;
				konfirma({
					titulu: d.titulu, mensajen: d.mensajen, kor: d.kor, ikon: d.ikon,
					label: btn.textContent.trim(), presizaNota: !!d.needNota
				}, function (nota) {
					f.querySelector('input[name=nota]').value = nota;
					f.action = btn.getAttribute('formaction');
					f.submit();
				});
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
