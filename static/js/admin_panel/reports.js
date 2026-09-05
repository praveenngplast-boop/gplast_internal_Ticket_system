document.addEventListener('DOMContentLoaded', function() {
    var filterForm = document.getElementById('filterForm');
    var unitSelect = document.getElementById('id_unit');
    var deptSelect = document.getElementById('id_department');
    var categoryInput = document.getElementById('categoryInput');
    var quickFilterBtns = document.querySelectorAll('.quick-filter-btn');

    // Dynamic Sub Error Type based on Main Error Type
    var mainErrorTypeSelect = document.getElementById('id_main_error_type');
    var subErrorTypeSelect = document.getElementById('id_sub_error_type');

    // Store all options with their data-main attribute
    var allSubErrorOptions = [];
    var allOptions = subErrorTypeSelect.querySelectorAll('option');
    allOptions.forEach(function(opt) {
        if (opt.value !== '') {
            allSubErrorOptions.push({
                value: opt.value,
                text: opt.textContent,
                mainType: opt.getAttribute('data-main') || '',
                selected: opt.selected
            });
        }
    });

    // Function to update sub-error options based on main error type
    function updateSubErrorOptions() {
        var selectedMain = mainErrorTypeSelect.value;
        var currentValue = subErrorTypeSelect.value;

        // Clear current options (keep "All")
        subErrorTypeSelect.innerHTML = '<option value="">All</option>';

        // Filter options based on selected main error type
        var filteredOptions = [];
        if (selectedMain === 'Roadmap Error') {
            filteredOptions = allSubErrorOptions.filter(function(opt) {
                return opt.mainType === 'Roadmap Error';
            });
        } else if (selectedMain === 'GPL Error') {
            filteredOptions = allSubErrorOptions.filter(function(opt) {
                return opt.mainType === 'GPL Error';
            });
        } else {
            // Show all options
            filteredOptions = allSubErrorOptions;
        }

        // Add filtered options to the select
        filteredOptions.forEach(function(opt) {
            var option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.text;
            option.setAttribute('data-main', opt.mainType);
            if (opt.value === currentValue) {
                option.selected = true;
            }
            subErrorTypeSelect.appendChild(option);
        });
    }

    // Run on page load to set initial state
    setTimeout(updateSubErrorOptions, 50);

    // Update when Main Error Type changes
    if (mainErrorTypeSelect) {
        mainErrorTypeSelect.addEventListener('change', function() {
            updateSubErrorOptions();
        });
    }

    function loadDepartments(unitId, selectedDeptId) {
        if (!unitId) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            deptSelect.disabled = true;
            return;
        }

        deptSelect.disabled = true;
        deptSelect.innerHTML = '<option value="">Loading...</option>';

        fetch('/ajax/get-departments/?unit_id=' + unitId, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            if (data.departments && data.departments.length) {
                data.departments.forEach(function(dept) {
                    var opt = document.createElement('option');
                    opt.value = dept.id;
                    opt.textContent = dept.name;
                    if (selectedDeptId && dept.id == selectedDeptId) {
                        opt.selected = true;
                    }
                    deptSelect.appendChild(opt);
                });
                deptSelect.disabled = false;
            } else {
                deptSelect.innerHTML += '<option value="">No departments available</option>';
            }
        })
        .catch(function() {
            deptSelect.innerHTML = '<option value="">Error loading departments</option>';
            deptSelect.disabled = true;
        });
    }

    var initialUnitId = unitSelect.value;
    var initialDeptId = '{{ selected_department|default:"" }}';

    if (initialUnitId) {
        loadDepartments(initialUnitId, initialDeptId);
    } else {
        deptSelect.disabled = true;
    }

    unitSelect.addEventListener('change', function() {
        loadDepartments(this.value, '');
    });

    quickFilterBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var url = new URL(this.href);
            var category = url.searchParams.get('category');
            if (categoryInput) {
                categoryInput.value = category;
            }
            // Preserve error type values before submitting
            if (mainErrorTypeSelect && mainErrorTypeSelect.value) {
                var currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('main_error_type', mainErrorTypeSelect.value);
                if (subErrorTypeSelect && subErrorTypeSelect.value) {
                    currentUrl.searchParams.set('sub_error_type', subErrorTypeSelect.value);
                }
                window.location.href = currentUrl.toString();
                return;
            }
            filterForm.submit();
        });
    });

    var rows = document.querySelectorAll('#reportsTable tbody tr');
    rows.forEach(function(row, index) {
        if (row.querySelector('.empty-state')) return;
        row.style.opacity = '0';
        row.style.animation = 'fadeIn 0.3s ease forwards';
        row.style.animationDelay = (index * 0.04) + 's';
    });

    function updateThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.filter-input, .filter-select');
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