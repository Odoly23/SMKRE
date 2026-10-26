{% load i18n %}
// Gráfiku status kazu, tribunál, Governu foti rai no eviksaun (dadus iha json_script "graf-dadus")
(function () {
    var G = JSON.parse(document.getElementById('graf-dadus').textContent);
    function koluna(id, dadus) {
        Highcharts.chart(id, {
            chart: { type: 'column', styledMode: true },
            title: { text: '' },
            xAxis: { type: 'category', labels: { rotation: -45 } },
            yAxis: { title: { text: '{% trans "Total Kazu" %}' }, allowDecimals: false },
            legend: { enabled: false },
            plotOptions: { column: { borderRadius: 4, colorByPoint: true, dataLabels: { enabled: true } } },
            series: [{ name: '{% trans "Kazu" %}', data: dadus }]
        });
    }
    function bar(id, dadus) {
        Highcharts.chart(id, {
            chart: { type: 'bar', styledMode: true },
            title: { text: '' },
            xAxis: { type: 'category' },
            yAxis: { title: { text: '{% trans "Total Kazu" %}' }, allowDecimals: false },
            legend: { enabled: false },
            plotOptions: { bar: { borderRadius: 4, colorByPoint: true, dataLabels: { enabled: true } } },
            series: [{ name: '{% trans "Kazu" %}', data: dadus }]
        });
    }
    function pie(id, dadus) {
        Highcharts.chart(id, {
            chart: { type: 'pie', styledMode: true },
            title: { text: '' },
            tooltip: { pointFormat: '<b>{point.y}</b> ({point.percentage:.0f}%)' },
            plotOptions: { pie: { dataLabels: { enabled: true, format: '{point.name}: {point.y}' } } },
            series: [{ name: '{% trans "Kazu" %}', data: dadus }]
        });
    }
    koluna('chart_tinan', G.tinan);
    bar('chart_rez', G.status);
    pie('chart_tribunal', G.tribunal);
    bar('chart_la_trib', G.tipu_la_trib);
    koluna('chart_entidade', G.entidade);
    koluna('chart_konsultasaun', G.konsultasaun_molok);
    koluna('chart_notifikasaun', G.notifikasaun_klaru);
    koluna('chart_forsa', G.uza_forsa);
})();
