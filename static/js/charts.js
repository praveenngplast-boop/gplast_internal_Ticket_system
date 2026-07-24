document.addEventListener('DOMContentLoaded', function() {
    const dataContainer = document.getElementById('charts-data');

    // Get current theme for dynamic colors
    function getThemeBorderColor() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.8)';
    }

    function getThemeGridColor() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)';
    }

    function getThemeTextColor() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)';
    }

    if (!dataContainer) return;
    
    let chartsData = {};
    try {
        chartsData = JSON.parse(dataContainer.textContent);
    } catch (e) {
        console.error("Error parsing charts data: ", e);
        return;
    }

    // Default chart configuration
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart',
        },
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    font: { family: 'Poppins', size: 12 },
                    padding: 15,
                    color: getThemeTextColor(),
                    usePointStyle: true,
                    pointStyleWidth: 10,
                }
            },
            tooltip: {
                padding: 12,
                titleFont: { family: 'Poppins', size: 13, weight: 'bold' },
                bodyFont: { family: 'Poppins', size: 12 },
                cornerRadius: 8,
                backgroundColor: 'rgba(26, 42, 108, 0.95)',
                boxPadding: 8,
            }
        }
    };

    // Color Palette
    const colors = {
        blue: '#3B82F6',
        orange: '#F59E0B',
        amber: '#FBBF24',
        purple: '#8B5CF6',
        green: '#22C55E',
        red: '#EF4444',
        teal: '#14B8A6',
        cyan: '#06B6D4',
        grey: '#6B7280',
        indigo: '#6366F1',
        pink: '#EC4899',
    };

    const colorArray = [
        colors.blue, colors.orange, colors.purple, colors.green, 
        colors.teal, colors.red, colors.cyan, colors.indigo, 
        colors.pink, colors.amber
    ];

    // Helper: Map data dictionary to labels and values arrays
    const parseDict = (dict) => {
        const labels = Object.keys(dict);
        const values = Object.values(dict);
        return { labels, values };
    };

    // Helper: Map data array of objects to labels, values, and ids
    const parseArray = (arr) => {
        const labels = arr.map(item => item.label);
        const values = arr.map(item => item.value);
        const ids = arr.map(item => item.id);
        return { labels, values, ids };
    };

    // ============================================
    // CHART 1: STATUS DISTRIBUTION (DOUGHNUT)
    // ============================================
    const statusData = parseDict(chartsData.status || {});
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        new Chart(statusCtx, {
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
                    borderColor: getThemeBorderColor(),
                    hoverOffset: 15,
                }]
            },
            options: {
                ...commonOptions,
                cutout: '65%',
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const status = statusCtx.chart.data.labels[index];
                        window.location.href = `/admin/tickets/?status=${encodeURIComponent(status)}`;
                    }
                }
            }
        });
    }

    // ============================================
    // CHART 2: UNIT-WISE TICKETS (PIE)
    // ============================================
    const unitData = parseArray(chartsData.units || []);
    const unitCtx = document.getElementById('unitChart');
    if (unitCtx) {
        new Chart(unitCtx, {
            type: 'pie',
            data: {
                labels: unitData.labels,
                datasets: [{
                    data: unitData.values,
                    backgroundColor: colorArray.slice(0, unitData.labels.length),
                    borderWidth: 2,
                    borderColor: getThemeBorderColor(),
                    hoverOffset: 15,
                }]
            },
            options: {
                ...commonOptions,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const unitId = unitData.ids[index];
                        window.location.href = `/admin/tickets/?unit=${unitId}`;
                    }
                }
            }
        });
    }

    // ============================================
    // CHART 3: PRIORITY DISTRIBUTION (PIE)
    // ============================================
    const priorityData = parseDict(chartsData.priority || {});
    const priorityCtx = document.getElementById('priorityChart');
    if (priorityCtx) {
        new Chart(priorityCtx, {
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
                    }),
                    borderWidth: 2,
                    borderColor: getThemeBorderColor(),
                    hoverOffset: 15,
                }]
            },
            options: {
                ...commonOptions,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const priority = priorityCtx.chart.data.labels[index];
                        window.location.href = `/admin/tickets/?priority=${encodeURIComponent(priority)}`;
                    }
                }
            }
        });
    }

    // ============================================
    // CHART 4: MONTHLY TICKET CREATION (BAR CHART)
    // ============================================
    const monthlyData = parseArray(chartsData.monthly || []);
    const monthlyCtx = document.getElementById('monthlyChart');
    if (monthlyCtx) {
        new Chart(monthlyCtx, {
            type: 'bar',
            data: {
                labels: monthlyData.labels,
                datasets: [{
                    label: 'Tickets Created',
                    data: monthlyData.values,
                    backgroundColor: monthlyData.values.map((val, i) => {
                        const alpha = 0.6 + (i / monthlyData.values.length) * 0.4;
                        return `rgba(59, 130, 246, ${alpha})`;
                    }),
                    borderColor: colors.blue,
                    borderWidth: 1,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: colors.blue,
                }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getThemeTextColor(),
                            font: { family: 'Poppins', size: 11 },
                            maxRotation: 45,
                            minRotation: 45,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: getThemeTextColor(),
                            font: { family: 'Poppins', size: 11 },
                        },
                        grid: {
                            color: getThemeGridColor(),
                        }
                    }
                }
            }
        });
    }

    // ============================================
    // CHART 5: DEPARTMENT-WISE TICKETS (HORIZONTAL BAR)
    // ============================================
    const deptData = parseArray(chartsData.departments || []);
    const deptCtx = document.getElementById('departmentChart');
    if (deptCtx && deptData.labels.length > 0) {
        new Chart(deptCtx, {
            type: 'bar',
            data: {
                labels: deptData.labels,
                datasets: [{
                    label: 'Tickets',
                    data: deptData.values,
                    backgroundColor: deptData.values.map((val, i) => {
                        const colorIndex = i % colorArray.length;
                        return colorArray[colorIndex];
                    }),
                    borderWidth: 1,
                    borderColor: getThemeBorderColor(),
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                ...commonOptions,
                indexAxis: 'y', // Makes it horizontal
                plugins: {
                    ...commonOptions.plugins,
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: getThemeTextColor(),
                            font: { family: 'Poppins', size: 11 },
                        },
                        grid: {
                            color: getThemeGridColor(),
                        }
                    },
                    y: {
                        ticks: {
                            color: getThemeTextColor(),
                            font: { family: 'Poppins', size: 11 },
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const deptId = deptData.ids[index];
                        window.location.href = `/admin/tickets/?department=${deptId}`;
                    }
                }
            }
        });
    }

    console.log('✅ Charts initialized successfully!');
});