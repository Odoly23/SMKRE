{% load i18n %}
$.ajax({
    method: "GET",
    url: '/api/report/kazu/mun/' + window.location.search,
    success: function(data){
        Highcharts.chart('chart_mun', {
            chart: { type: 'column', styledMode: true },
            title: { text: '' },
            xAxis: { categories: data.label },
            yAxis: [{ className: 'highcharts-color-0', title: { text: '{% trans "Total Kazu" %}' }, allowDecimals: false }],
            legend: { enabled: false },
            plotOptions: { column: { borderRadius: 5, dataLabels: { enabled: true } } },
            series: [{ name: '{% trans "Total Kazu" %}', data: data.obj }]
        });
    },
    error: function(error_data){ console.log("error", error_data); }
});
