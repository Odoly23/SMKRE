/* SIBAR-RbR — main.js (la iha inline script: seguru ho CSP) */
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

	// ── Konfirmasaun ho modal Bootstrap (form.js-confirm data-confirm="…") ──
	// Aksaun kazu (Verifika / Aprova / …) la uza ida-ne'e: sira iha modal rasik iha kazu/detail.html.
	var modal = document.getElementById('modal-konfirma');
	document.querySelectorAll('form.js-confirm').forEach(function (f) {
		f.addEventListener('submit', function (e) {
			if (f.dataset.konfirmadu || !modal || !window.jQuery) return;
			e.preventDefault();
			var btn = f.querySelector('[type=submit]');
			var ok = modal.querySelector('.mk-ok');
			modal.querySelector('.modal-body').textContent = f.dataset.confirm || '';
			ok.textContent = btn ? btn.textContent.trim() : 'OK';
			ok.className = 'btn mk-ok ' + (btn && /danger/.test(btn.className) ? 'btn-danger' : 'btn-rbr');
			ok.onclick = function () {
				ok.disabled = true;                              // evita klik dala rua
				f.dataset.konfirmadu = '1';
				f.submit();
			};
			ok.disabled = false;
			jQuery(modal).modal('show');
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

	// ── Data: hatudu sempre dd/mm/yyyy (formatu Timor-Leste), maske browser iha lian seluk (mm/dd/yyyy) ──
	// Input orijinál (type=date, valor ISO) hela iha formuláriu ba server no script seluk; ema hakerek / hili iha testu dd/mm/yyyy.
	function iso2dmy(v) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || ''); return m ? m[3] + '/' + m[2] + '/' + m[1] : ''; }
	function dmy2iso(v) {
		var m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec((v || '').trim());
		if (!m) return null;
		var d = new Date(+m[3], +m[2] - 1, +m[1]);
		if (d.getFullYear() !== +m[3] || d.getMonth() !== +m[2] - 1 || d.getDate() !== +m[1]) return null;
		return m[3] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
	}
	window.SIBARData = function (root) {
		(root || document).querySelectorAll('input[type="date"]:not([data-tl-data])').forEach(function (orig) {
			orig.setAttribute('data-tl-data', '1');
			var grp = document.createElement('div');
			grp.className = 'input-group tl-data';
			var txt = document.createElement('input');
			txt.type = 'text';
			txt.className = orig.className.replace('dateinput', '').trim() || 'form-control';
			txt.placeholder = 'dd/mm/yyyy';
			txt.inputMode = 'numeric';
			txt.maxLength = 10;
			txt.autocomplete = 'off';
			if (orig.id) {
				txt.id = orig.id + '_tl';
				var lbl = document.querySelector('label[for="' + orig.id + '"]');
				if (lbl) lbl.htmlFor = txt.id;
			}
			var ap = document.createElement('div');
			ap.className = 'input-group-append position-relative';
			ap.innerHTML = '<button type="button" class="btn btn-outline-secondary" tabindex="-1" aria-label="Kalendáriu"><i class="fa fa-calendar"></i></button>';
			var btn = ap.firstChild;
			orig.parentNode.insertBefore(grp, orig);
			grp.appendChild(txt);
			grp.appendChild(ap);
			ap.appendChild(orig);
			// Input orijinál subar iha butaun okos (kalendáriu browser)
			orig.style.cssText = 'position:absolute;left:0;bottom:0;width:100%;height:1px;opacity:0;pointer-events:none;border:0;padding:0';
			orig.tabIndex = -1;
			function hatudu() {
				txt.value = iso2dmy(orig.value);
				txt.readOnly = orig.readOnly; txt.disabled = btn.disabled = orig.disabled || orig.readOnly;
				txt.classList.toggle('is-invalid', orig.classList.contains('is-invalid'));
			}
			btn.addEventListener('click', function () {
				try { orig.showPicker(); } catch (e) { orig.focus(); orig.click(); }
			});
			orig.addEventListener('change', hatudu);
			txt.addEventListener('input', function () {
				// Hatama "/" automátiku: 26102026 → 26/10/2026
				var n = txt.value.replace(/[^0-9]/g, '').slice(0, 8);
				if (/^[0-9/]*$/.test(txt.value) && txt.value.indexOf('/') < 0 && n.length > 2)
					txt.value = n.slice(0, 2) + '/' + n.slice(2, 4) + (n.length > 4 ? '/' + n.slice(4) : '');
			});
			txt.addEventListener('change', function () {
				var v = txt.value.trim(), iso = v ? dmy2iso(v) : '';
				txt.classList.toggle('is-invalid', iso === null);
				if (iso === null) return;
				orig.value = iso;
				orig.dispatchEvent(new Event('change', { bubbles: true }));
				txt.value = iso2dmy(iso);
			});
			// Script seluk muda valor / readonly (ex. Tinan Simu) → atualiza testu
			new MutationObserver(hatudu).observe(orig, { attributes: true, attributeFilter: ['readonly', 'disabled', 'class'] });
			if (orig.classList.contains('is-invalid'))
				grp.parentNode.querySelectorAll('.invalid-feedback').forEach(function (f) { f.classList.add('d-block'); });
			hatudu();
		});
	};
	window.SIBARData();

	// ── Opsaun "Seluk": hili Seluk → kampu esplika mosu (data-seluk-for = naran kampu). Subar = mamuk bainhira haruka ──
	window.SIBARSeluk = function (root) {
		(root || document).querySelectorAll('[data-seluk-for]:not([data-seluk-ok])').forEach(function (box) {
			box.setAttribute('data-seluk-ok', '1');
			var form = box.closest('form') || document, f = box.getAttribute('data-seluk-for');
			var ids = box.hasAttribute('data-seluk-ids') ? box.getAttribute('data-seluk-ids').split(',') : null;
			var ctl = Array.prototype.filter.call(form.querySelectorAll('select, input'), function (el) {
				var n = el.name || '';
				return n === f || n.slice(-(f.length + 1)) === '-' + f;
			});
			function ativu() {
				return ctl.some(function (el) {
					if (el.type === 'checkbox' || el.type === 'radio') return el.checked && (ids ? ids.indexOf(el.value) >= 0 : el.value === 'SELUK');
					return el.value === 'SELUK';
				});
			}
			// Checkbox (ex. estragu): testu tuan iha ona → hatudu nafatin (la lakon dadus)
			var tuan = !!ids && Array.prototype.some.call(box.querySelectorAll('input, textarea'), function (i) { return i.type !== 'hidden' && i.value.trim() !== ''; });
			function atualiza() { box.hidden = !(ativu() || tuan); }
			ctl.forEach(function (el) { el.addEventListener('change', atualiza); });
			atualiza();
			if (form !== document) form.addEventListener('submit', function () {
				if (box.hidden) box.querySelectorAll('input, textarea').forEach(function (i) { if (i.type !== 'hidden') i.value = ''; });
			});
		});
	};
	window.SIBARSeluk();

	// ── Pájina erru: "Fila" = pájina antes (se la iha istória → Varanda) ──
	document.querySelectorAll('.js-koko').forEach(function (b) { b.addEventListener('click', function () { location.reload(); }); });
	document.querySelectorAll('.js-fila').forEach(function (a) {
		a.addEventListener('click', function (e) {
			if (window.history.length > 1 && document.referrer && document.referrer.indexOf(location.origin) === 0) { e.preventDefault(); history.back(); }
		});
	});

	// ── Butaun "Kopia" (input readonly) ──
	document.querySelectorAll('.js-kopia').forEach(function (b) {
		b.addEventListener('click', function () {
			var inp = document.getElementById(b.dataset.target);
			inp.select();
			(navigator.clipboard ? navigator.clipboard.writeText(inp.value) : Promise.reject()).catch(function () { document.execCommand('copy'); });
			b.innerHTML = '<i class="fa fa-check"></i>';
		});
	});

	// ── PWA: registu service worker ──
	if ('serviceWorker' in navigator && document.body.dataset.sw) {
		window.addEventListener('load', function () {
			navigator.serviceWorker.register(document.body.dataset.sw, { scope: '/' }).catch(function () {});
		});
	}
})();
