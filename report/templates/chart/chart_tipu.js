{% load i18n %}
$.ajax({
    method: "GET",
    url: '/api/report/kazu/tipu/' + window.location.search,
    success: function(data){
        Highcharts.chart('chart_tipu', {
            chart: { type: 'pie', styledMode: true },
            title: { text: '' },
            tooltip: { pointFormat: '<b>{point.y}</b> ({point.percentage:.0f}%)' },
            plotOptions: { pie: { dataLabels: { enabled: true, format: '{point.name}: {point.y}' } } },
            series: [{ name: '{% trans "Kazu" %}', data: data.label.map(function (l, i) { return [l, data.obj[i]]; }) }]
        });
    },
    error: function(error_data){ console.log("error", error_data); }
});
