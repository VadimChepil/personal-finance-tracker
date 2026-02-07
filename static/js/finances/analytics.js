document.addEventListener('DOMContentLoaded', function() {
    // Get chart data from JSON element
    const dataElement = document.getElementById('chart-data');
    if (!dataElement) {
        console.error('Chart data element not found');
        return;
    }

    const chartData = JSON.parse(dataElement.textContent);
        
        const categoryLabels = chartData.category_labels || [];
        const categoryData = chartData.category_data || [];
        const monthlyLabels = chartData.monthly_labels || [];
        const monthlyData = chartData.monthly_data || [];
        const currencyLabels = chartData.currency_labels || [];
        const currencyData = chartData.currency_data || [];
        const tableLabels = chartData.table_labels || [];
        const tableData = chartData.table_data || [];

    // Chart color palette
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
        '#9966FF', '#FF9F40', '#C9CBCF', '#43e97b',
        '#667eea', '#f093fb', '#4facfe', '#38f9d7'
    ];

    // 1. Category distribution chart (Pie chart)
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx) {
        new Chart(categoryCtx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryData,
                    backgroundColor: colors.slice(0, categoryLabels.length),
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                const value = context.parsed || 0;
                                label += value.toLocaleString('uk-UA', { 
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2 
                                }) + ' ₴';
                                
                                // Add percentage
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? (value / total * 100).toFixed(1) : 0;
                                label += ` (${percentage}%)`;
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Monthly trends chart (Line chart)
    const monthlyCtx = document.getElementById('monthlyChart');
    if (monthlyCtx) {
        new Chart(monthlyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: monthlyLabels,
                datasets: [{
                    label: 'Monthly Expenses',
                    data: monthlyData,
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#36A2EB',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toLocaleString('uk-UA', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                }) + ' ₴';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('uk-UA', {
                                    minimumFractionDigits: 0,
                                    maximumFractionDigits: 0
                                }) + ' ₴';
                            }
                        }
                    }
                }
            }
        });
    }

    // 3. Currency distribution chart (Doughnut chart)
    const currencyCtx = document.getElementById('currencyChart');
    if (currencyCtx) {
        new Chart(currencyCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: currencyLabels,
                datasets: [{
                    data: currencyData,
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const originalCurrency = label.includes('USD') ? '$' : 
                                                         label.includes('EUR') ? '€' : '₴';
                                return label + ': ' + value.toLocaleString('uk-UA', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                }) + ' ' + originalCurrency;
                            }
                        }
                    }
                }
            }
        });
    }

    // 4. Table distribution chart (Bar chart)
    const tableCtx = document.getElementById('tableChart');
    if (tableCtx) {
        new Chart(tableCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: tableLabels,
                datasets: [{
                    label: 'Expenses by Table',
                    data: tableData,
                    backgroundColor: colors.slice(0, tableLabels.length),
                    borderWidth: 1,
                    borderColor: '#fff',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toLocaleString('uk-UA', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                }) + ' ₴';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('uk-UA', {
                                    minimumFractionDigits: 0,
                                    maximumFractionDigits: 0
                                }) + ' ₴';
                            }
                        }
                    }
                }
            }
        });
    }
    
    
    // Moves legend from right to bottom on small screens
    function adjustLegendForMobile() {
        const categoryChartInstance = Chart.getChart('categoryChart');
        const currencyChartInstance = Chart.getChart('currencyChart');
        
        if (window.innerWidth < 768) {
            if (categoryChartInstance) {
                categoryChartInstance.options.plugins.legend.position = 'bottom';
                categoryChartInstance.update();
            }
            if (currencyChartInstance) {
                currencyChartInstance.options.plugins.legend.position = 'bottom';
                currencyChartInstance.update();
            }
        } else {
            if (categoryChartInstance) {
                categoryChartInstance.options.plugins.legend.position = 'right';
                categoryChartInstance.update();
            }
            if (currencyChartInstance) {
                currencyChartInstance.options.plugins.legend.position = 'right';
                currencyChartInstance.update();
            }
        }
    }
    
    // Event listener for window resize
    window.addEventListener('resize', adjustLegendForMobile);
    // Initial adjustment on page load
    adjustLegendForMobile();
});