Highcharts.chart('container', {
    chart: {
        type: 'column'
    },
     title: {
        text: vm.sce_title
    },
    xAxis: {
        categories: vm.categories,
        crosshair: true
    },
    yAxis: {
        min: 0,
        title: {
            text: 'Score'
        },
        tickPositions: [0, 25, 50, 75,100,125,150],
    },
    tooltip: {
        headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
        pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
        '<td style="padding:0"><b>{point.y:.1f}</b></td></tr>',
        footerFormat: '</table>',
        shared: true,
        useHTML: true
    },
    plotOptions: {
        column: {
            borderWidth: 0
        }
    },
    series: vm.sce_series
});
