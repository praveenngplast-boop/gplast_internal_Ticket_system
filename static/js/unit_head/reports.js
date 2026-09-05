/* ============================================================
   UNIT HEAD REPORTS JAVASCRIPT
   ============================================================ */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {

        // ============================================================
        // AUTO-SUBMIT ON FILTER CHANGE
        // ============================================================
        var filterForm = document.getElementById('filterForm');
        if (!filterForm) return;

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
        // DATE INPUTS - Auto submit on change
        // ============================================================
        var dateFrom = document.getElementById('date_from');
        var dateTo = document.getElementById('date_to');

        if (dateFrom) {
            dateFrom.addEventListener('change', function() {
                filterForm.submit();
            });
        }

        if (dateTo) {
            dateTo.addEventListener('change', function() {
                filterForm.submit();
            });
        }

        // ============================================================
        // THEME SYNC FOR FORM CONTROLS
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

        // Initial theme sync
        setTimeout(updateTheme, 200);

        // ============================================================
        // TABLE ROW HOVER EFFECT - already handled by CSS
        // ============================================================
        // No additional JS needed

        // ============================================================
        // EXPORT BUTTON - Track clicks for analytics (optional)
        // ============================================================
        var exportBtn = document.querySelector('.btn-uh-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', function() {
                console.log('📊 Unit Head Reports: Exporting to Excel');
                // You can add analytics tracking here
            });
        }

        console.log('✅ Unit Head Reports loaded with auto-filter and theme sync');
        console.log('📋 Report filters:', {
            status: document.getElementById('status')?.value || 'All',
            priority: document.getElementById('priority')?.value || 'All',
            department: document.getElementById('department')?.value || 'All',
            search: document.getElementById('search')?.value || ''
        });

    });

})();