// static/js/shared/charts.js

// ============================================================
// CHART.JS - Shared Chart Functions
// ============================================================

/**
 * Creates a pie chart with drill-down functionality
 */
function createPieChart(canvasId, data, labels, colors, title, drilldownUrl) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }

    // Destroy existing chart if any
    if (canvas._chart) {
        canvas._chart.destroy();
    }

    // Default colors if not provided
    const defaultColors = [
        '#3B82F6', '#EF4444', '#22C55E', '#F59E0B', 
        '#8B5CF6', '#EC4899', '#14B8A6', '#F97316',
        '#6366F1', '#84CC16', '#06B6D4', '#D946EF'
    ];
    
    const chartColors = colors || defaultColors.slice(0, labels.length);

    const ctx = canvas.getContext('2d');
    const chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: chartColors,
                borderColor: '#ffffff',
                borderWidth: 2,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 11,
                            family: 'Inter, sans-serif'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: function(event, elements, chart) {
                if (elements.length > 0 && drilldownUrl) {
                    const index = elements[0].index;
                    const label = chart.data.labels[index];
                    const value = chart.data.datasets[0].data[index];
                    
                    if (value > 0) {
                        // Redirect to filtered tickets view
                        const url = drilldownUrl + '?filter=' + encodeURIComponent(label);
                        window.location.href = url;
                    }
                }
            }
        }
    });

    canvas._chart = chart;
    return chart;
}

/**
 * Creates a bar chart
 */
function createBarChart(canvasId, data, labels, colors, title, drilldownUrl) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }

    if (canvas._chart) {
        canvas._chart.destroy();
    }

    const defaultColors = [
        '#3B82F6', '#EF4444', '#22C55E', '#F59E0B', 
        '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
    ];
    
    const chartColors = colors || defaultColors.slice(0, labels.length);

    const ctx = canvas.getContext('2d');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title || 'Tickets',
                data: data,
                backgroundColor: chartColors,
                borderColor: chartColors.map(c => c),
                borderWidth: 1,
                borderRadius: 6,
                maxBarThickness: 60
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} tickets`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 10
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                }
            },
            onClick: function(event, elements, chart) {
                if (elements.length > 0 && drilldownUrl) {
                    const index = elements[0].index;
                    const label = chart.data.labels[index];
                    const value = chart.data.datasets[0].data[index];
                    
                    if (value > 0) {
                        const url = drilldownUrl + '?filter=' + encodeURIComponent(label);
                        window.location.href = url;
                    }
                }
            }
        }
    });

    canvas._chart = chart;
    return chart;
}

/**
 * Creates a line chart for monthly trends
 */
function createLineChart(canvasId, data, labels, color, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error('Canvas element not found:', canvasId);
        return null;
    }

    if (canvas._chart) {
        canvas._chart.destroy();
    }

    const ctx = canvas.getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: title || 'Tickets Created',
                data: data,
                backgroundColor: color || 'rgba(59, 130, 246, 0.1)',
                borderColor: color || '#3B82F6',
                borderWidth: 2,
                pointBackgroundColor: color || '#3B82F6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} tickets`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 10
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 9
                        },
                        maxRotation: 45,
                        minRotation: 30
                    }
                }
            }
        }
    });

    canvas._chart = chart;
    return chart;
}

/**
 * Initialize all charts on a dashboard
 */
function initDashboardCharts(chartConfigs) {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded. Please include Chart.js library.');
        return;
    }

    chartConfigs.forEach(function(config) {
        const canvas = document.getElementById(config.id);
        if (!canvas) return;

        switch (config.type) {
            case 'pie':
                createPieChart(
                    config.id,
                    config.data,
                    config.labels,
                    config.colors,
                    config.title,
                    config.drilldownUrl
                );
                break;
            case 'bar':
                createBarChart(
                    config.id,
                    config.data,
                    config.labels,
                    config.colors,
                    config.title,
                    config.drilldownUrl
                );
                break;
            case 'line':
                createLineChart(
                    config.id,
                    config.data,
                    config.labels,
                    config.color,
                    config.title
                );
                break;
            default:
                console.warn('Unknown chart type:', config.type);
        }
    });
}