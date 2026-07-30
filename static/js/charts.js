// ============================================
// CENTRALIZED CHART.JS CONFIGURATION
// ============================================

(function() {
    'use strict';

    // ============================================
    // COLOR PALETTE
    // ============================================
    const COLORS = {
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
        status: {
            'Open': '#48bb78',
            'Assigned': '#4299e1',
            'Hold': '#ed8936',
            'Escalated': '#9f7aea',
            'Closed': '#718096'
        },
        priority: {
            'Critical': '#fc8181',
            'High': '#ed8936',
            'Medium': '#4299e1',
            'Low': '#48bb78'
        },
        errorType: {
            'ERP Error': '#EF4444',
            'Data Entry Error': '#F59E0B',
            'DB Error': '#3B82F6',
            'Server Error': '#8B5CF6',
            'IT Error': '#EC4899',
            'User Error': '#06B6D4',
            'Other': '#94A3B8',
            'Network Error': '#14B8A6',
            'Security Error': '#6366F1',
            'Hardware Error': '#F97316'
        }
    };

    const COLOR_ARRAY = [
        COLORS.blue, COLORS.orange, COLORS.purple, COLORS.green,
        COLORS.teal, COLORS.red, COLORS.cyan, COLORS.indigo,
        COLORS.pink, COLORS.amber
    ];

    // ============================================
    // THEME HELPERS
    // ============================================
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            textColor: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
            borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.8)',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)',
            bgColor: isDark ? '#1a202c' : '#ffffff'
        };
    }

    // ============================================
    // COMMON CHART OPTIONS
    // ============================================
    function getCommonOptions() {
        const theme = getThemeColors();
        return {
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
                        font: { family: 'Poppins, Inter, sans-serif', size: 12 },
                        padding: 15,
                        color: theme.textColor,
                        usePointStyle: true,
                        pointStyleWidth: 10,
                    }
                },
                tooltip: {
                    padding: 12,
                    titleFont: { family: 'Poppins, Inter, sans-serif', size: 13, weight: 'bold' },
                    bodyFont: { family: 'Poppins, Inter, sans-serif', size: 12 },
                    cornerRadius: 8,
                    backgroundColor: 'rgba(26, 42, 108, 0.95)',
                    boxPadding: 8,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                            return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        };
    }

    // ============================================
    // HELPER FUNCTIONS
    // ============================================
    function parseDict(dict) {
        const labels = Object.keys(dict);
        const values = Object.values(dict);
        return { labels, values };
    }

    function parseArray(arr) {
        const labels = arr.map(item => item.label);
        const values = arr.map(item => item.value);
        const ids = arr.map(item => item.id);
        return { labels, values, ids };
    }

    // ============================================
    // CHART CREATORS
    // ============================================

    /**
     * Create a Doughnut/Status Chart
     */
    function createStatusChart(canvasId, data, clickUrl, drillDownFunction) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseDict(data || {});
        if (chartData.labels.length === 0) return null;

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: chartData.labels.map(label => 
                        COLORS.status[label] || COLORS.grey
                    ),
                    borderWidth: 2,
                    borderColor: theme.borderColor,
                    hoverOffset: 15,
                }]
            },
            options: {
                ...getCommonOptions(),
                cutout: '65%',
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = this.data.labels[index];
                        if (drillDownFunction) {
                            drillDownFunction(label, label);
                        }
                    }
                }
            }
        });
    }

    /**
     * Create a Priority Chart (Pie)
     */
    function createPriorityChart(canvasId, data, clickUrl, drillDownFunction) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseDict(data || {});
        if (chartData.labels.length === 0) return null;

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: chartData.labels.map(label => 
                        COLORS.priority[label] || COLORS.grey
                    ),
                    borderWidth: 2,
                    borderColor: theme.borderColor,
                    hoverOffset: 15,
                }]
            },
            options: {
                ...getCommonOptions(),
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = this.data.labels[index];
                        if (drillDownFunction) {
                            drillDownFunction(label, label);
                        }
                    }
                }
            }
        });
    }

    /**
     * Create a Unit-wise Chart (Pie)
     */
    function createUnitChart(canvasId, data, drillDownFunction) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseArray(data || []);
        if (chartData.labels.length === 0) return null;

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: COLOR_ARRAY.slice(0, chartData.labels.length),
                    borderWidth: 2,
                    borderColor: theme.borderColor,
                    hoverOffset: 15,
                }]
            },
            options: {
                ...getCommonOptions(),
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const unitId = chartData.ids[index];
                        const unitLabel = chartData.labels[index];
                        if (drillDownFunction) drillDownFunction(unitId, unitLabel);
                    }
                }
            }
        });
    }

    /**
     * Create a Monthly Bar Chart
     */
    function createMonthlyChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseArray(data || []);
        if (chartData.labels.length === 0) return null;

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Tickets Created',
                    data: chartData.values,
                    backgroundColor: chartData.values.map((val, i) => {
                        const alpha = 0.6 + (i / chartData.values.length) * 0.4;
                        return `rgba(59, 130, 246, ${alpha})`;
                    }),
                    borderColor: COLORS.blue,
                    borderWidth: 1,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: COLORS.blue,
                }]
            },
            options: {
                ...getCommonOptions(),
                plugins: {
                    ...getCommonOptions().plugins,
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
                            color: theme.textColor,
                            font: { family: 'Poppins, Inter, sans-serif', size: 11 },
                            maxRotation: 45,
                            minRotation: 45,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: theme.textColor,
                            font: { family: 'Poppins, Inter, sans-serif', size: 11 },
                        },
                        grid: {
                            color: theme.gridColor,
                        }
                    }
                }
            }
        });
    }

    /**
     * Create a Department-wise Horizontal Bar Chart
     */
    function createDepartmentChart(canvasId, data, clickUrl) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseArray(data || []);
        if (chartData.labels.length === 0) return null;

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Tickets',
                    data: chartData.values,
                    backgroundColor: chartData.values.map((val, i) => {
                        const colorIndex = i % COLOR_ARRAY.length;
                        return COLOR_ARRAY[colorIndex];
                    }),
                    borderWidth: 1,
                    borderColor: theme.borderColor,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                ...getCommonOptions(),
                indexAxis: 'y',
                plugins: {
                    ...getCommonOptions().plugins,
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: theme.textColor,
                            font: { family: 'Poppins, Inter, sans-serif', size: 11 },
                        },
                        grid: {
                            color: theme.gridColor,
                        }
                    },
                    y: {
                        ticks: {
                            color: theme.textColor,
                            font: { family: 'Poppins, Inter, sans-serif', size: 11 },
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const deptId = chartData.ids[index];
                        if (clickUrl) {
                            window.location.href = clickUrl + '?department=' + encodeURIComponent(deptId);
                        }
                    }
                }
            }
        });
    }

    /**
     * Create a Department Status Chart (for Employee Dashboard)
     */
    function createDeptStatusChart(canvasId, data, drillDownFunction) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseDict(data || {});
        if (chartData.labels.length === 0) {
            // Show empty state
            const emptyEl = document.getElementById(canvasId + 'Empty');
            if (emptyEl) emptyEl.style.display = 'flex';
            ctx.style.display = 'none';
            return null;
        }

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: chartData.labels.map(label => 
                        COLORS.status[label] || COLORS.grey
                    ),
                    borderWidth: 2,
                    borderColor: theme.borderColor,
                    hoverOffset: 10
                }]
            },
            options: {
                ...getCommonOptions(),
                cutout: '65%',
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = this.data.labels[index];
                        if (drillDownFunction) {
                            drillDownFunction(label);
                        }
                    }
                }
            }
        });
    }

    /**
     * Create a Department Priority Chart (for Employee Dashboard)
     */
    function createDeptPriorityChart(canvasId, data, drillDownFunction) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseDict(data || {});
        if (chartData.labels.length === 0) {
            const emptyEl = document.getElementById(canvasId + 'Empty');
            if (emptyEl) emptyEl.style.display = 'flex';
            ctx.style.display = 'none';
            return null;
        }

        const theme = getThemeColors();
        
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: chartData.labels.map(label => 
                        COLORS.priority[label] || COLORS.grey
                    ),
                    borderWidth: 2,
                    borderColor: theme.borderColor,
                    hoverOffset: 10
                }]
            },
            options: {
                ...getCommonOptions(),
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = this.data.labels[index];
                        if (drillDownFunction) {
                            drillDownFunction(label);
                        }
                    }
                }
            }
        });
    }

    // ============================================
    // ✅ NEW: CREATE ERROR TYPE CHART
    // ============================================
    function createErrorTypeChart(canvasId, data, drillDownFunction) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = parseDict(data || {});
        
        // If no data, show empty state
        if (chartData.labels.length === 0) {
            ctx.style.display = 'none';
            const container = document.getElementById(canvasId + 'Container');
            if (container) {
                let emptyMsg = container.querySelector('.chart-empty-msg');
                if (!emptyMsg) {
                    emptyMsg = document.createElement('div');
                    emptyMsg.className = 'chart-empty-msg';
                    emptyMsg.style.cssText = `
                        text-align: center;
                        padding: 2rem 1rem;
                        color: var(--text-muted);
                    `;
                    emptyMsg.innerHTML = `
                        <i class="fa-solid fa-bug" style="font-size: 2rem; display: block; margin-bottom: 0.5rem; opacity: 0.3;"></i>
                        <p style="margin: 0; font-size: 0.85rem;">No error type data available</p>
                        <p style="margin: 0; font-size: 0.7rem; opacity: 0.7;">Only closed tickets with error types are shown</p>
                    `;
                    container.appendChild(emptyMsg);
                }
            }
            return null;
        }

        const theme = getThemeColors();
        
        // Use errorType colors from COLORS object
        const colors = chartData.labels.map(label => 
            COLORS.errorType[label] || COLORS.grey
        );
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: theme.borderColor,
                    hoverOffset: 15,
                }]
            },
            options: {
                ...getCommonOptions(),
                cutout: '65%',
                plugins: {
                    ...getCommonOptions().plugins,
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            font: { family: 'Poppins, Inter, sans-serif', size: 11 },
                            padding: 12,
                            color: theme.textColor,
                            usePointStyle: true,
                            pointStyleWidth: 10,
                            boxWidth: 12,
                        }
                    }
                },
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = this.data.labels[index];
                        if (drillDownFunction) {
                            drillDownFunction(label);
                        }
                    }
                }
            }
        });
    }

    // ============================================
    // THEME UPDATE FUNCTION
    // ============================================
    function updateAllCharts() {
        const theme = getThemeColors();
        Chart.helpers.each(Chart.instances, function(instance) {
            // Update border colors
            if (instance.data && instance.data.datasets) {
                instance.data.datasets.forEach(function(dataset) {
                    if (dataset.borderColor && typeof dataset.borderColor === 'string') {
                        dataset.borderColor = theme.borderColor;
                    }
                });
            }
            
            // Update legend colors
            if (instance.options.plugins && instance.options.plugins.legend) {
                if (instance.options.plugins.legend.labels) {
                    instance.options.plugins.legend.labels.color = theme.textColor;
                }
            }
            
            // Update scales colors
            if (instance.options.scales) {
                if (instance.options.scales.x) {
                    if (instance.options.scales.x.ticks) {
                        instance.options.scales.x.ticks.color = theme.textColor;
                    }
                    if (instance.options.scales.x.grid) {
                        instance.options.scales.x.grid.color = theme.gridColor;
                    }
                }
                if (instance.options.scales.y) {
                    if (instance.options.scales.y.ticks) {
                        instance.options.scales.y.ticks.color = theme.textColor;
                    }
                    if (instance.options.scales.y.grid) {
                        instance.options.scales.y.grid.color = theme.gridColor;
                    }
                }
            }
            
            instance.update();
        });
    }

    // ============================================
    // WATCH FOR THEME CHANGES
    // ============================================
    function watchThemeChanges() {
        const themeObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'data-theme') {
                    setTimeout(updateAllCharts, 100);
                }
            });
        });

        themeObserver.observe(document.documentElement, {
            attributes: true
        });
    }

    // ============================================
    // RESIZE HANDLER
    // ============================================
    function setupResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                Chart.helpers.each(Chart.instances, function(instance) {
                    instance.resize();
                });
            }, 200);
        });
    }

    // ============================================
    // CHART INITIALIZATION FUNCTION
    // ============================================
    window.initCharts = function(config) {
        const charts = {
            status: null,
            priority: null,
            unit: null,
            monthly: null,
            department: null,
            deptStatus: null,
            deptPriority: null,
            errorType: null  // ✅ ADDED ERROR TYPE
        };

        // Admin Dashboard Charts
        if (config.adminCharts) {
            const data = config.adminCharts;
            
            // Status Chart
            if (document.getElementById('statusChart')) {
                charts.status = createStatusChart(
                    'statusChart', data.status,
                    function(status) {
                        if (config.drillDown) config.drillDown.status(status);
                    }
                );
            }

            // Unit Chart
            if (document.getElementById('unitChart')) {
                charts.unit = createUnitChart('unitChart', data.units,
                    function(unitId, unitLabel) {
                        if (config.drillDown) config.drillDown.unit(unitId, unitLabel);
                    }
                );
            }

            // Priority Chart
            if (document.getElementById('priorityChart')) {
                charts.priority = createPriorityChart(
                    'priorityChart', data.priority,
                    function(priority) {
                        if (config.drillDown) config.drillDown.priority(priority);
                    }
                );
            }

            // ✅ ADDED: Error Type Chart
            if (document.getElementById('errorTypeChart')) {
                charts.errorType = createErrorTypeChart(
                    'errorTypeChart',
                    data.errorType || {},
                    function(errorType) {
                        if (config.drillDown) config.drillDown.errorType(errorType);
                    }
                );
            }

            // Monthly Chart
            if (document.getElementById('monthlyChart')) {
                charts.monthly = createMonthlyChart(
                    'monthlyChart',
                    data.monthly
                );
            }

            // Department Chart
            if (document.getElementById('departmentChart')) {
                charts.department = createDepartmentChart(
                    'departmentChart',
                    data.departments,
                    '/admin/tickets/'
                );
            }
        }

        // Employee Dashboard Charts
        if (config.employeeCharts) {
            const data = config.employeeCharts;
            
            // Department Status Chart
            if (document.getElementById('deptStatusChart')) {
                charts.deptStatus = createDeptStatusChart(
                    'deptStatusChart',
                    data.dept_status,
                    function(status) {
                        if (config.drillDown) {
                            config.drillDown.status(status);
                        }
                    }
                );
            }

            // Department Priority Chart
            if (document.getElementById('deptPriorityChart')) {
                charts.deptPriority = createDeptPriorityChart(
                    'deptPriorityChart',
                    data.dept_priority,
                    function(priority) {
                        if (config.drillDown) {
                            config.drillDown.priority(priority);
                        }
                    }
                );
            }
        }

        // Setup theme watching and resize
        watchThemeChanges();
        setupResizeHandler();

        // Initial theme update
        setTimeout(updateAllCharts, 500);

        console.log('✅ Charts initialized successfully!');
        console.log('📊 Charts created:', Object.keys(charts).filter(k => charts[k] !== null));
        return charts;
    };

    // ============================================
    // EXPOSE HELPERS GLOBALLY
    // ============================================
    window.COLORS = COLORS;
    window.createStatusChart = createStatusChart;
    window.createPriorityChart = createPriorityChart;
    window.createUnitChart = createUnitChart;
    window.createMonthlyChart = createMonthlyChart;
    window.createDepartmentChart = createDepartmentChart;
    window.createDeptStatusChart = createDeptStatusChart;
    window.createDeptPriorityChart = createDeptPriorityChart;
    window.createErrorTypeChart = createErrorTypeChart;  // ✅ EXPOSED
    window.updateAllCharts = updateAllCharts;

})();