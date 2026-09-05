/* ============================================================
   UNIT HEAD DASHBOARD JAVASCRIPT - FIXED
   ============================================================ */

(function() {
    'use strict';

    // ============================================================
    // DOM READY
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {

        // ------------------------------------------------------------
        // Cleanup helper for modal backdrops
        // ------------------------------------------------------------
        function forceCleanupBackdrops() {
            document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                backdrop.remove();
            });
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }

        // ------------------------------------------------------------
        // Load Chart Data from JSON script tag
        // ------------------------------------------------------------
        let chartsData = {};
        try {
            const dataElement = document.getElementById('charts-data');
            if (dataElement) {
                chartsData = JSON.parse(dataElement.textContent);
            }
        } catch (e) {
            console.error('Error parsing chart data:', e);
        }

        const hasStatusData = chartsData.status && Object.keys(chartsData.status).length > 0;
        const hasPriorityData = chartsData.priority && Object.keys(chartsData.priority).length > 0;
        const hasDeptData = chartsData.department && Object.keys(chartsData.department).length > 0;

        const statusEmpty = document.getElementById('statusEmpty');
        const priorityEmpty = document.getElementById('priorityEmpty');
        const deptEmpty = document.getElementById('deptEmpty');
        const statusCanvas = document.getElementById('statusChart');
        const priorityCanvas = document.getElementById('priorityChart');
        const deptCanvas = document.getElementById('deptChart');

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#E8EDF5' : '#1A2A6C';

        // ------------------------------------------------------------
        // CHART 1: STATUS - Doughnut with Drill Down
        // ------------------------------------------------------------
        if (statusCanvas && hasStatusData) {
            const statusLabels = Object.keys(chartsData.status);
            const statusValues = Object.values(chartsData.status);
            const statusColors = {
                'Open': '#22C55E',
                'Assigned': '#3B82F6',
                'Hold': '#F59E0B',
                'Escalated': '#8B5CF6',
                'Closed': '#94A3B8'
            };
            const colors = statusLabels.map(label => statusColors[label] || '#6B7280');

            const ctx = statusCanvas.getContext('2d');
            const chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: statusLabels,
                    datasets: [{
                        data: statusValues,
                        backgroundColor: colors,
                        borderColor: isDark ? '#1A1A2E' : '#FFFFFF',
                        borderWidth: 3,
                        hoverOffset: 15
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
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                                }
                            }
                        }
                    },
                    cutout: '60%',
                    onClick: function(event, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = this.data.labels[index];
                            window.drillDownUnitTickets(label);
                        }
                    }
                }
            });
            statusCanvas.chart = chart;
        } else if (statusCanvas && statusEmpty) {
            statusCanvas.style.display = 'none';
            statusEmpty.style.display = 'flex';
        }

        // ------------------------------------------------------------
        // CHART 2: PRIORITY - Pie with Drill Down
        // ------------------------------------------------------------
        if (priorityCanvas && hasPriorityData) {
            const priorityLabels = Object.keys(chartsData.priority);
            const priorityValues = Object.values(chartsData.priority);
            const priorityColors = {
                'Critical': '#EF4444',
                'High': '#F59E0B',
                'Medium': '#3B82F6',
                'Low': '#94A3B8'
            };
            const colors = priorityLabels.map(label => priorityColors[label] || '#6B7280');

            const ctx = priorityCanvas.getContext('2d');
            const chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: priorityLabels,
                    datasets: [{
                        data: priorityValues,
                        backgroundColor: colors,
                        borderColor: isDark ? '#1A1A2E' : '#FFFFFF',
                        borderWidth: 3,
                        hoverOffset: 15
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
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                                }
                            }
                        }
                    },
                    onClick: function(event, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = this.data.labels[index];
                            window.drillDownUnitTicketsByPriority(label);
                        }
                    }
                }
            });
            priorityCanvas.chart = chart;
        } else if (priorityCanvas && priorityEmpty) {
            priorityCanvas.style.display = 'none';
            priorityEmpty.style.display = 'flex';
        }

        // ------------------------------------------------------------
        // CHART 3: DEPARTMENT DISTRIBUTION - Pie Chart
        // ------------------------------------------------------------
        const deptColors = [
            '#FF6B00', '#8B5CF6', '#3B82F6', '#22C55E', '#F59E0B',
            '#EF4444', '#EC4899', '#14B8A6', '#F97316', '#6366F1'
        ];

        if (deptCanvas && hasDeptData) {
            const deptLabels = Object.keys(chartsData.department);
            const deptValues = Object.values(chartsData.department);
            const colors = deptLabels.map((_, index) => deptColors[index % deptColors.length]);

            const ctx = deptCanvas.getContext('2d');
            const chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: deptLabels,
                    datasets: [{
                        data: deptValues,
                        backgroundColor: colors,
                        borderColor: isDark ? '#1A1A2E' : '#FFFFFF',
                        borderWidth: 3,
                        hoverOffset: 15
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
                                font: { family: 'Inter, sans-serif', size: 10, weight: '500' },
                                padding: 12,
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
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return context.label + ': ' + context.parsed + ' tickets (' + percentage + '%)';
                                }
                            }
                        }
                    },
                    onClick: function(event, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = this.data.labels[index];
                            window.drillDownUnitTicketsByDepartment(label);
                        }
                    }
                }
            });
            deptCanvas.chart = chart;
        } else if (deptCanvas && deptEmpty) {
            deptCanvas.style.display = 'none';
            deptEmpty.style.display = 'flex';
        }

        // ------------------------------------------------------------
        // CHART RESIZE HANDLER
        // ------------------------------------------------------------
        function resizeCharts() {
            document.querySelectorAll('.chart-wrapper canvas').forEach(canvas => {
                if (canvas.chart) { canvas.chart.resize(); }
            });
        }

        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(resizeCharts, 250);
        });

        // ------------------------------------------------------------
        // THEME CHANGE HANDLER for charts
        // ------------------------------------------------------------
        function updateChartColors() {
            const isDarkNow = document.documentElement.getAttribute('data-theme') === 'dark';
            const newColor = isDarkNow ? '#E8EDF5' : '#1A2A6C';

            document.querySelectorAll('.chart-wrapper canvas').forEach(canvas => {
                if (canvas.chart) {
                    const chart = canvas.chart;
                    if (chart.options.plugins && chart.options.plugins.legend) {
                        chart.options.plugins.legend.labels.color = newColor;
                        chart.update();
                    }
                }
            });
        }

        const themeToggleBtn = document.getElementById('themeToggleFloating');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', function() {
                setTimeout(updateChartColors, 150);
            });
        }

        const themeObserver = new MutationObserver(function(mutations) {
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

        // ------------------------------------------------------------
        // MODAL CLEANUP
        // ------------------------------------------------------------
        const modalEl = document.getElementById('drillDownModal');
        if (modalEl) {
            modalEl.addEventListener('hidden.bs.modal', function() {
                forceCleanupBackdrops();
            });
            modalEl.addEventListener('hide.bs.modal', function() {
                setTimeout(forceCleanupBackdrops, 50);
            });
        }

        // ------------------------------------------------------------
        // CONSOLE LOG
        // ------------------------------------------------------------
        console.log('✅ Unit Head Dashboard loaded with drill-down enabled');
        console.log('📊 Status data:', hasStatusData ? 'Available' : 'None');
        console.log('📊 Priority data:', hasPriorityData ? 'Available' : 'None');
        console.log('📊 Department data:', hasDeptData ? 'Available' : 'None');

    }); // end DOMContentLoaded

    // ================================================================
    // GLOBAL DRILL DOWN FUNCTIONS
    // ================================================================

    // ----------------------------------------------------------------
    // drillDownUnitTickets - Filter by Status
    // ----------------------------------------------------------------
    window.drillDownUnitTickets = function(status) {
        forceCleanupBackdrops();

        const modalEl = document.getElementById('drillDownModal');
        const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

        const modalBody = document.getElementById('drillDownModalBody');
        const statusLabel = document.getElementById('drillDownStatusLabel');
        const viewAllBtn = document.getElementById('drillDownViewAllBtn');

        const statusMap = {
            'all': 'All Unit Tickets',
            'Open': 'Open Tickets',
            'Assigned': 'Assigned Tickets',
            'Hold': 'Hold Tickets',
            'Escalated': 'Escalated Tickets',
            'Closed': 'Closed Tickets',
            'Critical': 'Critical Priority Tickets'
        };
        statusLabel.textContent = statusMap[status] || status || 'All Unit Tickets';

        let filterParam = 'status';
        let filterValue = status;

        if (status === 'Critical') {
            filterParam = 'priority';
            filterValue = 'Critical';
        } else if (status === 'all') {
            filterParam = '';
            filterValue = '';
        }

        // Build the "View All" button URL
        const allTicketsUrl = document.getElementById('unitHeadAllTicketsUrl');
        let baseUrl = allTicketsUrl ? allTicketsUrl.getAttribute('data-url') : '/unit-head/tickets/';

        if (filterParam && filterValue) {
            viewAllBtn.href = baseUrl + '?' + filterParam + '=' + encodeURIComponent(filterValue);
        } else {
            viewAllBtn.href = baseUrl;
        }

        modalBody.innerHTML = `
            <div class="modal-loading">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <p>Loading tickets...</p>
            </div>
        `;

        modal.show();

        let url = baseUrl + '?ajax=1';
        if (filterParam && filterValue) {
            url += '&' + filterParam + '=' + encodeURIComponent(filterValue);
        }
        url += '&_=' + Date.now();

        // ✅ FIX: Added credentials: 'same-origin' to send session cookies
        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'  // ← THIS IS THE FIX
        })
        .then(response => {
            // ✅ Handle 302/401 responses
            if (response.status === 302 || response.status === 401) {
                throw new Error('Your session has expired. Please login again.');
            }
            if (!response.ok) throw new Error('Server returned ' + response.status);
            return response.json();
        })
        .then(data => {
            if (data.success === false) throw new Error(data.message || 'Server error');
            if (data.html) {
                modalBody.innerHTML = data.html;
                if (data.count !== undefined) {
                    statusLabel.textContent = (statusMap[status] || status || 'All Unit Tickets') + ' (' + data.count + ')';
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
        .catch(error => {
            console.error('Drill-down error:', error);
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: #EF4444;">
                    <i class="fa-solid fa-circle-exclamation fa-2x mb-2 d-block"></i>
                    <p><strong>Error loading tickets</strong></p>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">${error.message || 'Please try again.'}</p>
                    <button class="btn btn-primary-custom btn-sm mt-2" onclick="window.drillDownUnitTickets('${status}')">
                        <i class="fa-solid fa-rotate me-1"></i>Retry
                    </button>
                    <a href="/login/?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-primary-custom btn-sm mt-2" style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <i class="fa-solid fa-right-to-bracket"></i> Login
                    </a>
                </div>
            `;
        });
    };

    // ----------------------------------------------------------------
    // drillDownUnitTicketsByPriority - Filter by Priority
    // ----------------------------------------------------------------
    window.drillDownUnitTicketsByPriority = function(priority) {
        forceCleanupBackdrops();

        const modalEl = document.getElementById('drillDownModal');
        const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

        const modalBody = document.getElementById('drillDownModalBody');
        const statusLabel = document.getElementById('drillDownStatusLabel');
        const viewAllBtn = document.getElementById('drillDownViewAllBtn');

        statusLabel.textContent = 'Priority: ' + priority;

        const allTicketsUrl = document.getElementById('unitHeadAllTicketsUrl');
        let baseUrl = allTicketsUrl ? allTicketsUrl.getAttribute('data-url') : '/unit-head/tickets/';

        viewAllBtn.href = baseUrl + '?priority=' + encodeURIComponent(priority);

        modalBody.innerHTML = `
            <div class="modal-loading">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <p>Loading ${priority} priority tickets...</p>
            </div>
        `;

        modal.show();

        let url = baseUrl + '?ajax=1&priority=' + encodeURIComponent(priority);
        url += '&_=' + Date.now();

        // ✅ FIX: Added credentials: 'same-origin' to send session cookies
        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'  // ← THIS IS THE FIX
        })
        .then(response => {
            // ✅ Handle 302/401 responses
            if (response.status === 302 || response.status === 401) {
                throw new Error('Your session has expired. Please login again.');
            }
            if (!response.ok) throw new Error('Server returned ' + response.status);
            return response.json();
        })
        .then(data => {
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
        .catch(error => {
            console.error('Priority drill-down error:', error);
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: #EF4444;">
                    <i class="fa-solid fa-circle-exclamation fa-2x mb-2 d-block"></i>
                    <p><strong>Error loading tickets</strong></p>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">${error.message || 'Please try again.'}</p>
                    <button class="btn btn-primary-custom btn-sm mt-2" onclick="window.drillDownUnitTicketsByPriority('${priority}')">
                        <i class="fa-solid fa-rotate me-1"></i>Retry
                    </button>
                    <a href="/login/?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-primary-custom btn-sm mt-2" style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <i class="fa-solid fa-right-to-bracket"></i> Login
                    </a>
                </div>
            `;
        });
    };

    // ----------------------------------------------------------------
    // drillDownUnitTicketsByDepartment - Filter by Department
    // ----------------------------------------------------------------
    window.drillDownUnitTicketsByDepartment = function(departmentName) {
        forceCleanupBackdrops();

        const modalEl = document.getElementById('drillDownModal');
        const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });

        const modalBody = document.getElementById('drillDownModalBody');
        const statusLabel = document.getElementById('drillDownStatusLabel');
        const viewAllBtn = document.getElementById('drillDownViewAllBtn');

        statusLabel.textContent = 'Department: ' + departmentName;

        const allTicketsUrl = document.getElementById('unitHeadAllTicketsUrl');
        let baseUrl = allTicketsUrl ? allTicketsUrl.getAttribute('data-url') : '/unit-head/tickets/';

        viewAllBtn.href = baseUrl + '?department=' + encodeURIComponent(departmentName);

        modalBody.innerHTML = `
            <div class="modal-loading">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <p>Loading ${departmentName} tickets...</p>
            </div>
        `;

        modal.show();

        let url = baseUrl + '?ajax=1&department=' + encodeURIComponent(departmentName);
        url += '&_=' + Date.now();

        console.log('Fetching department tickets:', url);

        // ✅ FIX: Added credentials: 'same-origin' to send session cookies
        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'  // ← THIS IS THE FIX
        })
        .then(response => {
            // ✅ Handle 302/401 responses
            if (response.status === 302 || response.status === 401) {
                throw new Error('Your session has expired. Please login again.');
            }
            if (!response.ok) throw new Error('Server returned ' + response.status);
            return response.json();
        })
        .then(data => {
            console.log('Department data response:', data);
            if (data.success === false) throw new Error(data.message || 'Server error');
            if (data.html) {
                modalBody.innerHTML = data.html;
                if (data.count !== undefined) {
                    statusLabel.textContent = 'Department: ' + departmentName + ' (' + data.count + ')';
                }
            } else {
                modalBody.innerHTML = `
                    <div class="text-center py-4" style="color: var(--text-muted);">
                        <i class="fa-solid fa-receipt fa-2x mb-2 d-block opacity-25" style="color: var(--brand-orange);"></i>
                        <p>No tickets found for department: ${departmentName}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Department drill-down error:', error);
            modalBody.innerHTML = `
                <div class="text-center py-4" style="color: #EF4444;">
                    <i class="fa-solid fa-circle-exclamation fa-2x mb-2 d-block"></i>
                    <p><strong>Error loading tickets</strong></p>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">${error.message || 'Please try again.'}</p>
                    <button class="btn btn-primary-custom btn-sm mt-2" onclick="window.drillDownUnitTicketsByDepartment('${departmentName}')">
                        <i class="fa-solid fa-rotate me-1"></i>Retry
                    </button>
                    <a href="/login/?next=${encodeURIComponent(window.location.pathname)}" class="btn btn-primary-custom btn-sm mt-2" style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <i class="fa-solid fa-right-to-bracket"></i> Login
                    </a>
                </div>
            `;
        });
    };

    // ----------------------------------------------------------------
    // Helper: forceCleanupBackdrops (also available globally)
    // ----------------------------------------------------------------
    function forceCleanupBackdrops() {
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    // Make it globally available
    window.forceCleanupBackdrops = forceCleanupBackdrops;

})(); // end IIFE