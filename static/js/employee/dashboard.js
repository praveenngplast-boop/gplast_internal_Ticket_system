// ============================================================
// FORCE CLEANUP BACKDROPS - SINGLE DEFINITION
// ============================================================
function forceCleanupBackdrops() {
    document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
        backdrop.remove();
    });
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
}

// ============================================================
// MAIN - DOM CONTENT LOADED
// ============================================================
document.addEventListener('DOMContentLoaded', function() {

    // Load Chart Data
    var chartsData = {};
    try {
        var dataElement = document.getElementById('charts-data');
        if (dataElement) {
            chartsData = JSON.parse(dataElement.textContent);
        }
    } catch (e) {
        console.error('Error parsing chart data:', e);
    }

    var hasStatusData = chartsData.dept_status && Object.keys(chartsData.dept_status).length > 0;
    var hasPriorityData = chartsData.dept_priority && Object.keys(chartsData.dept_priority).length > 0;

    var statusEmpty = document.getElementById('deptStatusEmpty');
    var priorityEmpty = document.getElementById('deptPriorityEmpty');
    var statusCanvas = document.getElementById('deptStatusChart');
    var priorityCanvas = document.getElementById('deptPriorityChart');

    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    var textColor = isDark ? '#E8EDF5' : '#1A2A6C';

    // Chart 1: Status
    if (statusCanvas && hasStatusData) {
        var statusLabels = Object.keys(chartsData.dept_status);
        var statusValues = Object.values(chartsData.dept_status);
        var statusColors = {
            'Open': '#22C55E',
            'Assigned': '#3B82F6',
            'Hold': '#F59E0B',
            'Escalated': '#8B5CF6',
            'Closed': '#94A3B8'
        };
        var colors = statusLabels.map(function(label) {
            return statusColors[label] || '#6B7280';
        });

        var ctx = statusCanvas.getContext('2d');
        var chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: statusLabels,
                datasets: [{
                    data: statusValues,
                    backgroundColor: colors,
                    borderColor: isDark ? '#1A1A2E' : '#FFFFFF',
                    borderWidth: 3,
                    hoverOffset: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            font: { family: 'Inter, sans-serif', size: 11, weight: '500' },
                            padding: 14,
                            color: textColor,
                            usePointStyle: true,
                            pointStyleWidth: 12,
                            boxWidth: 14,
                            boxHeight: 14
                        }
                    },
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
                cutout: '60%',
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        var index = elements[0].index;
                        var label = this.data.labels[index];
                        drillDownTickets(label);
                    }
                }
            }
        });
        statusCanvas.chart = chart;
    } else if (statusCanvas && statusEmpty) {
        statusCanvas.style.display = 'none';
        statusEmpty.style.display = 'flex';
    }

    // Chart 2: Priority
    if (priorityCanvas && hasPriorityData) {
        var priorityLabels = Object.keys(chartsData.dept_priority);
        var priorityValues = Object.values(chartsData.dept_priority);
        var priorityColors = {
            'Critical': '#EF4444',
            'High': '#F59E0B',
            'Medium': '#3B82F6',
            'Low': '#94A3B8'
        };
        var colors = priorityLabels.map(function(label) {
            return priorityColors[label] || '#6B7280';
        });

        var ctx = priorityCanvas.getContext('2d');
        var chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: priorityLabels,
                datasets: [{
                    data: priorityValues,
                    backgroundColor: colors,
                    borderColor: isDark ? '#1A1A2E' : '#FFFFFF',
                    borderWidth: 3,
                    hoverOffset: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            font: { family: 'Inter, sans-serif', size: 11, weight: '500' },
                            padding: 14,
                            color: textColor,
                            usePointStyle: true,
                            pointStyleWidth: 12,
                            boxWidth: 14,
                            boxHeight: 14
                        }
                    },
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
                onClick: function(event, elements) {
                    if (elements.length > 0) {
                        var index = elements[0].index;
                        var label = this.data.labels[index];
                        drillDownTicketsByPriority(label);
                    }
                }
            }
        });
        priorityCanvas.chart = chart;
    } else if (priorityCanvas && priorityEmpty) {
        priorityCanvas.style.display = 'none';
        priorityEmpty.style.display = 'flex';
    }

    // Chart resize handler
    function resizeCharts() {
        document.querySelectorAll('.chart-wrapper canvas').forEach(function(canvas) {
            if (canvas.chart) { canvas.chart.resize(); }
        });
    }

    var resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(resizeCharts, 250);
    });

    // Theme change handler for charts
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

    // Modal cleanup
    var modalEl = document.getElementById('drillDownModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', function() {
            forceCleanupBackdrops();
        });
        modalEl.addEventListener('hide.bs.modal', function() {
            setTimeout(forceCleanupBackdrops, 50);
        });
    }

    // Make functions global
    window.drillDownTickets = drillDownTickets;
    window.drillDownTicketsByPriority = drillDownTicketsByPriority;

    console.log('✅ Employee Dashboard loaded');
    console.log('📊 Status data:', hasStatusData ? 'Available' : 'None');
    console.log('📊 Priority data:', hasPriorityData ? 'Available' : 'None');
});

// ============================================================
// DRILL DOWN FUNCTIONS
// ============================================================

function drillDownTickets(status) {
    forceCleanupBackdrops();

    var modalEl = document.getElementById('drillDownModal');
    var modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

    var modalBody = document.getElementById('drillDownModalBody');
    var statusLabel = document.getElementById('drillDownStatusLabel');
    var viewAllBtn = document.getElementById('drillDownViewAllBtn');

    var statusMap = {
        'all': 'All Tickets',
        'Open': 'Open Tickets',
        'Assigned': 'Assigned Tickets',
        'Hold': 'Hold Tickets',
        'Escalated': 'Escalated Tickets',
        'Closed': 'Closed Tickets',
        'Critical': 'Critical Priority Tickets'
    };
    statusLabel.textContent = statusMap[status] || status || 'All Tickets';

    var filterParam = 'status';
    var filterValue = status;

    if (status === 'Critical') {
        filterParam = 'priority';
        filterValue = 'Critical';
    } else if (status === 'all') {
        filterParam = '';
        filterValue = '';
    }

    if (filterParam && filterValue) {
        viewAllBtn.href = "/my-tickets/?" + filterParam + "=" + encodeURIComponent(filterValue);
    } else {
        viewAllBtn.href = "/my-tickets/";
    }

    modalBody.innerHTML = `
        <div class="modal-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading tickets...</p>
        </div>
    `;

    modal.show();

    var url = "/my-tickets/?ajax=1";
    if (filterParam && filterValue) {
        url += "&" + filterParam + "=" + encodeURIComponent(filterValue);
    }
    url += "&_=" + Date.now();

    // ✅ FIX: Added credentials: 'same-origin' to send session cookies
    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'  // ← THIS IS THE FIX
    })
    .then(function(response) {
        // ✅ Handle 401/302 responses properly
        if (response.status === 401 || response.status === 302) {
            throw new Error('Your session has expired. Please refresh the page and login again.');
        }
        if (!response.ok) throw new Error('Server returned ' + response.status);
        return response.json();
    })
    .then(function(data) {
        if (data.success === false) throw new Error(data.message || 'Server error');
        if (data.html) {
            modalBody.innerHTML = data.html;
            if (data.count !== undefined) {
                statusLabel.textContent = (statusMap[status] || status || 'All Tickets') + ' (' + data.count + ')';
            }
        } else {
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: var(--text-muted);">
                    <i class="fa-solid fa-receipt fa-2x mb-2 d-block opacity-25" style="color: var(--brand-orange);"></i>
                    <p>No tickets found with status: ${statusLabel.textContent}</p>
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
                <button class="btn btn-primary-custom btn-sm mt-2" onclick="drillDownTickets('${status}')">
                    <i class="fa-solid fa-rotate me-1"></i>Retry
                </button>
                <a href="/login/?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-primary-custom btn-sm mt-2" style="display: inline-flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-right-to-bracket"></i> Login
                </a>
            </div>
        `;
    });
}

function drillDownTicketsByPriority(priority) {
    forceCleanupBackdrops();

    var modalEl = document.getElementById('drillDownModal');
    var modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

    var modalBody = document.getElementById('drillDownModalBody');
    var statusLabel = document.getElementById('drillDownStatusLabel');
    var viewAllBtn = document.getElementById('drillDownViewAllBtn');

    statusLabel.textContent = 'Priority: ' + priority;
    viewAllBtn.href = "/my-tickets/?priority=" + encodeURIComponent(priority);

    modalBody.innerHTML = `
        <div class="modal-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading ${priority} priority tickets...</p>
        </div>
    `;

    modal.show();

    var url = "/my-tickets/?ajax=1&priority=" + encodeURIComponent(priority);
    url += "&_=" + Date.now();

    // ✅ FIX: Added credentials: 'same-origin' to send session cookies
    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'  // ← THIS IS THE FIX
    })
    .then(function(response) {
        // ✅ Handle 401/302 responses properly
        if (response.status === 401 || response.status === 302) {
            throw new Error('Your session has expired. Please refresh the page and login again.');
        }
        if (!response.ok) throw new Error('Server returned ' + response.status);
        return response.json();
    })
    .then(function(data) {
        if (data.success === false) throw new Error(data.message || 'Server error');
        if (data.html) {
            modalBody.innerHTML = data.html;
            if (data.count !== undefined) {
                statusLabel.textContent = 'Priority: ' + priority + ' (' + data.count + ')';
            }
        } else {
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: var(--text-muted);">
                    <i class="fa-solid fa-receipt fa-2x mb-2 d-block opacity-25" style="color: var(--brand-orange);"></i>
                    <p>No ${priority} priority tickets found</p>
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
                <button class="btn btn-primary-custom btn-sm mt-2" onclick="drillDownTicketsByPriority('${priority}')">
                    <i class="fa-solid fa-rotate me-1"></i>Retry
                </button>
                <a href="/login/?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-primary-custom btn-sm mt-2" style="display: inline-flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-right-to-bracket"></i> Login
                </a>
            </div>
        `;
    });
}