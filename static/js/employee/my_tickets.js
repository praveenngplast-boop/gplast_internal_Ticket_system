document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const filterForm  = document.getElementById('filterForm');
    const clearBtn    = document.getElementById('clearFilters');
    const toggleBtn   = document.getElementById('tkFiltersToggle');
    const filtersBox  = document.getElementById('tkFilters');
    const filterCount = document.getElementById('tkFilterCount');

    const mainErrorSelect = document.getElementById('filterMainError');
    const subErrorSelect  = document.getElementById('filterSubError');

    /* ------------------------------------------------------------
       Sub Error cascade
       ------------------------------------------------------------ */
    const allSubOptions = [];
    if (subErrorSelect) {
        subErrorSelect.querySelectorAll('option').forEach(function (opt) {
            if (opt.value !== '') {
                allSubOptions.push({
                    value: opt.value,
                    text: opt.textContent,
                    mainType: opt.getAttribute('data-main') || ''
                });
            }
        });
    }

    function updateSubErrorOptions() {
        if (!mainErrorSelect || !subErrorSelect) return;

        const selectedMain = mainErrorSelect.value;
        const currentValue = subErrorSelect.value;

        subErrorSelect.innerHTML = '<option value="">All</option>';

        let filtered = allSubOptions;
        if (selectedMain === 'Roadmap Error' || selectedMain === 'GPL Error') {
            filtered = allSubOptions.filter(o => o.mainType === selectedMain);
        }

        filtered.forEach(function (o) {
            const option = document.createElement('option');
            option.value = o.value;
            option.textContent = o.text;
            option.setAttribute('data-main', o.mainType);
            if (o.value === currentValue) option.selected = true;
            subErrorSelect.appendChild(option);
        });
    }

    if (mainErrorSelect) {
        mainErrorSelect.addEventListener('change', updateSubErrorOptions);
    }

    /* ------------------------------------------------------------
       Collapsible advanced filters
       ------------------------------------------------------------ */
    const ADV_KEY = 'tk_filters_open';

    function countActive() {
        if (!filterForm) return 0;
        let n = 0;
        filterForm.querySelectorAll('select, input[type="text"], input[type="date"]').forEach(function (el) {
            if (el.name === 'search' && !el.value.trim()) return; // empty search doesn't count
            if (el.value && el.value.trim() !== '') n++;
        });
        return n;
    }

    function refreshCount() {
        if (!filterCount) return;
        const n = countActive();
        filterCount.textContent = n;
        filterCount.style.display = n > 0 ? 'inline-block' : 'none';
    }

    // Auto-open if there are active advanced filters or user preference
    const activeCount = countActive();
    if (activeCount > 0 || localStorage.getItem(ADV_KEY) === '1') {
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
       Clear all filters
       ------------------------------------------------------------ */
    if (clearBtn) {
        clearBtn.addEventListener('click', function (e) {
            e.preventDefault();
            filterForm.querySelectorAll('input, select').forEach(function (field) {
                if (field.name) field.value = '';
            });
            filterForm.submit();
        });
    }

    /* ------------------------------------------------------------
       Date validation
       ------------------------------------------------------------ */
    if (filterForm) {
        filterForm.addEventListener('submit', function (e) {
            const df = filterForm.querySelector('input[name="date_from"]');
            const dt = filterForm.querySelector('input[name="date_to"]');
            if (df && dt && df.value && dt.value && new Date(df.value) > new Date(dt.value)) {
                e.preventDefault();
                alert('The "From Date" cannot be later than the "To Date".');
                df.focus();
            }
        });
    }

    /* ------------------------------------------------------------
       Card click → navigate (unless clicking a link)
       ------------------------------------------------------------ */
    document.querySelectorAll('.tk-card[data-url]').forEach(function (card, i) {
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