document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // AUTO-SUBMIT ON FILTER CHANGE
    // ============================================================
    var filterForm = document.getElementById('filterForm');
    var filterSelects = filterForm.querySelectorAll('select');

    filterSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            filterForm.submit();
        });
    });

    // ============================================================
    // SEARCH WITH DEBOUNCE
    // ============================================================
    var searchInput = document.getElementById('search');
    var searchTimeout;

    function debounceSubmit() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            filterForm.submit();
        }, 500);
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounceSubmit);
    }

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, .form-select');
        inputs.forEach(function(input) {
            if (isDark) {
                input.style.backgroundColor = 'rgba(255,255,255,0.05)';
                input.style.borderColor = 'rgba(255,255,255,0.08)';
                input.style.color = '#E8EDF5';
                input.style.webkitTextFillColor = '#E8EDF5';
            } else {
                input.style.backgroundColor = '';
                input.style.borderColor = '';
                input.style.color = '';
                input.style.webkitTextFillColor = '';
            }
        });

        var selects = document.querySelectorAll('.form-select');
        selects.forEach(function(select) {
            var options = select.querySelectorAll('option');
            options.forEach(function(option) {
                if (isDark) {
                    option.style.backgroundColor = '#1A1A2E';
                    option.style.color = '#E8EDF5';
                } else {
                    option.style.backgroundColor = '';
                    option.style.color = '';
                }
            });
        });
    }

    var themeToggle = document.getElementById('themeToggleFloating');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            setTimeout(updateTheme, 100);
        });
    }

    var observer = new MutationObserver(function() {
        updateTheme();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
    setTimeout(updateTheme, 200);

});