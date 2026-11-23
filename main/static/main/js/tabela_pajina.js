/* Paginasaun tabela (client): <table data-pajina="10"> → hatudu liña 10 kada pájina + paginador okos.
   Testu husi data-* (tradus iha template): data-hatudu="Hatudu {a}–{b} husi {t}". tfoot (TOTAL) sempre hatudu. */
(function () {
	'use strict';
	function liga(tbl) {
		var por = parseInt(tbl.getAttribute('data-pajina'), 10) || 10;
		var tbody = tbl.tBodies[0];
		if (!tbody) return;
		var rows = Array.prototype.slice.call(tbody.rows);
		if (rows.length <= por) return;                         // 10 ka menus: la presiza paginador
		var total = rows.length, pajinas = Math.ceil(total / por), atual = 1;
		var bar = document.createElement('div');
		bar.className = 'd-flex justify-content-between align-items-center flex-wrap mt-2 pajina-bar';
		var info = document.createElement('small');
		info.className = 'text-muted mb-1';
		var ul = document.createElement('ul');
		ul.className = 'pagination pagination-sm mb-1';
		var nav = document.createElement('nav');
		nav.setAttribute('aria-label', tbl.getAttribute('data-pajina-label') || 'Pájina');
		nav.appendChild(ul);
		bar.appendChild(info);
		bar.appendChild(nav);
		var wrap = tbl.closest('.table-responsive') || tbl;
		wrap.parentNode.insertBefore(bar, wrap.nextSibling);

		function butaun(txt, alvu, ativu, label) {
			var li = document.createElement('li');
			li.className = 'page-item' + (ativu ? ' active' : '');
			var el = document.createElement(alvu ? 'button' : 'span');
			el.className = 'page-link';
			el.textContent = txt;
			if (label) el.setAttribute('aria-label', label);
			if (alvu) { el.type = 'button'; el.addEventListener('click', function () { hatudu(alvu); }); }
			li.appendChild(el);
			ul.appendChild(li);
		}
		function hatudu(p) {
			atual = Math.min(Math.max(1, p), pajinas);
			var a = (atual - 1) * por, b = Math.min(a + por, total);
			rows.forEach(function (r, i) { r.hidden = i < a || i >= b; });
			info.textContent = (tbl.getAttribute('data-hatudu') || '{a}–{b} / {t}')
				.replace('{a}', a + 1).replace('{b}', b).replace('{t}', total);
			ul.innerHTML = '';
			if (atual > 1) { butaun('«', 1, false, 'first'); butaun('‹', atual - 1, false, 'prev'); }
			butaun(atual + ' / ' + pajinas, null, true);
			if (atual < pajinas) { butaun('›', atual + 1, false, 'next'); butaun('»', pajinas, false, 'last'); }
		}
		hatudu(1);
	}
	document.querySelectorAll('table[data-pajina]').forEach(liga);
})();
