/* ============================================================
   Reports — Chart.js rendering
   File: js/admin_view/reports.js
   ============================================================ */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        /* ------------------------------------------------------
           Read JSON payloads rendered by Django's json_script
           ------------------------------------------------------ */
        var byStatusEl   = document.getElementById('by-status-data');
        var byPriorityEl = document.getElementById('by-priority-data');

        if (!byStatusEl || !byPriorityEl) return;

        var byStatus   = JSON.parse(byStatusEl.textContent || '[]');
        var byPriority = JSON.parse(byPriorityEl.textContent || '[]');

        /* ------------------------------------------------------
           Color maps
           ------------------------------------------------------ */
        var STATUS_COLORS = {
            open:      '#22C55E',
            assigned:  '#3B82F6',
            hold:      '#F59E0B',
            escalated: '#8B5CF6',
            closed:    '#94A3B8',
        };

        var PRIORITY_COLORS = {
            critical: '#EF4444',
            high:     '#F59E0B',
            medium:   '#3B82F6',
            low:      '#94A3B8',
        };

        var DEFAULT_COLOR = '#6A6A7A';

        /* ------------------------------------------------------
           Shared chart config
           ------------------------------------------------------ */
        function makeConfig(labels, data, colors, colorMap, keyLookup) {
            return {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Tickets',
                        data: data,
                        backgroundColor: data.map(function (_, i) {
                            var key = (keyLookup[i] || '').toLowerCase();
                            return colorMap[key] || colors[i] || DEFAULT_COLOR;
                        }),
                        borderRadius: 6,
                        borderSkipped: false,
                        maxBarThickness: 56,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 400 },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(10, 10, 26, 0.9)',
                            padding: 10,
                            cornerRadius: 8,
                            titleFont: { family: 'Inter', size: 12, weight: '600' },
                            bodyFont:  { family: 'Inter', size: 12 },
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.06)' },
                            ticks: {
                                font: { family: 'Inter', size: 11 },
                                precision: 0,
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { family: 'Inter', size: 11 },
                                maxRotation: 0,
                                autoSkip: false,
                            }
                        }
                    }
                }
            };
        }

        /* ------------------------------------------------------
           Status chart
           ------------------------------------------------------ */
        var statusEl = document.getElementById('avReportsStatusChart');
        if (statusEl && byStatus.length) {
            var statusKeys   = byStatus.map(function (r) { return (r.status || ''); });
            var statusLabels = statusKeys.map(function (s) {
                return s.charAt(0).toUpperCase() + s.slice(1);
            });
            var statusData   = byStatus.map(function (r) { return r.count; });

            new Chart(statusEl, makeConfig(
                statusLabels,
                statusData,
                statusData.map(function () { return DEFAULT_COLOR; }),
                STATUS_COLORS,
                statusKeys
            ));
        }

        /* ------------------------------------------------------
           Priority chart
           ------------------------------------------------------ */
        var priorityEl = document.getElementById('avReportsPriorityChart');
        if (priorityEl && byPriority.length) {
            var priorityKeys   = byPriority.map(function (r) { return (r.priority || ''); });
            var priorityLabels = priorityKeys.map(function (p) {
                return p.charAt(0).toUpperCase() + p.slice(1);
            });
            var priorityData   = byPriority.map(function (r) { return r.count; });

            new Chart(priorityEl, makeConfig(
                priorityLabels,
                priorityData,
                priorityData.map(function () { return DEFAULT_COLOR; }),
                PRIORITY_COLORS,
                priorityKeys
            ));
        }
    });
})();