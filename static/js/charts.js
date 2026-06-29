document.addEventListener('DOMContentLoaded', function() {
    const dataContainer = document.getElementById('charts-data');
    if (!dataContainer) return;
    
    let chartsData = {};
    try {
        chartsData = JSON.parse(dataContainer.textContent);
    } catch (e) {
        console.error("Error parsing charts data: ", e);
        return;
    }

    // Default chart configuration options for premium aesthetics
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    font: { family: 'Outfit', size: 12 },
                    padding: 15
                }
            },
            tooltip: {
                padding: 12,
                titleFont: { family: 'Outfit', size: 13, weight: 'bold' },
                bodyFont: { family: 'Outfit', size: 12 },
                cornerRadius: 8,
                backgroundColor: 'rgba(31, 78, 121, 0.95)'
            }
        }
    };

    // Color Palette
    const colors = {
        blue: '#0d6efd',
        orange: '#fd7e14',
        amber: '#ffb703',
        purple: '#6f42c1',
        green: '#198754',
        red: '#dc3545',
        teal: '#20c997',
        cyan: '#0dcaf0',
        grey: '#6c757d',
        indigo: '#6610f2'
    };

    const colorArray = [colors.blue, colors.orange, colors.amber, colors.purple, colors.green, colors.red, colors.teal, colors.cyan, colors.indigo, colors.grey];

    // Helper: Map data dictionary to labels and values arrays
    const parseDict = (dict) => {
        const labels = Object.keys(dict);
        const values = Object.values(dict);
        return { labels, values };
    };

    // 1. Status Distribution (Doughnut)
    const statusData = parseDict(chartsData.status || {});
    new Chart(document.getElementById('statusChart'), {
        type: 'doughnut',
        data: {
            labels: statusData.labels,
            datasets: [{
                data: statusData.values,
                backgroundColor: statusData.labels.map(s => {
                    if (s === 'Open') return colors.blue;
                    if (s === 'Assigned') return colors.orange;
                    if (s === 'Hold') return colors.amber;
                    if (s === 'Escalated') return colors.purple;
                    if (s === 'Closed') return colors.green;
                    return colors.grey;
                }),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            ...commonOptions,
            cutout: '65%'
        }
    });

    // 2. Unit-wise Tickets (Pie)
    const unitData = parseDict(chartsData.units || {});
    new Chart(document.getElementById('unitChart'), {
        type: 'pie',
        data: {
            labels: unitData.labels,
            datasets: [{
                data: unitData.values,
                backgroundColor: colorArray.slice(0, unitData.labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: commonOptions
    });

    // 3. Department-wise Tickets (Horizontal Bar)
    const deptData = parseDict(chartsData.depts || {});
    new Chart(document.getElementById('deptChart'), {
        type: 'bar',
        data: {
            labels: deptData.labels,
            datasets: [{
                label: 'Tickets count',
                data: deptData.values,
                backgroundColor: colors.teal,
                borderRadius: 8
            }]
        },
        options: {
            ...commonOptions,
            indexAxis: 'y',
            plugins: { ...commonOptions.plugins, legend: { display: false } },
            scales: {
                x: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

    // 4. Priority Distribution (Pie)
    const priorityData = parseDict(chartsData.priority || {});
    new Chart(document.getElementById('priorityChart'), {
        type: 'pie',
        data: {
            labels: priorityData.labels,
            datasets: [{
                data: priorityData.values,
                backgroundColor: priorityData.labels.map(p => {
                    if (p === 'Critical') return colors.red;
                    if (p === 'High') return colors.orange;
                    if (p === 'Medium') return colors.blue;
                    return colors.green;
                })
            }]
        },
        options: commonOptions
    });

    // 5. Error Type Distribution (Pie)
    const errTypeData = parseDict(chartsData.error_type || {});
    new Chart(document.getElementById('errorTypeChart'), {
        type: 'pie',
        data: {
            labels: errTypeData.labels,
            datasets: [{
                data: errTypeData.values,
                backgroundColor: [colors.cyan, colors.indigo, colors.orange]
            }]
        },
        options: commonOptions
    });

    // 6. Monthly Ticket Trend (Line)
    const trendData = parseDict(chartsData.trend || {});
    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: trendData.labels,
            datasets: [{
                label: 'Monthly Tickets',
                data: trendData.values,
                borderColor: colors.blue,
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: true,
                tension: 0.3,
                borderWidth: 3,
                pointBackgroundColor: colors.blue
            }]
        },
        options: {
            ...commonOptions,
            plugins: { ...commonOptions.plugins, legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

    // 7. Escalated vs Closed (Bar)
    const escClosedData = parseDict(chartsData.esc_closed || {});
    new Chart(document.getElementById('escClosedChart'), {
        type: 'bar',
        data: {
            labels: escClosedData.labels,
            datasets: [{
                label: 'Tickets count',
                data: escClosedData.values,
                backgroundColor: [colors.purple, colors.green],
                borderRadius: 8
            }]
        },
        options: {
            ...commonOptions,
            plugins: { ...commonOptions.plugins, legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

    // 8. Average Resolution Time (hours) per Unit (Bar)
    const avgResData = parseDict(chartsData.avg_res || {});
    new Chart(document.getElementById('avgResChart'), {
        type: 'bar',
        data: {
            labels: avgResData.labels,
            datasets: [{
                label: 'Average Hours',
                data: avgResData.values,
                backgroundColor: colors.orange,
                borderRadius: 8
            }]
        },
        options: {
            ...commonOptions,
            plugins: { ...commonOptions.plugins, legend: { display: false } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Hours', font: { family: 'Outfit' } } }
            }
        }
    });

    // 9. Top 10 Reported Issues (Bar)
    const issuesData = parseDict(chartsData.top_issues || {});
    new Chart(document.getElementById('topIssuesChart'), {
        type: 'bar',
        data: {
            labels: issuesData.labels.map(lbl => lbl.length > 20 ? lbl.substring(0, 18) + '...' : lbl),
            datasets: [{
                label: 'Reported count',
                data: issuesData.values,
                backgroundColor: colors.indigo,
                borderRadius: 8
            }]
        },
        options: {
            ...commonOptions,
            plugins: {
                ...commonOptions.plugins,
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

    // 10. Top Departments by Ticket Count (Bar)
    const topDeptsData = parseDict(chartsData.top_depts || {});
    new Chart(document.getElementById('topDeptsChart'), {
        type: 'bar',
        data: {
            labels: topDeptsData.labels,
            datasets: [{
                label: 'Tickets count',
                data: topDeptsData.values,
                backgroundColor: colors.green,
                borderRadius: 8
            }]
        },
        options: {
            ...commonOptions,
            plugins: { ...commonOptions.plugins, legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });
});
