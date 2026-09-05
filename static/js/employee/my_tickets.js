document.addEventListener('DOMContentLoaded', function() {
    var filterForm = document.getElementById('filterForm');
    var clearFiltersBtn = document.getElementById('clearFilters');
    var toggleAdvancedBtn = document.getElementById('toggleAdvanced');
    var filterStatus = document.getElementById('filterStatus');
    var filterPriority = document.getElementById('filterPriority');
    var filterSearch = document.getElementById('filterSearch');
    var filterTicketNumber = document.getElementById('filterTicketNumber');
    var filterDateFrom = document.getElementById('filterDateFrom');
    var filterDateTo = document.getElementById('filterDateTo');
    var ticketNumberGroup = document.getElementById('ticketNumberGroup');
    var dateFromGroup = document.getElementById('dateFromGroup');
    var dateToGroup = document.getElementById('dateToGroup');

    // Dynamic Sub Error Type based on Main Error Type
    var filterMainError = document.getElementById('filterMainError');
    var filterSubError = document.getElementById('filterSubError');

    // Store all options with their data-main attribute
    var allSubErrorOptions = [];
    var allOptions = filterSubError.querySelectorAll('option');
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
        var selectedMain = filterMainError.value;
        var currentValue = filterSubError.value;

        // Clear current options (keep "All")
        filterSubError.innerHTML = '<option value="">All</option>';

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
            filterSubError.appendChild(option);
        });

        // If no option selected and we have options, select the first one
        if (!filterSubError.value && filteredOptions.length > 0) {
            filterSubError.value = filteredOptions[0].value;
        }
    }

    // Run on page load to set initial state
    setTimeout(updateSubErrorOptions, 50);

    // Update when Main Error Type changes
    if (filterMainError) {
        filterMainError.addEventListener('change', function() {
            updateSubErrorOptions();
        });
    }

    var advancedVisible = false;

    function toggleAdvancedFields(show) {
        advancedVisible = (show !== undefined) ? show : !advancedVisible;
        
        var groups = [ticketNumberGroup, dateFromGroup, dateToGroup];
        groups.forEach(function(group) {
            group.style.display = advancedVisible ? 'flex' : 'none';
        });
        
        toggleAdvancedBtn.innerHTML = advancedVisible 
            ? '<i class="fa-solid fa-sliders-horizontal"></i> Hide Advanced'
            : '<i class="fa-solid fa-sliders-horizontal"></i> Advanced';
    }

    var hasAdvancedValue = filterTicketNumber.value || filterDateFrom.value || filterDateTo.value;
    toggleAdvancedFields(hasAdvancedValue);

    toggleAdvancedBtn.addEventListener('click', function(e) {
        e.preventDefault();
        toggleAdvancedFields();
    });

    clearFiltersBtn.addEventListener('click', function(e) {
        e.preventDefault();
        filterForm.querySelectorAll('input, select').forEach(function(field) {
            if (field.name) {
                field.value = '';
            }
        });
        filterForm.submit();
    });

    var rows = document.querySelectorAll('#ticketsTable tbody tr[data-url]');
    rows.forEach(function(row, index) {
        row.style.opacity = '0';
        row.style.animation = 'fadeIn 0.3s ease forwards';
        row.style.animationDelay = (index * 0.05) + 's';
        
        row.addEventListener('click', function(e) {
            if (!e.target.closest('.btn-view-details') && !e.target.closest('a')) {
                var url = this.getAttribute('data-url');
                if (url) {
                    window.location.href = url;
                }
            }
        });
    });

    filterForm.addEventListener('submit', function(e) {
        var dateFromValue = filterDateFrom.value;
        var dateToValue = filterDateTo.value;

        if (dateFromValue && dateToValue && new Date(dateFromValue) > new Date(dateToValue)) {
            e.preventDefault();
            alert('The "From Date" cannot be later than the "To Date". Please correct the date range.');
            filterDateFrom.focus();
            return;
        }
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