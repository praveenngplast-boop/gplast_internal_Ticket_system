document.addEventListener('DOMContentLoaded', function() {
    // ========== HIERARCHICAL TREE VIEW LOGIC ==========
    var currentDeptId = null;
    var employeeCache = window.employeeCache || {};
    var searchQuery = '';

    // ============================================================
    // TOGGLE UNIT EXPAND/COLLAPSE
    // ============================================================
    window.toggleUnit = function(element, unitId) {
        var container = document.getElementById('deptContainer-' + unitId);
        var isExpanded = element.classList.contains('expanded');

        if (isExpanded) {
            element.classList.remove('expanded');
            if (container) container.classList.remove('expanded');
        } else {
            element.classList.add('expanded');
            if (container) container.classList.add('expanded');
        }
    };

    // ============================================================
    // EXPAND ALL UNITS
    // ============================================================
    window.expandAllUnits = function() {
        document.querySelectorAll('.tree-unit-item').forEach(function(unit) {
            var unitId = unit.getAttribute('data-unit-id');
            var container = document.getElementById('deptContainer-' + unitId);
            if (container && !unit.classList.contains('expanded')) {
                unit.classList.add('expanded');
                container.classList.add('expanded');
            }
        });
    };

    // ============================================================
    // COLLAPSE ALL UNITS
    // ============================================================
    window.collapseAllUnits = function() {
        document.querySelectorAll('.tree-unit-item').forEach(function(unit) {
            var unitId = unit.getAttribute('data-unit-id');
            var container = document.getElementById('deptContainer-' + unitId);
            if (container && unit.classList.contains('expanded')) {
                unit.classList.remove('expanded');
                container.classList.remove('expanded');
            }
        });
    };

    // ============================================================
    // FILTER TREE ITEMS
    // ============================================================
    window.filterTreeItems = function(query) {
        query = query.toLowerCase().trim();
        searchQuery = query;
        var clearBtn = document.getElementById('clearTreeSearch');

        if (query.length > 0) {
            if (clearBtn) clearBtn.classList.add('visible');
        } else {
            if (clearBtn) clearBtn.classList.remove('visible');
        }

        document.querySelectorAll('.tree-unit-item').forEach(function(unit) {
            var unitName = unit.getAttribute('data-unit-name').toLowerCase();
            var hasMatch = false;

            var deptContainer = unit.nextElementSibling;
            if (deptContainer && deptContainer.classList.contains('tree-dept-container')) {
                var depts = deptContainer.querySelectorAll('.tree-dept-item');
                depts.forEach(function(dept) {
                    var deptName = dept.getAttribute('data-dept-name').toLowerCase();
                    var match = query.length === 0 || deptName.includes(query) || unitName.includes(query);

                    if (match) {
                        dept.classList.remove('hidden');
                        if (query.length > 0 && deptName.includes(query)) {
                            var nameSpan = dept.querySelector('.tree-dept-name');
                            if (nameSpan) {
                                nameSpan.innerHTML = deptName.replace(new RegExp(query, 'gi'), function(matchText) {
                                    return '<span class="tree-dept-match">' + matchText + '</span>';
                                });
                            }
                        } else {
                            var nameSpan = dept.querySelector('.tree-dept-name');
                            if (nameSpan) {
                                nameSpan.innerHTML = deptName;
                            }
                        }
                        hasMatch = true;
                    } else {
                        dept.classList.add('hidden');
                    }
                });
            }

            if (hasMatch || query.length === 0) {
                unit.classList.remove('hidden');
            } else {
                unit.classList.add('hidden');
            }
        });

        if (query.length > 0) {
            document.querySelectorAll('.tree-dept-item:not(.hidden)').forEach(function(dept) {
                var unitId = dept.getAttribute('data-unit-id');
                var unitElement = document.querySelector('.tree-unit-item[data-unit-id="' + unitId + '"]');
                var container = document.getElementById('deptContainer-' + unitId);
                if (unitElement && container) {
                    unitElement.classList.add('expanded');
                    container.classList.add('expanded');
                }
            });
        }
    };

    // ============================================================
    // CLEAR TREE SEARCH
    // ============================================================
    window.clearTreeSearch = function() {
        var input = document.getElementById('treeSearchInput');
        if (input) {
            input.value = '';
            filterTreeItems('');
        }
    };

    // ============================================================
    // LOAD DEPARTMENT EMPLOYEES - FIXED
    // ============================================================
    window.loadDepartmentEmployees = function(deptId, deptName, unitCode) {
        var tableBody = document.getElementById('employeeTableBody');
        var deptNameEl = document.getElementById('selectedDeptName');
        var deptCodeEl = document.getElementById('selectedDeptCode');
        var empCountEl = document.getElementById('selectedEmpCount');

        // Update department info
        if (deptNameEl) deptNameEl.textContent = deptName || 'Select a Department';
        if (deptCodeEl) deptCodeEl.textContent = unitCode || '—';
        if (empCountEl) empCountEl.textContent = 'Loading...';

        // Show loading state
        if (tableBody) {
            tableBody.innerHTML = `
                <div class="loading-state">
                    <i class="fa-solid fa-spinner fa-spin"></i>
                    <h6>Loading employees...</h6>
                    <p>Please wait while we fetch the employee data</p>
                </div>
            `;
        }

        // Check cache first
        if (employeeCache[deptId] && employeeCache[deptId].employees && employeeCache[deptId].employees.length > 0) {
            renderEmployeeTable(deptId, employeeCache[deptId].employees);
            return;
        }

        // ✅ FIXED: Use the correct URL with custom-admin prefix
        var fetchUrl = '/ajax/get-employees-by-department/?department_id=' + deptId;
        console.log('Fetching employees from:', fetchUrl);

        fetch(fetchUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            console.log('Employee data response:', data);
            
            if (data.success) {
                // Update cache
                if (!employeeCache[deptId]) {
                    employeeCache[deptId] = {};
                }
                employeeCache[deptId].employees = data.employees || [];
                
                // Update badge
                var badge = document.getElementById('deptBadge-' + deptId);
                if (badge) {
                    badge.textContent = data.count || 0;
                }
                
                renderEmployeeTable(deptId, data.employees || []);
            } else {
                tableBody.innerHTML = `
                    <div class="empty-state error">
                        <i class="fa-solid fa-circle-exclamation" style="color: #EF4444; opacity: 0.4;"></i>
                        <h6>Error Loading Employees</h6>
                        <p>${data.message || 'Please try again'}</p>
                    </div>
                `;
                if (empCountEl) empCountEl.textContent = '0 employees';
            }
        })
        .catch(function(error) {
            console.error('Error loading employees:', error);
            if (tableBody) {
                tableBody.innerHTML = `
                    <div class="empty-state error">
                        <i class="fa-solid fa-circle-exclamation" style="color: #EF4444; opacity: 0.4;"></i>
                        <h6>Error Loading Employees</h6>
                        <p>Network error. Please try again.</p>
                        <button class="btn-retry" onclick="loadDepartmentEmployees('${deptId}', '${deptName}', '${unitCode}')">
                            <i class="fa-solid fa-rotate"></i> Retry
                        </button>
                    </div>
                `;
            }
            if (empCountEl) empCountEl.textContent = '0 employees';
        });
    };

    // ============================================================
    // RENDER EMPLOYEE TABLE
    // ============================================================
    function renderEmployeeTable(deptId, employees, searchQuery) {
        var tableBody = document.getElementById('employeeTableBody');
        var empCountEl = document.getElementById('selectedEmpCount');

        if (empCountEl) {
            empCountEl.textContent = employees.length + ' employee' + (employees.length !== 1 ? 's' : '');
        }

        if (!employees || employees.length === 0) {
            if (tableBody) {
                tableBody.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-users"></i>
                        <h6>No Employees Found</h6>
                        <p>This department has no employees assigned</p>
                    </div>
                `;
            }
            return;
        }

        var query = (searchQuery || '').toLowerCase().trim();

        var html = `
            <table class="emp-table">
                <thead>
                    <tr>
                        <th><i class="fa-regular fa-id-card"></i> Employee ID</th>
                        <th><i class="fa-regular fa-user"></i> Name</th>
                        <th><i class="fa-solid fa-phone"></i> Mobile</th>
                        <th><i class="fa-regular fa-envelope"></i> Email</th>
                        <th><i class="fa-regular fa-circle"></i> Status</th>
                    </tr>
                </thead>
                <tbody>
        `;

        employees.forEach(function(emp, index) {
            var statusClass = emp.is_active ? 'active' : 'inactive';
            var statusText = emp.is_active ? 'Active' : 'Inactive';
            var statusIcon = emp.is_active ? 'fa-regular fa-circle-check' : 'fa-regular fa-circle';

            var empIdDisplay = emp.employee_id || '-';
            var empNameDisplay = emp.employee_name || '-';
            var empMobileDisplay = emp.mobile || '-';
            var empEmailDisplay = emp.email || '-';

            // Highlight search matches
            if (query) {
                if (empIdDisplay.toLowerCase().includes(query)) {
                    empIdDisplay = empIdDisplay.replace(new RegExp(query, 'gi'), function(matchText) {
                        return '<span class="emp-match">' + matchText + '</span>';
                    });
                }
                if (empNameDisplay.toLowerCase().includes(query)) {
                    empNameDisplay = empNameDisplay.replace(new RegExp(query, 'gi'), function(matchText) {
                        return '<span class="emp-match">' + matchText + '</span>';
                    });
                }
                if (empMobileDisplay.toLowerCase().includes(query)) {
                    empMobileDisplay = empMobileDisplay.replace(new RegExp(query, 'gi'), function(matchText) {
                        return '<span class="emp-match">' + matchText + '</span>';
                    });
                }
                if (empEmailDisplay.toLowerCase().includes(query)) {
                    empEmailDisplay = empEmailDisplay.replace(new RegExp(query, 'gi'), function(matchText) {
                        return '<span class="emp-match">' + matchText + '</span>';
                    });
                }
            }

            var delay = (index * 0.03);
            html += `
                <tr style="animation-delay: ${delay}s;">
                    <td><span class="emp-id">${empIdDisplay}</span></td>
                    <td><span class="emp-name">${empNameDisplay}</span></td>
                    <td><span class="emp-mobile">${empMobileDisplay}</span></td>
                    <td><span class="emp-email">${empEmailDisplay}</span></td>
                    <td>
                        <span class="status-badge ${statusClass}">
                            <i class="${statusIcon}"></i> ${statusText}
                        </span>
                    </td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        if (tableBody) {
            tableBody.innerHTML = html;
        }
    }

    // ============================================================
    // SELECT DEPARTMENT
    // ============================================================
    window.selectDepartment = function(element, deptId, deptName, unitCode) {
        // Remove active class from all departments
        document.querySelectorAll('.tree-dept-item').forEach(function(item) {
            item.classList.remove('active');
        });
        
        // Add active class to selected
        if (element) {
            element.classList.add('active');
        }

        currentDeptId = deptId;

        // Auto-expand the parent unit
        var unitId = element ? element.getAttribute('data-unit-id') : null;
        if (unitId) {
            var unitElement = document.querySelector('.tree-unit-item[data-unit-id="' + unitId + '"]');
            if (unitElement && !unitElement.classList.contains('expanded')) {
                unitElement.classList.add('expanded');
                var container = document.getElementById('deptContainer-' + unitId);
                if (container) {
                    container.classList.add('expanded');
                }
            }
        }

        // Load employees
        loadDepartmentEmployees(deptId, deptName, unitCode);
    };

    // ============================================================
    // FILTER EMPLOYEES (Search within selected department)
    // ============================================================
    window.filterEmployees = function() {
        var searchInput = document.getElementById('empSearchInput');
        if (!searchInput) return;
        
        var query = searchInput.value;

        if (!currentDeptId) return;

        var employees = employeeCache[currentDeptId]?.employees || [];
        renderEmployeeTable(currentDeptId, employees, query);
    };

    // ============================================================
    // CLEAR EMPLOYEE SEARCH
    // ============================================================
    window.clearEmployeeSearch = function() {
        var searchInput = document.getElementById('empSearchInput');
        if (searchInput) {
            searchInput.value = '';
            filterEmployees();
        }
    };

    // ============================================================
    // INITIALIZE - Auto-expand first department on load
    // ============================================================
    setTimeout(function() {
        var firstUnit = document.querySelector('.tree-unit-item');
        if (firstUnit) {
            var unitId = firstUnit.getAttribute('data-unit-id');
            firstUnit.classList.add('expanded');
            var container = document.getElementById('deptContainer-' + unitId);
            if (container) {
                container.classList.add('expanded');
            }

            var firstDept = document.querySelector('.tree-dept-item');
            if (firstDept) {
                // Trigger click to load first department
                var deptId = firstDept.getAttribute('data-dept-id');
                var deptName = firstDept.getAttribute('data-dept-name');
                var unitCode = firstDept.getAttribute('data-unit-code');
                if (deptId) {
                    selectDepartment(firstDept, deptId, deptName, unitCode);
                }
            }
        }
    }, 500);

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.tree-search-box input, .search-box input');
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

    setTimeout(updateTheme, 200);

    console.log('✅ Department Employees JS loaded');
});