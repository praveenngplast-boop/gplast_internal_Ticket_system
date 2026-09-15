(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        const filterForm  = document.getElementById('filterForm');
        if (!filterForm) return;

        const searchInput = document.getElementById('search');
        const dateFrom    = document.getElementById('date_from');
        const dateTo      = document.getElementById('date_to');
        const filtersBox  = document.getElementById('uhFilters');
        const toggleBtn   = document.getElementById('uhFiltersToggle');
        const filterCount = document.getElementById('uhFilterCount');

        /* ------------------------------------------------------------
           Auto-submit on select change
           ------------------------------------------------------------ */
        filterForm.querySelectorAll('select').forEach(function (sel) {
            sel.addEventListener('change', function () {
                filterForm.submit();
            });
        });

        /* ------------------------------------------------------------
           Debounced search
           ------------------------------------------------------------ */
        let searchTimeout;
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(function () {
                    filterForm.submit();
                }, 500);
            });
        }

        /* ------------------------------------------------------------
           Date auto-submit with validation
           ------------------------------------------------------------ */
        [dateFrom, dateTo].forEach(function (el) {
            if (el) {
                el.addEventListener('change', function () {
                    if (dateFrom && dateTo && dateFrom.value && dateTo.value
                        && new Date(dateFrom.value) > new Date(dateTo.value)) {
                        alert('The "Date From" cannot be later than the "Date To".');
                        el.focus();
                        return;
                    }
                    filterForm.submit();
                });
            }
        });

        /* ------------------------------------------------------------
           Collapsible filter panel + active count
           ------------------------------------------------------------ */
        const ADV_KEY = 'uhr_filters_open';

        function countActive() {
            let n = 0;
            filterForm.querySelectorAll('select').forEach(function (el) {
                if (el.value && el.value.trim() !== '') n++;
            });
            if (searchInput && searchInput.value.trim() !== '') n++;
            if (dateFrom && dateFrom.value) n++;
            if (dateTo && dateTo.value) n++;
            return n;
        }

        function refreshCount() {
            if (!filterCount) return;
            const n = countActive();
            filterCount.textContent = n;
            filterCount.style.display = n > 0 ? 'inline-block' : 'none';
        }

        if (countActive() > 0 || localStorage.getItem(ADV_KEY) === '1') {
            filtersBox.classList.add('open');
        }

        if (toggleBtn) {
            toggleBtn.addEventListener('click', function () {
                filtersBox.classList.toggle('open');
                localStorage.setItem(ADV_KEY, filtersBox.classList.contains('open') ? '1' : '0');
            });
        }

        refreshCount();

        /* ------------------------------------------------------------
           Card click → navigate (unless clicking inner link)
           ------------------------------------------------------------ */
        document.querySelectorAll('.uh-card[data-url]').forEach(function (card, i) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(8px)';
            card.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
            setTimeout(function () {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, Math.min(i * 25, 300));

            card.addEventListener('click', function (e) {
                if (e.target.closest('a')) return;
                const url = this.getAttribute('data-url');
                if (url) window.location.href = url;
            });
        });
    });

})();