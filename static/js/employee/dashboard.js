var employeeAllTicketsUrlElement = document.getElementById('employeeAllTicketsUrl');
var employeeAllTicketsUrl = employeeAllTicketsUrlElement
    ? employeeAllTicketsUrlElement.getAttribute('data-url')
    : '/all-tickets/';

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
// ✅ FIX: Define DRILL DOWN FUNCTIONS FIRST (Before Charts)
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
        viewAllBtn.href = employeeAllTicketsUrl + "?" + filterParam + "=" + encodeURIComponent(filterValue);
    } else {
        viewAllBtn.href = employeeAllTicketsUrl;
    }

    modalBody.innerHTML = `
        <div class="modal-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading tickets...</p>
        </div>
    `;

    modal.show();

    var url = employeeAllTicketsUrl + "?ajax=1";
    if (filterParam && filterValue) {
        url += "&" + filterParam + "=" + encodeURIComponent(filterValue);
    }
    url += "&_=" + Date.now();

    // ✅ FIX: Added credentials: 'same-origin' to send session cookies
    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
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
        
        // ✅ Handle both HTML and tickets data
        if (data.html) {
            modalBody.innerHTML = data.html;
            if (data.count !== undefined) {
                statusLabel.textContent = (statusMap[status] || status || 'All Tickets') + ' (' + data.count + ')';
            }
        } else if (data.tickets && data.tickets.length > 0) {
            // ✅ Handle tickets data directly
            var html = '';
            html += '<div class="table-responsive"><table class="table table-hover align-middle">';
            html += '<thead><tr>';
            html += '<th>Ticket #</th><th>Subject</th><th>Employee</th><th>Status</th><th>Priority</th>';
            html += '<th>Target Date</th>';
            html += '<th>Created</th><th>Aging</th><th>Action</th>';
            html += '</tr></thead><tbody>';
            
            data.tickets.forEach(function(ticket) {
                var statusClass = ticket.status.toLowerCase();
                var priorityClass = ticket.priority.toLowerCase();
                var targetDate = ticket.target_date ? new Date(ticket.target_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Not Set';
                var createdDate = ticket.created_at ? new Date(ticket.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '';
                
                // ✅ Calculate aging
                var createdAt = ticket.created_at ? new Date(ticket.created_at) : null;
                var ageSeconds = createdAt ? Math.max(0, (Date.now() - createdAt.getTime()) / 1000) : 0;
                var agingLabel, agingClass;
                
                if (!createdAt) {
                    agingLabel = 'N/A';
                    agingClass = 'aging-unknown';
                } else if (ageSeconds < 60) {
                    agingLabel = 'Just now';
                    agingClass = 'aging-fresh';
                } else if (ageSeconds < 3600) {
                    agingLabel = Math.floor(ageSeconds / 60) + 'm';
                    agingClass = 'aging-fresh';
                } else if (ageSeconds < 86400) {
                    var ageHours = Math.floor(ageSeconds / 3600);
                    var ageMinutes = Math.floor((ageSeconds % 3600) / 60);
                    agingLabel = ageHours + 'h' + (ageMinutes ? ' ' + ageMinutes + 'm' : '');
                    agingClass = 'aging-medium';
                } else if (ageSeconds < 2592000) {
                    var ageDays = Math.floor(ageSeconds / 86400);
                    var remainingHours = Math.floor((ageSeconds % 86400) / 3600);
                    agingLabel = ageDays + 'd' + (remainingHours ? ' ' + remainingHours + 'h' : '');
                    agingClass = 'aging-old';
                } else {
                    var ageMonths = Math.floor(ageSeconds / 2592000);
                    var remainingDays = Math.floor((ageSeconds % 2592000) / 86400);
                    agingLabel = ageMonths + 'mo' + (remainingDays ? ' ' + remainingDays + 'd' : '');
                    agingClass = 'aging-very-old';
                }
                
                html += '<tr>';
                html += '<td><strong>' + ticket.ticket_number + '</strong></td>';
                html += '<td>' + (ticket.subject ? ticket.subject.substring(0, 30) + (ticket.subject.length > 30 ? '...' : '') : '') + '</td>';
                html += '<td>' + (ticket.employee_name || 'N/A') + '</td>';
                html += '<td><span class="badge-custom badge-status-' + statusClass + '">' + ticket.status + '</span></td>';
                html += '<td><span class="badge-priority badge-priority-' + priorityClass + '">' + ticket.priority + '</span></td>';
                html += '<td><span style="font-size: 0.75rem; ' + (ticket.target_date ? 'color: var(--brand-orange); font-weight: 600;' : 'color: var(--text-muted);') + '">' + targetDate + '</span></td>';
                html += '<td style="font-size:0.65rem;">' + createdDate + '</td>';
                html += '<td><span class="aging-badge ' + agingClass + '" title="Created: ' + (ticket.created_at || '') + '">' + agingLabel + '</span></td>';
                html += '<td>';
                html += '<a href="/ticket/' + ticket.id + '/" class="btn-view btn-sm" target="_blank">';
                html += '<i class="fa-solid fa-eye"></i> View';
                html += '</a>';
                html += '</td>';
                html += '</tr>';
            });
            
            html += '</tbody></table></div>';
            html += '<div style="text-align: center; margin-top: 0.5rem; font-size: 0.7rem; color: var(--text-muted);">';
            html += '<i class="fa-regular fa-clock me-1"></i>Showing ' + data.tickets.length + ' tickets';
            html += '</div>';
            modalBody.innerHTML = html;
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
        console.error('Drill-down error:', error);
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
    viewAllBtn.href = employeeAllTicketsUrl + "?priority=" + encodeURIComponent(priority);

    modalBody.innerHTML = `
        <div class="modal-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading ${priority} priority tickets...</p>
        </div>
    `;

    modal.show();

    var url = employeeAllTicketsUrl + "?ajax=1&priority=" + encodeURIComponent(priority);
    url += "&_=" + Date.now();

    // ✅ FIX: Added credentials: 'same-origin' to send session cookies
    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
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
        
        // ✅ Handle both HTML and tickets data
        if (data.html) {
            modalBody.innerHTML = data.html;
            if (data.count !== undefined) {
                statusLabel.textContent = 'Priority: ' + priority + ' (' + data.count + ')';
            }
        } else if (data.tickets && data.tickets.length > 0) {
            // ✅ Handle tickets data directly
            var html = '';
            html += '<div class="table-responsive"><table class="table table-hover align-middle">';
            html += '<thead><tr>';
            html += '<th>Ticket #</th><th>Subject</th><th>Employee</th><th>Status</th><th>Priority</th>';
            html += '<th>Target Date</th>';
            html += '<th>Created</th><th>Aging</th><th>Action</th>';
            html += '</tr></thead><tbody>';
            
            data.tickets.forEach(function(ticket) {
                var statusClass = ticket.status.toLowerCase();
                var priorityClass = ticket.priority.toLowerCase();
                var targetDate = ticket.target_date ? new Date(ticket.target_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Not Set';
                var createdDate = ticket.created_at ? new Date(ticket.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '';
                
                // ✅ Calculate aging
                var createdAt = ticket.created_at ? new Date(ticket.created_at) : null;
                var ageSeconds = createdAt ? Math.max(0, (Date.now() - createdAt.getTime()) / 1000) : 0;
                var agingLabel, agingClass;
                
                if (!createdAt) {
                    agingLabel = 'N/A';
                    agingClass = 'aging-unknown';
                } else if (ageSeconds < 60) {
                    agingLabel = 'Just now';
                    agingClass = 'aging-fresh';
                } else if (ageSeconds < 3600) {
                    agingLabel = Math.floor(ageSeconds / 60) + 'm';
                    agingClass = 'aging-fresh';
                } else if (ageSeconds < 86400) {
                    var ageHours = Math.floor(ageSeconds / 3600);
                    var ageMinutes = Math.floor((ageSeconds % 3600) / 60);
                    agingLabel = ageHours + 'h' + (ageMinutes ? ' ' + ageMinutes + 'm' : '');
                    agingClass = 'aging-medium';
                } else if (ageSeconds < 2592000) {
                    var ageDays = Math.floor(ageSeconds / 86400);
                    var remainingHours = Math.floor((ageSeconds % 86400) / 3600);
                    agingLabel = ageDays + 'd' + (remainingHours ? ' ' + remainingHours + 'h' : '');
                    agingClass = 'aging-old';
                } else {
                    var ageMonths = Math.floor(ageSeconds / 2592000);
                    var remainingDays = Math.floor((ageSeconds % 2592000) / 86400);
                    agingLabel = ageMonths + 'mo' + (remainingDays ? ' ' + remainingDays + 'd' : '');
                    agingClass = 'aging-very-old';
                }
                
                html += '<tr>';
                html += '<td><strong>' + ticket.ticket_number + '</strong></td>';
                html += '<td>' + (ticket.subject ? ticket.subject.substring(0, 30) + (ticket.subject.length > 30 ? '...' : '') : '') + '</td>';
                html += '<td>' + (ticket.employee_name || 'N/A') + '</td>';
                html += '<td><span class="badge-custom badge-status-' + statusClass + '">' + ticket.status + '</span></td>';
                html += '<td><span class="badge-priority badge-priority-' + priorityClass + '">' + ticket.priority + '</span></td>';
                html += '<td><span style="font-size: 0.75rem; ' + (ticket.target_date ? 'color: var(--brand-orange); font-weight: 600;' : 'color: var(--text-muted);') + '">' + targetDate + '</span></td>';
                html += '<td style="font-size:0.65rem;">' + createdDate + '</td>';
                html += '<td><span class="aging-badge ' + agingClass + '" title="Created: ' + (ticket.created_at || '') + '">' + agingLabel + '</span></td>';
                html += '<td>';
                html += '<a href="/ticket/' + ticket.id + '/" class="btn-view btn-sm" target="_blank">';
                html += '<i class="fa-solid fa-eye"></i> View';
                html += '</a>';
                html += '</td>';
                html += '</tr>';
            });
            
            html += '</tbody></table></div>';
            html += '<div style="text-align: center; margin-top: 0.5rem; font-size: 0.7rem; color: var(--text-muted);">';
            html += '<i class="fa-regular fa-clock me-1"></i>Showing ' + data.tickets.length + ' tickets';
            html += '</div>';
            modalBody.innerHTML = html;
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
        console.error('Priority drill-down error:', error);
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

// ============================================================
// ✅ FIX: Make functions globally accessible BEFORE charts
// ============================================================
window.drillDownTickets = drillDownTickets;
window.drillDownTicketsByPriority = drillDownTicketsByPriority;

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
                onClick: function(event, elements, chart) {
                    if (elements.length > 0) {
                        var index = elements[0].index;
                        var label = chart.data.labels[index];
                        // ✅ Use window.drillDownTickets (already defined)
                        window.drillDownTickets(label);
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
                onClick: function(event, elements, chart) {
                    if (elements.length > 0) {
                        var index = elements[0].index;
                        var label = chart.data.labels[index];
                        // ✅ Use window.drillDownTicketsByPriority (already defined)
                        window.drillDownTicketsByPriority(label);
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

    // ✅ Check if user is authenticated on page load
    fetch('/dashboard/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
    })
    .then(function(response) {
        if (response.status === 302 || response.status === 401) {
            window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        }
    })
    .catch(function() {
        // Silent fail - don't redirect on network errors
    });

   

});