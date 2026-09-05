var adminAllTicketsUrl = '/custom-admin/tickets/';

document.addEventListener('DOMContentLoaded', function() {

    var adminAllTicketsUrlElement = document.getElementById('adminAllTicketsUrl');
    adminAllTicketsUrl = adminAllTicketsUrlElement
        ? adminAllTicketsUrlElement.getAttribute('data-url')
        : adminAllTicketsUrl;

    function forceCleanupBackdrops() {
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    var chartsData = {};
    try {
        var dataElement = document.getElementById('charts-data');
        if (dataElement) {
            chartsData = JSON.parse(dataElement.textContent);
        }
    } catch (e) {}

    function setupLegendClickHandler(legendId, chartType, labels) {
        var legendContainer = document.getElementById(legendId);
        if (!legendContainer) return;

        legendContainer.querySelectorAll('.chart-legend-item').forEach(function(item, index) {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                var label = labels[index];
                if (!label) return;

                if (chartType === 'status') {
                    drillDownAdminTickets(label);
                } else if (chartType === 'priority') {
                    drillDownWithFilter('priority', label, 'Priority: ' + label);
                } else if (chartType === 'unit') {
                    var unitData = chartsData.units || [];
                    var unit = unitData.find(function(u) {
                        return (u.label || u.name || u.unit) === label;
                    });
                    drillDownWithFilter('unit', unit ? unit.id || unit.unit_id : label, 'Unit: ' + label);
                } else if (chartType === 'errorType') {
                    drillDownWithFilter('errorType', label, 'Error Type: ' + label + ' (Closed Tickets)');
                } else if (chartType === 'subErrorType') {
                    drillDownWithFilter('subErrorType', label, 'Sub Error: ' + label + ' (Closed Tickets)');
                }
            });
        });
    }

    window.handleAdminChartClick = function(chartType) {
        if (chartType === 'status') {
            var statusData = chartsData.status || {};
            var statusLabels = Object.keys(statusData);
            if (statusLabels.length > 0) drillDownAdminTickets(statusLabels[0]);
        } else if (chartType === 'unit') {
            var unitData = chartsData.units || [];
            if (unitData.length > 0) {
                var firstUnit = unitData[0];
                drillDownWithFilter('unit', firstUnit.id || firstUnit.unit_id, 'Unit: ' + (firstUnit.label || firstUnit.name || 'Unknown'));
            }
        } else if (chartType === 'priority') {
            var priorityData = chartsData.priority || {};
            var priorityLabels = Object.keys(priorityData);
            if (priorityLabels.length > 0) drillDownWithFilter('priority', priorityLabels[0], 'Priority: ' + priorityLabels[0]);
        } else if (chartType === 'errorType') {
            var errorTypeData = chartsData.mainErrorType || chartsData.errorType || {};
            var errorTypeLabels = Object.keys(errorTypeData);
            if (errorTypeLabels.length > 0) {
                drillDownWithFilter('errorType', errorTypeLabels[0], 'Error Type: ' + errorTypeLabels[0] + ' (Closed Tickets)');
            }
        }
    };

    window.drillDownAdminTickets = drillDownAdminTickets;
    window.drillDownWithFilter = drillDownWithFilter;

    function generateLegend(legendId, labels, colors, chartType) {
        var container = document.getElementById(legendId);
        if (!container) return;
        container.innerHTML = '';
        labels.forEach(function(label, index) {
            var item = document.createElement('span');
            item.className = 'chart-legend-item';
            var displayLabel = label;
            if (displayLabel.length > 12) displayLabel = displayLabel.substring(0, 10) + '...';
            item.innerHTML = `
                <span class="legend-color" style="background: ${colors[index % colors.length]};"></span>
                ${displayLabel}
            `;
            container.appendChild(item);
        });

        setTimeout(function() {
            setupLegendClickHandler(legendId, chartType, labels);
        }, 100);
    }

    function initChartsWithLegends() {
        var statusColors = ['#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#94A3B8'];
        var unitColors = ['#FF6B00', '#FFB800', '#3B82F6', '#22C55E', '#8B5CF6', '#EF4444', '#F59E0B', '#06B6D4', '#EC4899'];
        var priorityColors = ['#EF4444', '#F59E0B', '#3B82F6', '#22C55E'];
        var errorTypeColors = ['#8B5CF6', '#10B981', '#94A3B8', '#F59E0B', '#EF4444', '#3B82F6', '#EC4899', '#06B6D4'];

        var statusData = chartsData.status || {};
        var unitData = chartsData.units || [];
        var priorityData = chartsData.priority || {};
        var errorTypeData = chartsData.mainErrorType || chartsData.errorType || {};

        var statusLabels = Object.keys(statusData);
        if (statusLabels.length > 0) {
            generateLegend('statusLegend', statusLabels, statusColors, 'status');
        }

        var unitLabels = unitData.map(function(u) { return u.label || u.name || u.unit || 'Unknown'; });
        if (unitLabels.length > 0) {
            generateLegend('unitLegend', unitLabels, unitColors, 'unit');
        }

        var priorityLabels = Object.keys(priorityData);
        if (priorityLabels.length > 0) {
            generateLegend('priorityLegend', priorityLabels, priorityColors, 'priority');
        }

        var errorTypeLabels = Object.keys(errorTypeData);
        if (errorTypeLabels.length > 0) {
            generateLegend('errorTypeLegend', errorTypeLabels, errorTypeColors, 'errorType');
        }
    }

    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    var textColor = isDark ? '#E8EDF5' : '#1A2A6C';

    function createChart(canvasId, data, colors, type, chartType) {
        var canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        var labels = Object.keys(data);
        var values = Object.values(data);
        if (labels.length === 0) {
            var empty = document.getElementById(canvasId.replace('Chart', 'Empty'));
            if (empty) { empty.style.display = 'flex'; }
            return null;
        }
        var ctx = canvas.getContext('2d');
        var chart = new Chart(ctx, {
            type: type || 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: isDark ? '#1A1A2E' : '#FFFFFF',
                    borderWidth: 3,
                    hoverOffset: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                var total = context.dataset.data.reduce(function(a, b) { return a + b; }, 0);
                                var percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }
                        }
                    }
                },
                cutout: type === 'doughnut' ? '60%' : undefined,
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        var index = elements[0].index;
                        var label = this.data.labels[index];
                        if (canvasId === 'statusChart') {
                            drillDownAdminTickets(label);
                        } else if (canvasId === 'priorityChart') {
                            drillDownWithFilter('priority', label, 'Priority: ' + label);
                        } else if (canvasId === 'unitChart') {
                            var unitData = chartsData.units || [];
                            var unit = unitData.find(function(u) { return (u.label || u.name || u.unit) === label; });
                            drillDownWithFilter('unit', unit ? unit.id || unit.unit_id : label, 'Unit: ' + label);
                        } else if (canvasId === 'errorTypeChart') {
                            drillDownWithFilter('errorType', label, 'Error Type: ' + label + ' (Closed Tickets)');
                        }
                    }
                }
            }
        });
        canvas.chart = chart;
        return chart;
    }

    var statusColors = ['#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#94A3B8'];
    var unitColors = ['#FF6B00', '#FFB800', '#3B82F6', '#22C55E', '#8B5CF6', '#EF4444', '#F59E0B', '#06B6D4', '#EC4899'];
    var priorityColors = ['#EF4444', '#F59E0B', '#3B82F6', '#22C55E'];
    var errorTypeColors = ['#8B5CF6', '#10B981', '#94A3B8', '#F59E0B', '#EF4444', '#3B82F6', '#EC4899', '#06B6D4'];

    createChart('statusChart', chartsData.status || {}, statusColors, 'doughnut', 'status');
    
    var unitChartData = {};
    if (chartsData.units) {
        chartsData.units.forEach(function(u) {
            unitChartData[u.label || u.name || u.unit] = u.count || u.value || 0;
        });
    }
    createChart('unitChart', unitChartData, unitColors, 'doughnut', 'unit');
    createChart('priorityChart', chartsData.priority || {}, priorityColors, 'pie', 'priority');
    createChart('errorTypeChart', chartsData.mainErrorType || chartsData.errorType || {}, errorTypeColors, 'doughnut', 'errorType');

    setTimeout(initChartsWithLegends, 500);

    var kpiValues = document.querySelectorAll('.kpi-value');
    kpiValues.forEach(function(value, index) {
        var originalText = value.textContent;
        if (!isNaN(parseInt(originalText))) {
            value.textContent = '0';
            setTimeout(function() {
                value.textContent = originalText;
                value.style.transform = 'scale(1.1)';
                setTimeout(function() { value.style.transform = 'scale(1)'; }, 300);
            }, 300 + (index * 80));
        }
    });

    function resizeCharts() {
        document.querySelectorAll('.chart-wrapper canvas').forEach(function(canvas) {
            if (canvas.chart) canvas.chart.resize();
        });
    }

    var resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(resizeCharts, 250);
    });

    function updateChartColors() {
        var isDarkNow = document.documentElement.getAttribute('data-theme') === 'dark';
        var newColor = isDarkNow ? '#E8EDF5' : '#1A2A6C';
        document.querySelectorAll('.chart-wrapper canvas').forEach(function(canvas) {
            if (canvas.chart) {
                var chart = canvas.chart;
                if (chart.options.plugins && chart.options.plugins.legend) {
                    chart.options.plugins.legend.labels.color = newColor;
                    chart.update();
                }
            }
        });
    }

    var themeToggleBtn = document.getElementById('themeToggleFloating');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            setTimeout(updateChartColors, 150);
        });
    }

    var themeObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                setTimeout(updateChartColors, 150);
            }
        });
    });
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    var modalEl = document.getElementById('adminDrillDownModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', function() { forceCleanupBackdrops(); });
        modalEl.addEventListener('hide.bs.modal', function() { setTimeout(forceCleanupBackdrops, 50); });
    }
});

// ============================================================
// DRILL DOWN FUNCTIONS - WITH AGING
// ============================================================

function drillDownAdminTickets(filterValue) {
    forceCleanupBackdrops();

    var modalEl = document.getElementById('adminDrillDownModal');
    var modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

    var modalBody = document.getElementById('adminDrillDownModalBody');
    var statusLabel = document.getElementById('adminDrillDownStatusLabel');
    var viewAllBtn = document.getElementById('adminDrillDownViewAllBtn');

    var statusMap = {
        'all': 'All Tickets',
        'Open': 'Open Tickets',
        'Assigned': 'Assigned Tickets',
        'Hold': 'Hold Tickets',
        'Escalated': 'Escalated Tickets',
        'Closed': 'Closed Tickets',
        'Critical': 'Critical Priority Tickets'
    };
    statusLabel.textContent = statusMap[filterValue] || filterValue || 'All Tickets';

    var filterParam = 'status';
    if (filterValue === 'Critical') { filterParam = 'priority'; }
    else if (filterValue === 'all') { filterParam = ''; }

    if (filterParam) {
        viewAllBtn.href = adminAllTicketsUrl + "?" + filterParam + "=" + encodeURIComponent(filterValue);
    } else {
        viewAllBtn.href = adminAllTicketsUrl;
    }

    modalBody.innerHTML = `
        <div class="modal-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading tickets...</p>
        </div>
    `;

    modal.show();

    var url = adminAllTicketsUrl + "?ajax=1";
    if (filterParam) { url += "&" + filterParam + "=" + encodeURIComponent(filterValue); }

    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function(response) {
        if (!response.ok) throw new Error('Server returned ' + response.status);
        return response.json();
    })
    .then(function(data) {
        if (data.success === false) throw new Error(data.message || 'Server error');
        if (data.html) {
            modalBody.innerHTML = data.html;
            if (data.count !== undefined) {
                statusLabel.textContent = (statusMap[filterValue] || filterValue || 'All Tickets') + ` (${data.count})`;
            }
        } else {
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: var(--text-muted);">
                    <i class="fa-solid fa-receipt fa-2x mb-2 d-block opacity-25" style="color: var(--brand-orange);"></i>
                    <p>No tickets found</p>
                </div>
            `;
        }
    })
    .catch(function(error) {
        modalBody.innerHTML = `
            <div class="text-center py-4" style="color: #EF4444;">
                <i class="fa-solid fa-circle-exclamation fa-2x mb-2 d-block"></i>
                <p><strong>Error loading tickets</strong></p>
                <p style="font-size: 0.85rem; color: var(--text-muted);">${error.message || 'Please try again.'}</p>
                <button class="btn btn-primary-custom btn-sm mt-2" onclick="drillDownAdminTickets('${filterValue}')">
                    <i class="fa-solid fa-rotate me-1"></i>Retry
                </button>
            </div>
        `;
    });
}

function drillDownWithFilter(filterType, filterValue, filterLabel) {
    forceCleanupBackdrops();

    var modalEl = document.getElementById('adminDrillDownModal');
    var modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

    var modalBody = document.getElementById('adminDrillDownModalBody');
    var statusLabel = document.getElementById('adminDrillDownStatusLabel');
    var viewAllBtn = document.getElementById('adminDrillDownViewAllBtn');

    statusLabel.textContent = filterLabel;

    var url = adminAllTicketsUrl + "?ajax=1";
    
    if (filterType === 'unit') {
        viewAllBtn.href = adminAllTicketsUrl + "?unit=" + encodeURIComponent(filterValue);
        url += "&unit=" + encodeURIComponent(filterValue);
    } else if (filterType === 'priority') {
        viewAllBtn.href = adminAllTicketsUrl + "?priority=" + encodeURIComponent(filterValue);
        url += "&priority=" + encodeURIComponent(filterValue);
    } else if (filterType === 'errorType') {
        viewAllBtn.href = adminAllTicketsUrl + "?main_error_type=" + encodeURIComponent(filterValue) + "&status=Closed";
        url += "&main_error_type=" + encodeURIComponent(filterValue) + "&status=Closed";
        statusLabel.textContent = 'Main Error: ' + filterValue + ' (Closed Tickets)';
    } else if (filterType === 'subErrorType') {
        viewAllBtn.href = adminAllTicketsUrl + "?sub_error_type=" + encodeURIComponent(filterValue) + "&status=Closed";
        url += "&sub_error_type=" + encodeURIComponent(filterValue) + "&status=Closed";
        statusLabel.textContent = 'Sub Error: ' + filterValue + ' (Closed Tickets)';
    } else {
        viewAllBtn.href = adminAllTicketsUrl;
    }

    modalBody.innerHTML = `
        <div class="modal-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading tickets...</p>
        </div>
    `;

    modal.show();

    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function(response) {
        if (!response.ok) throw new Error('Server returned ' + response.status);
        return response.json();
    })
    .then(function(data) {
        if (data.success === false) throw new Error(data.message || 'Server error');
        if (data.html) {
            modalBody.innerHTML = data.html;
            if (data.count !== undefined) {
                statusLabel.textContent = filterLabel + ` (${data.count})`;
            }
        } else {
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: var(--text-muted);">
                    <i class="fa-solid fa-receipt fa-2x mb-2 d-block opacity-25" style="color: var(--brand-orange);"></i>
                    <p>No tickets found</p>
                </div>
            `;
        }
    })
    .catch(function(error) {
        modalBody.innerHTML = `
            <div class="text-center py-4" style="color: #EF4444;">
                <i class="fa-solid fa-circle-exclamation fa-2x mb-2 d-block"></i>
                <p><strong>Error loading tickets</strong></p>
                <p style="font-size: 0.85rem; color: var(--text-muted);">${error.message || 'Please try again.'}</p>
                <button class="btn btn-primary-custom btn-sm mt-2" onclick="drillDownWithFilter('${filterType}', '${filterValue}', '${filterLabel}')">
                    <i class="fa-solid fa-rotate me-1"></i>Retry
                </button>
            </div>
        `;
    });
}

function forceCleanupBackdrops() {
    document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
        backdrop.remove();
    });
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
}