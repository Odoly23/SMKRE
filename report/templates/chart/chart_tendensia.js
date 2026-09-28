{% load i18n %}
$.ajax({
    method: "GET",
    url: '/api/report/kazu/tendensia/' + window.location.search,
    success: function(data){
        Highcharts.chart('chart_tendensia', {
            chart: { type: 'line', styledMode: true },
            title: { text: '' },
            xAxis: { categories: data.label },
            yAxis: { title: { text: '{% trans "Kazu" %}' }, allowDecimals: false },
            series: [
                { name: '{% trans "Total kazu" %}', data: data.total },
                { name: '{% trans "Deslokamentu / Eviksaun" %}', data: data.eviksaun, dashStyle: 'ShortDash' }
            ]
        });
    },
    error: function(error_data){ console.log("error", error_data); }
});
