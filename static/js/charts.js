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
});
