{% load i18n %}
$.ajax({
    method: "GET",
    url: '/api/report/kazu/afetadu/' + window.location.search,
    success: function(data){
        Highcharts.chart('chart_afetadu', {
            chart: { type: 'column', styledMode: true },
            title: { text: '' },
            xAxis: { categories: data.label },
            yAxis: { title: { text: '{% trans "Ema" %}' }, allowDecimals: false, stackLabels: { enabled: true } },
            plotOptions: { column: { stacking: 'normal', borderRadius: 3 } },
            tooltip: { valueSuffix: ' {% trans "ema" %}' },
            series: [
                { name: '{% trans "Mane" %}', data: data.mane },
                { name: '{% trans "Feto" %}', data: data.feto },
                { name: '{% trans "Labarik" %}', data: data.labarik }
            ]
        });
    },
    error: function(error_data){ console.log("error", error_data); }
});
