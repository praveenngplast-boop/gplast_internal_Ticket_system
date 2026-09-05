document.addEventListener('DOMContentLoaded', function() {
    var filterForm = document.getElementById('filterForm');
    var clearFiltersBtn = document.getElementById('clearFilters');
    var toggleAdvancedBtn = document.getElementById('toggleAdvanced');
    var searchInput = document.getElementById('searchInput');
    var clearSearchBtn = document.getElementById('clearSearch');
    var unitSelect = document.getElementById('id_unit');
    var deptSelect = document.getElementById('id_department');
    var deptCount = document.getElementById('deptCount');

    var ticketNumberGroup = document.getElementById('ticketNumberGroup');
    var dateFromGroup = document.getElementById('dateFromGroup');
    var dateToGroup = document.getElementById('dateToGroup');
    var filterTicketNumber = document.getElementById('id_ticket_number');
    var filterDateFrom = document.getElementById('id_date_from');
    var filterDateTo = document.getElementById('id_date_to');
    var formSearchInput = document.getElementById('id_search');

    var advancedVisible = false;

    function toggleAdvanced(show) {
        advancedVisible = (show !== undefined) ? show : !advancedVisible;
        var groups = [ticketNumberGroup, dateFromGroup, dateToGroup];
        groups.forEach(function(el) {
            if (el) el.style.display = advancedVisible ? 'flex' : 'none';
        });
        if (toggleAdvancedBtn) {
            toggleAdvancedBtn.innerHTML = advancedVisible
                ? '<i class="fa-solid fa-gear"></i> Hide Advanced'
                : '<i class="fa-solid fa-gear"></i> Advanced';
        }
    }

    var hasAdvanced = (filterTicketNumber && filterTicketNumber.value) ||
                       (filterDateFrom && filterDateFrom.value) ||
                       (filterDateTo && filterDateTo.value);
    toggleAdvanced(hasAdvanced);

    if (toggleAdvancedBtn) {
        toggleAdvancedBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleAdvanced();
        });
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            filterForm.querySelectorAll('input, select').forEach(function(field) {
                if (field.name && field.name !== 'category') {
                    if (field.tagName.toLowerCase() === 'select') {
                        field.selectedIndex = 0;
                    } else {
                        field.value = '';
                    }
                }
            });
            if (searchInput) searchInput.value = '';
            if (formSearchInput) formSearchInput.value = '';
            filterForm.submit();
        });
    }

    function loadDepartments(unitId, selectedDeptId) {
        if (!deptSelect) return;
        if (!unitId) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            deptSelect.disabled = true;
            if (deptCount) deptCount.textContent = '';
            return;
        }

        deptSelect.disabled = true;
        if (deptCount) deptCount.innerHTML = '<span class="dept-loading"></span>';
        deptSelect.innerHTML = '<option value="">Loading...</option>';

        var url = '/ajax/get-departments/?unit_id=' + unitId + '&selected_department=' + (selectedDeptId || '');

        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            if (data.departments && data.departments.length) {
                data.departments.forEach(function(dept) {
                    var opt = document.createElement('option');
                    opt.value = dept.id;
                    opt.textContent = dept.name;
                    if (selectedDeptId && dept.id == selectedDeptId) opt.selected = true;
                    deptSelect.appendChild(opt);
                });
                deptSelect.disabled = false;
                if (deptCount) {
                    deptCount.textContent = '(' + data.departments.length + ' dept' + (data.departments.length !== 1 ? 's' : '') + ')';
                }
            } else {
                deptSelect.innerHTML += '<option value="">No departments available</option>';
                if (deptCount) deptCount.textContent = '(0 depts)';
            }
        })
        .catch(function() {
            deptSelect.innerHTML = '<option value="">Error loading departments</option>';
            deptSelect.disabled = true;
            if (deptCount) deptCount.textContent = '(Error)';
        });
    }

    var initialUnitId = unitSelect ? unitSelect.value : '';
    var initialDeptId = '{{ selected_department|default:"" }}';

    if (initialUnitId) {
        loadDepartments(initialUnitId, initialDeptId);
    } else if (deptSelect) {
        deptSelect.disabled = true;
        if (deptCount) deptCount.textContent = '';
    }

    if (unitSelect) {
        unitSelect.addEventListener('change', function() {
            loadDepartments(this.value, '');
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (formSearchInput) formSearchInput.value = this.value;
            if (clearSearchBtn) clearSearchBtn.classList.toggle('visible', this.value.length > 0);
        });

        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                if (formSearchInput) formSearchInput.value = this.value;
                filterForm.submit();
            }
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchInput) {
                searchInput.value = '';
                if (formSearchInput) formSearchInput.value = '';
                filterForm.submit();
            }
        });
        clearSearchBtn.classList.toggle('visible', searchInput && searchInput.value.length > 0);
    }

    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            var from = filterDateFrom ? filterDateFrom.value : '';
            var to = filterDateTo ? filterDateTo.value : '';
            if (from && to && new Date(from) > new Date(to)) {
                e.preventDefault();
                alert('"From Date" cannot be later than "To Date".');
                if (filterDateFrom) filterDateFrom.focus();
            }
        });
    }

    var sortColumn = '';
    var sortDirection = 'asc';

    window.sortTable = function(column) {
        var tbody = document.getElementById('ticketsBody');
        var rows = Array.from(tbody.querySelectorAll('tr:not(:has(.empty-state))'));
        if (!rows.length) return;

        sortColumn = (sortColumn === column) ? column : column;
        sortDirection = (sortColumn === column && sortDirection === 'asc') ? 'desc' : 'asc';

        document.querySelectorAll('.sortable .sort-indicator').forEach(function(el) {
            el.innerHTML = '<i class="fa-solid fa-chevron-up"></i>';
            el.parentElement.classList.remove('sorted-asc', 'sorted-desc');
        });

        var header = document.getElementById('sort-' + column);
        if (header) {
            var icon = header.querySelector('.sort-indicator');
            icon.innerHTML = sortDirection === 'asc'
                ? '<i class="fa-solid fa-chevron-up"></i>'
                : '<i class="fa-solid fa-chevron-down"></i>';
            header.classList.add('sorted-' + sortDirection);
        }

        function getVal(row, col) {
            var val = row.getAttribute('data-' + col) || '';
            if (col === 'status') {
                var badge = row.querySelector('.badge-status');
                if (badge) val = badge.textContent.trim();
            } else if (col === 'unit') {
                var badge = row.querySelector('.badge-unit');
                if (badge) val = badge.textContent.trim();
            } else if (col === 'priority') {
                var badge = row.querySelector('.badge-priority');
                if (badge) val = badge.textContent.trim();
            } else if (col === 'ticket') {
                var span = row.querySelector('.cell-ticket');
                if (span) val = span.textContent.trim();
            } else if (col === 'error') {
                var badge = row.querySelector('.badge-error-type');
                if (badge) val = badge.textContent.trim();
                else val = row.getAttribute('data-error') || '';
            }
            return val.toLowerCase();
        }

        rows.sort(function(a, b) {
            var aVal = getVal(a, column);
            var bVal = getVal(b, column);
            if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        rows.forEach(function(row) { tbody.appendChild(row); });
    };

    document.querySelectorAll('#ticketsBody tr').forEach(function(row) {
        var viewBtn = row.querySelector('.btn-action-view');
        if (viewBtn) {
            row.addEventListener('click', function(e) {
                if (!e.target.closest('.btn-action-view') &&
                    !e.target.closest('.btn-icon-attach') &&
                    !e.target.closest('a')) {
                    var link = this.querySelector('.btn-action-view');
                    if (link) window.location.href = link.href;
                }
            });
            row.style.cursor = 'pointer';
        }
    });

    function syncThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.querySelectorAll('.filter-item .input-field, .filter-item .select-field').forEach(function(el) {
            if (isDark) {
                el.style.backgroundColor = 'rgba(255,255,255,0.04)';
                el.style.borderColor = 'rgba(255,255,255,0.06)';
                el.style.color = '#E8EDF5';
            } else {
                el.style.backgroundColor = '';
                el.style.borderColor = '';
                el.style.color = '';
            }
        });
    }

    var themeToggle = document.getElementById('themeToggleFloating');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            setTimeout(syncThemeStyles, 100);
        });
    }

    var observer = new MutationObserver(syncThemeStyles);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    setTimeout(syncThemeStyles, 200);
});