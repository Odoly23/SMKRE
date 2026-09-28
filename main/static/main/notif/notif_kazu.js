/* Notifikasaun 🔔 — pola hanesan SGDS: $.get ba API kada segundu 30 */
(function () {
	'use strict';
	var cfg = document.getElementById('notif-script');
	if (!cfg) return;

	function esc(t) { return $('<div>').text(t).html(); }

	function notifKazu() {
		if (!navigator.onLine) return;
		$.get(cfg.dataset.ikus, function (data) {
			document.getElementById('notifbadge').innerHTML = data.value > 0 ? data.value : '';
			var box = document.getElementById('notif-items');
			if (!box) return;
			if (!data.objects.length) return;
			box.innerHTML = data.objects.map(function (o) {
				return '<a class="dropdown-item ' + (o.urgent ? 'urgent' : '') + '" href="' + cfg.dataset.open + o.id + '/">' +
					(o.urgent ? '<span class="badge badge-urjente rounded-pill px-2">URJENTE</span><br>' : '') +
					'<b>' + esc(o.message) + '</b><br><small class="text-muted">' + esc(o.ago) + '</small></a>';
			}).join('');
		});
	}
	notifKazu();                       // la'o dala ida kedas bainhira pájina loke
	setInterval(notifKazu, 30000);     // depois kada segundu 30
})();
