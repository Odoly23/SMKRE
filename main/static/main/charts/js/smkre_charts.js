/* Konfigurasaun Highcharts ba SMKRE: la uza server externu (offline), la iha kréditu */
(function () {
	if (!window.Highcharts) return;
	var el = document.getElementById('chart-lang');
	var lang = el ? JSON.parse(el.textContent) : {};
	Highcharts.setOptions({
		lang: lang,
		credits: { enabled: false },
		exporting: { fallbackToExportServer: false, sourceWidth: 1200, sourceHeight: 600 },
		chart: { style: { fontFamily: 'Lato, sans-serif' } }
	});
})();
