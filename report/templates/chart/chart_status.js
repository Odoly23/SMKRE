{% load i18n %}
$.ajax({
    method: "GET",
    url: '/api/report/kazu/status/' + window.location.search,
    success: function(data){
        Highcharts.chart('chart_status', {
            chart: { type: 'bar', styledMode: true },
            title: { text: '' },
            xAxis: { categories: data.label },
            yAxis: { title: { text: '{% trans "Total Kazu" %}' }, allowDecimals: false },
            legend: { enabled: false },
            plotOptions: { bar: { borderRadius: 4, colorByPoint: true, dataLabels: { enabled: true } } },
            series: [{ name: '{% trans "Kazu" %}', data: data.obj }]
        });
    },
    error: function(error_data){ console.log("error", error_data); }
});
