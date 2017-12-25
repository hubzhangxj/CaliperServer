function chart(title,key,data) {
    // console.log("-------------------------");
    // console.log(key);
    Highcharts.chart(key, {
        title: {
            text: key +' BarChart'
        },
        subtitle: {
            text: 'Test Cases for  '+title+'_' + key
        },
        yAxis: {
            title: {
                text: 'Score'
            },
            tickPositions: [0, 25, 50, 75, 100, 125, 150],
        },
        xAxis: {
            title: {
                text: 'DataTime'
            },
            categories: data['categories'],

        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle'
        },

        series: data['series'],
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
}
