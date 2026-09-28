document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const filterForm      = document.getElementById('filterForm');
    const unitSelect      = document.getElementById('id_unit');
    const deptSelect      = document.getElementById('id_department');
    const categoryInput   = document.getElementById('categoryInput');
    const quickFilterBtns = document.querySelectorAll('.rp-quick a');

    const mainErrorTypeSelect = document.getElementById('id_main_error_type');
    const subErrorTypeSelect  = document.getElementById('id_sub_error_type');

    const filtersBox   = document.getElementById('rpFilters');
    const filtersBtn   = document.getElementById('rpFiltersToggle');
    const filterCount  = document.getElementById('rpFilterCount');

    /* ------------------------------------------------------------
       Sub Error Type cascade
       Reads all options once on load, then filters them by main.
       Works for ANY main error type (not just Roadmap/GPL).
       ------------------------------------------------------------ */
    const allSubErrorOptions = [];
    if (subErrorTypeSelect) {
        subErrorTypeSelect.querySelectorAll('option').forEach(function (opt) {
            if (opt.value !== '') {
                allSubErrorOptions.push({
                    value: opt.value,
                    text: opt.textContent,
                    mainType: opt.getAttribute('data-main') || ''
                });
            }
        });
    }

    function updateSubErrorOptions() {
        if (!subErrorTypeSelect || !mainErrorTypeSelect) return;

        const selectedMain = mainErrorTypeSelect.value;
        const currentValue = subErrorTypeSelect.value;

        // Rebuild the sub dropdown from scratch
        subErrorTypeSelect.innerHTML = '<option value="">All</option>';

        // If a specific main is selected, filter to that main only.
        // If no main is selected, show every sub.
        let filtered = allSubErrorOptions;
        if (selectedMain) {
            filtered = allSubErrorOptions.filter(function (o) {
                return o.mainType === selectedMain;
            });
        }

        filtered.forEach(function (o) {
            const option = document.createElement('option');
            option.value = o.value;
            option.textContent = o.text;
            option.setAttribute('data-main', o.mainType);
            // Preserve current selection if it still exists in the filtered set
            if (o.value === currentValue) option.selected = true;
            subErrorTypeSelect.appendChild(option);
        });
    }

    if (mainErrorTypeSelect) {
        // Run once on page load to sync with any pre-selected main
        setTimeout(updateSubErrorOptions, 0);
        mainErrorTypeSelect.addEventListener('change', updateSubErrorOptions);
    }

    /* ------------------------------------------------------------
       Unit → Department cascade
       ------------------------------------------------------------ */
    const selectedDepartment = '{{ selected_department|default:"" }}';

    function loadDepartments(unitId, selectedDeptId) {
        if (!deptSelect) return;

        if (!unitId) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            deptSelect.disabled = false;
            return;
        }

        deptSelect.disabled = true;
        deptSelect.innerHTML = '<option value="">Loading…</option>';

        fetch('/ajax/get-departments/?unit_id=' + encodeURIComponent(unitId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(r => r.json())
        .then(function (data) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            if (data.departments && data.departments.length) {
                data.departments.forEach(function (dept) {
                    const opt = document.createElement('option');
                    opt.value = dept.id;
                    opt.textContent = dept.name;
                    if (selectedDeptId && String(dept.id) === String(selectedDeptId)) {
                        opt.selected = true;
                    }
                    deptSelect.appendChild(opt);
                });
            } else {
                const opt = document.createElement('option');
                opt.value = '';
                opt.textContent = 'No departments available';
                deptSelect.appendChild(opt);
            }
            deptSelect.disabled = false;
        })
        .catch(function () {
            deptSelect.innerHTML = '<option value="">Error loading departments</option>';
            deptSelect.disabled = false;
        });
    }

    if (unitSelect && deptSelect) {
        const initialUnit = unitSelect.value;
        if (initialUnit) {
            loadDepartments(initialUnit, selectedDepartment);
        } else {
            deptSelect.disabled = false;
        }
        unitSelect.addEventListener('change', function () {
            loadDepartments(this.value, '');
        });
    }

    /* ------------------------------------------------------------
       Quick pills — preserve error values
       ------------------------------------------------------------ */
    quickFilterBtns.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const url = new URL(this.href, window.location.origin);
            const category = url.searchParams.get('category') || 'all';

            if (categoryInput) categoryInput.value = category;

            if (mainErrorTypeSelect && mainErrorTypeSelect.value) {
                appendHidden('main_error_type', mainErrorTypeSelect.value);
            }
            if (subErrorTypeSelect && subErrorTypeSelect.value) {
                appendHidden('sub_error_type', subErrorTypeSelect.value);
            }

            filterForm.submit();
        });
    });

    function appendHidden(name, value) {
        const existing = filterForm.querySelector('input[data-temp="' + name + '"]');
        if (existing) existing.remove();
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        input.setAttribute('data-temp', name);
        filterForm.appendChild(input);
    }

    /* ------------------------------------------------------------
       Collapsible advanced filters
       ------------------------------------------------------------ */
    const ADV_KEY = 'rp_filters_open';

    // Auto-open if there are active advanced filters OR user preference
    const hasActiveAdvanced = countActiveFilters() > 0;
    if (hasActiveAdvanced || localStorage.getItem(ADV_KEY) === '1') {
        filtersBox.classList.add('open');
    }

    filtersBtn.addEventListener('click', function () {
        filtersBox.classList.toggle('open');
        localStorage.setItem(ADV_KEY, filtersBox.classList.contains('open') ? '1' : '0');
    });

    /* ------------------------------------------------------------
       Active filter count
       ------------------------------------------------------------ */
    function countActiveFilters() {
        if (!filterForm) return 0;
        let count = 0;

        const cat = categoryInput ? categoryInput.value : '';
        if (cat && cat !== 'all') count++;

        filterForm.querySelectorAll('select, input[type="text"], input[type="date"]').forEach(function (el) {
            if (el.type === 'hidden') return;
            if (el.name === 'per_page') return;
            if (el.name === 'vendor_ticket_number' && !el.value.trim()) return; // skip empty search
            if (el.value && el.value.trim() !== '') count++;
        });
        return count;
    }

    function refreshFilterCount() {
        if (!filterCount) return;
        const n = countActiveFilters();
        filterCount.textContent = n;
        filterCount.style.display = n > 0 ? 'inline-block' : 'none';
    }

    refreshFilterCount();

    /* ------------------------------------------------------------
       Card entrance animation
       ------------------------------------------------------------ */
    document.querySelectorAll('.rp-card').forEach(function (card, i) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(8px)';
        card.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
        setTimeout(function () {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, Math.min(i * 25, 300));
    });
});