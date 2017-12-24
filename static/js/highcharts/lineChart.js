Highcharts.chart('lineContainer', {
    title: {
        text: ''
    },
    yAxis: {
        title: {
            text: 'Score'
        },
        tickPositions: [0, 25, 50, 75,100,125,150],
    },
    xAxis: {
        title: {
            text: 'DataTime'
        },
        categories: vm.times,

    },
    legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle'
    },

    series: vm.lineSeries,
    responsive: {
        rules: [{
            condition: {
                maxWidth: 500
            },
            chartOptions: {
                legend: {
                    layout: 'horizontal',
                    align: 'center',
                    verticalAlign: 'bottom'
                }
            }
        }]
    }
});
