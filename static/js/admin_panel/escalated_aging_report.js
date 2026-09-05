document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // DEPARTMENT LOADING
    // ============================================================
    var unitSelect = document.getElementById('unit');
    var departmentSelect = document.getElementById('department');
    var selectedDepartment = '{{ selected_department|escapejs }}';

    function loadDepartments(unitId, selectedId) {
        if (!unitId) {
            departmentSelect.innerHTML = '<option value="">Select unit first</option>';
            departmentSelect.disabled = true;
            return;
        }
        departmentSelect.innerHTML = '<option value="">Loading departments...</option>';
        departmentSelect.disabled = true;

        var url = '/ajax/get-departments/?unit_id=' + encodeURIComponent(unitId);

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            departmentSelect.innerHTML = '<option value="">All Departments</option>';
            (data.departments || []).forEach(function(department) {
                var option = document.createElement('option');
                option.value = department.id;
                option.textContent = department.name;
                if (String(department.id) === String(selectedId)) {
                    option.selected = true;
                }
                departmentSelect.appendChild(option);
            });
            departmentSelect.disabled = false;
        })
        .catch(function() {
            departmentSelect.innerHTML = '<option value="">Unable to load departments</option>';
            departmentSelect.disabled = true;
        });
    }

    if (unitSelect) {
        unitSelect.addEventListener('change', function() {
            loadDepartments(this.value, '');
        });

        if (unitSelect.value) {
            loadDepartments(unitSelect.value, selectedDepartment);
        }
    }

    // ============================================================
    // CHART
    // ============================================================
    var canvas = document.getElementById('agingChart');
    if (canvas) {
        var labels = canvas.dataset.labels ? canvas.dataset.labels.split(',') : [];
        var values = canvas.dataset.values ? canvas.dataset.values.split(',').map(Number) : [];

        var colors = ['#22C55E', '#F59E0B', '#F97316', '#EF4444', '#991B1B'];

        if (labels.length > 0 && values.length > 0) {
            new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Tickets',
                        data: values,
                        backgroundColor: colors.slice(0, labels.length),
                        borderRadius: 6,
                        borderSkipped: false,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                                font: { size: 10, family: 'Inter' }
                            },
                            grid: {
                                color: 'rgba(0,0,0,0.04)'
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 10, family: 'Inter' }
                            }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.parsed.y + ' tickets';
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var selects = document.querySelectorAll('.aging-form select');
        var inputs = document.querySelectorAll('.aging-form input');

        selects.forEach(function(select) {
            if (isDark) {
                select.style.backgroundColor = 'rgba(255,255,255,0.05)';
                select.style.borderColor = 'rgba(255,255,255,0.08)';
                select.style.color = '#E8EDF5';
                var options = select.querySelectorAll('option');
                options.forEach(function(option) {
                    option.style.backgroundColor = '#1A1A2E';
                    option.style.color = '#E8EDF5';
                });
            } else {
                select.style.backgroundColor = '';
                select.style.borderColor = '';
                select.style.color = '';
                var options = select.querySelectorAll('option');
                options.forEach(function(option) {
                    option.style.backgroundColor = '';
                    option.style.color = '';
                });
            }
        });

        inputs.forEach(function(input) {
            if (isDark) {
                input.style.backgroundColor = 'rgba(255,255,255,0.05)';
                input.style.borderColor = 'rgba(255,255,255,0.08)';
                input.style.color = '#E8EDF5';
            } else {
                input.style.backgroundColor = '';
                input.style.borderColor = '';
                input.style.color = '';
            }
        });
    }

    var themeToggle = document.getElementById('themeToggleFloating');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            setTimeout(updateThemeStyles, 100);
        });
    }

    var observer = new MutationObserver(function() {
        updateThemeStyles();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateThemeStyles, 200);
});