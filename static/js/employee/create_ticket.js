document.addEventListener('DOMContentLoaded', function() {
    // ============================================================
    // DOM ELEMENTS
    // ============================================================
    var empIdInput = document.getElementById('id_employee_id');
    var empNameInput = document.getElementById('id_employee_name');
    var empMobileInput = document.getElementById('id_mobile');
    var empEmailInput = document.getElementById('id_email');
    var erpUserIdInput = document.getElementById('erp_user_id');
    var erpAutoFillBadge = document.getElementById('erpAutoFillBadge');
    var unitSelect = document.getElementById('id_unit');
    var deptSelect = document.getElementById('id_department');
    var deptLoading = document.getElementById('dept-loading');
    var empFetchStatus = document.getElementById('empFetchStatus');
    var empFetchMessage = document.getElementById('empFetchMessage');
    var autoFillBadge = document.getElementById('autoFillBadge');
    var mismatchWarning = document.getElementById('mismatchWarning');
    var mismatchMessage = document.getElementById('mismatchMessage');
    var employeeValid = document.getElementById('employeeValid');
    var empNotFound = document.getElementById('empNotFound');
    var validationBadge = document.getElementById('validationBadge');
    var unitLockBadge = document.getElementById('unitLockBadge');
    var deptLockBadge = document.getElementById('deptLockBadge');
    var form = document.getElementById('ticketForm');
    var submitBtn = document.getElementById('submitBtn');

    // ============================================================
    // STATE VARIABLES
    // ============================================================
    var userUnitId = form.getAttribute('data-user-unit') || '';
    var userDeptId = form.getAttribute('data-user-dept') || '';
    var fetchTimeout = null;
    var isAutoFilled = false;
    var employeeMismatch = false;
    var employeeValidated = false;
    var isCredentialedUser = form.getAttribute('data-is-credentialed') === 'true';
    var isFetching = false;

    // ============================================================
    // CORE LOCKING FUNCTIONS - Using readonly/disabled attributes
    // ============================================================
    
    /**
     * Lock all auto-filled fields (Name, Mobile, Email, Unit, Department)
     * Using readonly for text inputs and disabled for select dropdowns
     */
    function lockFields(lock) {
        // Text inputs - use readonly attribute
        var textFields = [empNameInput, empMobileInput, empEmailInput];
        textFields.forEach(function(field) {
            if (field) {
                if (lock) {
                    field.setAttribute('readonly', 'readonly');
                    field.classList.add('field-locked');
                    field.style.cursor = 'not-allowed';
                } else {
                    field.removeAttribute('readonly');
                    field.classList.remove('field-locked');
                    field.style.cursor = '';
                }
            }
        });

        // ERP User ID - always readonly (but we'll manage the class)
        if (erpUserIdInput) {
            if (lock) {
                erpUserIdInput.classList.add('field-locked');
            } else {
                erpUserIdInput.classList.remove('field-locked');
            }
        }

        // Keep auto-filled selects locked visually, but enabled so their values submit.
        var selectFields = [unitSelect, deptSelect];
        selectFields.forEach(function(field) {
            if (field) {
                if (lock) {
                    field.setAttribute('aria-disabled', 'true');
                    field.style.pointerEvents = 'none';
                    field.classList.add('field-locked');
                } else {
                    // Don't remove disabled if user is credentialed
                    if (!isCredentialedUser) {
                        field.removeAttribute('aria-disabled');
                        field.style.pointerEvents = '';
                        field.classList.remove('field-locked');
                    }
                }
            }
        });

        // Show/hide lock badges
        if (unitLockBadge) {
            unitLockBadge.style.display = (lock && !isCredentialedUser) ? 'inline-flex' : 'none';
        }
        if (deptLockBadge) {
            deptLockBadge.style.display = (lock && !isCredentialedUser) ? 'inline-flex' : 'none';
        }

        // If user is credentialed, keep their fields locked always
        if (isCredentialedUser) {
            if (unitSelect) {
                unitSelect.setAttribute('aria-disabled', 'true');
                unitSelect.style.pointerEvents = 'none';
                unitSelect.classList.add('field-locked');
            }
            if (deptSelect) {
                deptSelect.setAttribute('aria-disabled', 'true');
                deptSelect.style.pointerEvents = 'none';
                deptSelect.classList.add('field-locked');
            }
            if (unitLockBadge) unitLockBadge.style.display = 'inline-flex';
            if (deptLockBadge) deptLockBadge.style.display = 'inline-flex';
        }
    }

    /**
     * Unlock all fields and clear auto-filled values
     */
    function unlockAndClearFields() {
        // Unlock fields
        lockFields(false);
        
        // Clear auto-filled values but preserve if credentialed
        if (!isCredentialedUser) {
            [empNameInput, empMobileInput, empEmailInput].forEach(function(field) {
                if (field) {
                    field.value = '';
                    field.classList.remove('field-auto-filled');
                    field.removeAttribute('data-auto-filled');
                }
            });
            
            if (unitSelect) {
                unitSelect.value = '';
                unitSelect.classList.remove('field-auto-filled');
                unitSelect.removeAttribute('data-auto-filled');
            }
            if (deptSelect) {
                deptSelect.value = '';
                deptSelect.classList.remove('field-auto-filled');
                deptSelect.removeAttribute('data-auto-filled');
            }
            
            // Clear ERP User ID
            if (erpUserIdInput) {
                erpUserIdInput.value = '';
                erpUserIdInput.style.borderColor = '';
                erpUserIdInput.style.color = '';
            }
            if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
            
            // Clear screens
            var screenSelect = document.getElementById('id_screen_number');
            if (screenSelect) {
                screenSelect.innerHTML = '<option value="">Please enter Employee ID first</option>';
            }
        }
        
        isAutoFilled = false;
        employeeValidated = false;
        employeeMismatch = false;
    }

    /**
     * Mark a field as auto-filled
     */
    function markFieldAutoFilled(field, isAuto) {
        if (!field) return;
        if (isAuto) {
            field.classList.add('field-auto-filled');
            field.setAttribute('data-auto-filled', 'true');
        } else {
            field.classList.remove('field-auto-filled');
            field.removeAttribute('data-auto-filled');
        }
    }

    // ============================================================
    // INIT: LOCK FIELDS FOR CREDENTIALED USERS
    // ============================================================
    if (isCredentialedUser) {
        lockFields(true);
        if (unitSelect) {
            unitSelect.classList.add('field-locked');
            unitSelect.setAttribute('aria-disabled', 'true');
            unitSelect.style.pointerEvents = 'none';
        }
        if (deptSelect) {
            deptSelect.classList.add('field-locked');
            deptSelect.setAttribute('aria-disabled', 'true');
            deptSelect.style.pointerEvents = 'none';
        }
        if (unitLockBadge) unitLockBadge.style.display = 'inline-flex';
        if (deptLockBadge) deptLockBadge.style.display = 'inline-flex';
    }

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================
    function hideAllValidationMessages() {
        [mismatchWarning, employeeValid, empNotFound].forEach(function(el) {
            if (el) el.classList.remove('show');
        });
        if (empFetchMessage) {
            empFetchMessage.style.display = 'none';
            empFetchMessage.textContent = '';
        }
        if (autoFillBadge) autoFillBadge.style.display = 'none';
        if (validationBadge) validationBadge.style.display = 'none';
        if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
    }

    function showFetchStatus(status, message) {
        message = message || '';
        if (!empFetchStatus) return;

        hideAllValidationMessages();
        empFetchStatus.className = 'emp-fetch-status';
        employeeMismatch = false;
        employeeValidated = false;

        if (status === 'loading') {
            empFetchStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            empFetchStatus.classList.add('loading');
            if (empFetchMessage) {
                empFetchMessage.style.display = 'block';
                empFetchMessage.textContent = '⏳ Validating employee ID...';
                empFetchMessage.style.color = 'var(--text-muted-light)';
                empFetchMessage.className = 'char-counter';
                empFetchMessage.style.textAlign = 'left';
            }
            isFetching = true;
            // Unlock fields while loading
            if (!isCredentialedUser) {
                lockFields(false);
            }
        } else if (status === 'found') {
            employeeValidated = true;
            empFetchStatus.innerHTML = '<i class="fa-regular fa-circle-check"></i>';
            empFetchStatus.classList.add('found');
            if (empFetchMessage) {
                empFetchMessage.style.display = 'block';
                empFetchMessage.textContent = '✅ Employee verified! Belongs to your department.';
                empFetchMessage.style.color = 'var(--success-color)';
                empFetchMessage.className = 'char-counter';
                empFetchMessage.style.textAlign = 'left';
            }
            if (autoFillBadge) {
                autoFillBadge.style.display = 'inline-block';
                autoFillBadge.innerHTML = '<i class="fa-solid fa-magic me-1"></i>Auto-filled';
            }
            if (validationBadge) {
                validationBadge.style.display = 'inline-block';
                validationBadge.className = 'validation-badge valid';
                validationBadge.innerHTML = '<i class="fa-regular fa-check-circle me-1"></i>Valid';
            }
            if (employeeValid) {
                employeeValid.classList.add('show');
                employeeValid.innerHTML = '<i class="fa-regular fa-circle-check"></i> Employee verified and belongs to your department.';
            }
            if (mismatchWarning) mismatchWarning.classList.remove('show');
            if (empNotFound) empNotFound.classList.remove('show');
            isFetching = false;
            
            // LOCK ALL FIELDS after successful validation
            if (!isCredentialedUser) {
                lockFields(true);
            }
            
        } else if (status === 'mismatch') {
            employeeMismatch = true;
            employeeValidated = false;
            empFetchStatus.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            empFetchStatus.classList.add('mismatch');
            
            if (empFetchMessage) {
                empFetchMessage.style.display = 'none';
                empFetchMessage.textContent = '';
            }
            
            if (autoFillBadge) autoFillBadge.style.display = 'none';
            if (validationBadge) {
                validationBadge.style.display = 'inline-block';
                validationBadge.className = 'validation-badge invalid';
                validationBadge.innerHTML = '<i class="fa-solid fa-times-circle me-1"></i>Invalid';
            }
            if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
            
            if (mismatchWarning) {
                mismatchWarning.classList.add('show');
                mismatchWarning.className = 'validation-message mismatch show';
                if (mismatchMessage) {
                    mismatchMessage.textContent = '⚠️ Employee belongs to a different department/unit. You can only create tickets for employees in your department.';
                }
            }
            
            if (employeeValid) employeeValid.classList.remove('show');
            if (empNotFound) empNotFound.classList.remove('show');
            
            // Clear and unlock on mismatch
            unlockAndClearFields();
            if (empIdInput) {
                empIdInput.value = '';
                empIdInput.focus();
            }
            isFetching = false;
            
        } else if (status === 'not-found') {
            employeeMismatch = true;
            employeeValidated = false;
            empFetchStatus.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
            empFetchStatus.classList.add('not-found');
            
            if (empFetchMessage) {
                empFetchMessage.style.display = 'none';
                empFetchMessage.textContent = '';
            }
            
            if (autoFillBadge) autoFillBadge.style.display = 'none';
            if (validationBadge) {
                validationBadge.style.display = 'inline-block';
                validationBadge.className = 'validation-badge invalid';
                validationBadge.innerHTML = '<i class="fa-solid fa-times-circle me-1"></i>Invalid';
            }
            if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
            if (mismatchWarning) mismatchWarning.classList.remove('show');
            if (employeeValid) employeeValid.classList.remove('show');
            if (empNotFound) {
                empNotFound.classList.add('show');
                empNotFound.className = 'validation-message not-found show';
                var notFoundSpan = empNotFound.querySelector('span');
                if (notFoundSpan) {
                    notFoundSpan.textContent = 'Employee ID not found. Please check and try again.';
                }
            }
            
            // Clear and unlock on not found
            unlockAndClearFields();
            if (empIdInput) {
                empIdInput.value = '';
                empIdInput.focus();
            }
            isFetching = false;
        }
    }

    function clearFetchStatus() {
        hideAllValidationMessages();
        if (empFetchStatus) {
            empFetchStatus.className = 'emp-fetch-status';
            empFetchStatus.innerHTML = '';
        }
        if (empFetchMessage) {
            empFetchMessage.style.display = 'none';
            empFetchMessage.textContent = '';
        }
        if (autoFillBadge) autoFillBadge.style.display = 'none';
        if (validationBadge) validationBadge.style.display = 'none';
        if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
        if (mismatchWarning) mismatchWarning.classList.remove('show');
        if (employeeValid) employeeValid.classList.remove('show');
        if (empNotFound) empNotFound.classList.remove('show');
        employeeMismatch = false;
        employeeValidated = false;
        isFetching = false;
        
        // Unlock fields when clearing status (unless credentialed)
        if (!isCredentialedUser) {
            lockFields(false);
        }
    }

    function autoFillEmployeeDetails(data) {
        if (employeeMismatch || !data) return;

        isAutoFilled = true;
        employeeValidated = true;

        // Fill Employee Name
        if (data.employee_name) {
            empNameInput.value = data.employee_name;
            markFieldAutoFilled(empNameInput, true);
        }

        // Fill Mobile (optional - only if present)
        if (data.mobile) {
            empMobileInput.value = data.mobile;
            markFieldAutoFilled(empMobileInput, true);
        }

        // Fill Email (optional - only if present)
        if (data.email) {
            empEmailInput.value = data.email;
            markFieldAutoFilled(empEmailInput, true);
        }

        // Fill ERP User ID
        if (data.erp_user_id && erpUserIdInput) {
            erpUserIdInput.value = data.erp_user_id;
            erpUserIdInput.style.borderColor = 'var(--success-color)';
            erpUserIdInput.style.color = 'var(--success-color)';
            if (erpAutoFillBadge) {
                erpAutoFillBadge.style.display = 'inline-block';
                erpAutoFillBadge.innerHTML = '<i class="fa-solid fa-magic me-1"></i>Auto-filled';
            }
            // Fetch mapped screens
            fetchScreensForErp(data.erp_user_id);
        } else if (erpUserIdInput) {
            erpUserIdInput.value = 'Not mapped';
            erpUserIdInput.style.borderColor = 'var(--warning-color)';
            erpUserIdInput.style.color = 'var(--warning-color)';
            if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
            // Clear screens
            var screenSelect = document.getElementById('id_screen_number');
            if (screenSelect) {
                screenSelect.innerHTML = '<option value="">No screens mapped for this ERP ID</option>';
            }
        }

        // Fill Unit
        if (data.unit_id && unitSelect) {
            unitSelect.value = data.unit_id;
            markFieldAutoFilled(unitSelect, true);
            loadDepartments(data.unit_id, data.department_id, true);
        }
        
        // Fill Department
        if (data.department_id && deptSelect) {
            if (deptSelect.querySelector('option[value="' + data.department_id + '"]')) {
                deptSelect.value = data.department_id;
                markFieldAutoFilled(deptSelect, true);
            }
        }

        // LOCK ALL FIELDS after filling
        if (!isCredentialedUser) {
            lockFields(true);
        }
    }

    // ============================================================
    // EMPLOYEE FETCH FUNCTION
    // ============================================================
    function fetchEmployeeDetails(employeeId) {
        if (fetchTimeout) {
            clearTimeout(fetchTimeout);
            fetchTimeout = null;
        }

        var trimmedId = employeeId.trim();

        if (!trimmedId || trimmedId.length < 2) {
            clearFetchStatus();
            unlockAndClearFields();
            employeeMismatch = false;
            // If credentialed, re-lock
            if (isCredentialedUser) {
                lockFields(true);
            }
            return;
        }

        fetchTimeout = setTimeout(function() {
            showFetchStatus('loading', 'Validating employee ID...');
            
            var url = '/ajax/get-employee/?employee_id=' + encodeURIComponent(trimmedId);
            if (userUnitId) url += '&unit_id=' + encodeURIComponent(userUnitId);
            if (userDeptId) url += '&department_id=' + encodeURIComponent(userDeptId);

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
            .then(function(res) { 
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json(); 
            })
            .then(function(data) {
                if (data.found) {
                    if (data.mismatch) {
                        var errorMsg = data.message || 'Employee belongs to a different department/unit.';
                        showFetchStatus('mismatch', errorMsg);
                        unlockAndClearFields();
                        if (empIdInput) {
                            empIdInput.value = '';
                            empIdInput.focus();
                        }
                    } else {
                        showFetchStatus('found', 'Employee verified! Belongs to your department.');
                        autoFillEmployeeDetails(data.employee);
                    }
                } else {
                    showFetchStatus('not-found', data.message || 'Employee ID not found. Please check and try again.');
                    unlockAndClearFields();
                    if (empIdInput) {
                        empIdInput.value = '';
                        empIdInput.focus();
                    }
                }
            })
            .catch(function(err) {
                console.error('Fetch error:', err);
                showFetchStatus('not-found', 'Error fetching employee. Please try again.');
                unlockAndClearFields();
            });
        }, 800);
    }

    // ============================================================
    // EMPLOYEE ID INPUT EVENTS
    // ============================================================
    if (empIdInput) {
        empIdInput.addEventListener('input', function() {
            if (fetchTimeout) {
                clearTimeout(fetchTimeout);
                fetchTimeout = null;
            }

            var value = this.value.trim();
            
            if (value.length < 2) {
                clearFetchStatus();
                unlockAndClearFields();
                employeeMismatch = false;
                if (isCredentialedUser) {
                    lockFields(true);
                } else {
                    lockFields(false);
                }
                return;
            }

            fetchEmployeeDetails(value);
        });

        empIdInput.addEventListener('blur', function() {
            var value = this.value.trim();
            if (value.length >= 2 && !isAutoFilled && !employeeValidated && !isFetching) {
                if (fetchTimeout) {
                    clearTimeout(fetchTimeout);
                    fetchTimeout = null;
                }
                fetchEmployeeDetails(value);
            }
        });

        empIdInput.addEventListener('paste', function() {
            setTimeout(function() {
                var value = empIdInput.value.trim();
                if (value.length >= 2) {
                    if (fetchTimeout) {
                        clearTimeout(fetchTimeout);
                        fetchTimeout = null;
                    }
                    fetchEmployeeDetails(value);
                }
            }, 150);
        });
    }

    // ============================================================
    // CLEAR AUTO-FILLED FIELDS WHEN USER TYPES OVER THEM
    // ============================================================
    [empNameInput, empMobileInput, empEmailInput].forEach(function(field) {
        if (field) {
            field.addEventListener('input', function() {
                // If field is locked (readonly), don't allow editing
                if (this.hasAttribute('readonly')) {
                    // If user tries to type in a locked field, revert the value
                    this.value = this.defaultValue || '';
                    return;
                }
                
                if (this.getAttribute('data-auto-filled') === 'true') {
                    markFieldAutoFilled(this, false);
                    employeeValidated = false;
                    if (validationBadge) validationBadge.style.display = 'none';
                    if (employeeValid) employeeValid.classList.remove('show');
                    // Unlock fields if user manually edits
                    if (!isCredentialedUser) {
                        lockFields(false);
                    }
                }
            });
        }
    });

    // ============================================================
    // UNIT SELECT CHANGE - Clear validation
    // ============================================================
    if (unitSelect) {
        unitSelect.addEventListener('change', function() {
            // If unit is disabled (locked), don't allow changes
            if (this.hasAttribute('disabled')) {
                // Revert to previous value if user tries to change
                var currentVal = this.value;
                var prevVal = this.getAttribute('data-locked-value') || '';
                if (currentVal !== prevVal) {
                    this.value = prevVal;
                }
                return;
            }
            
            markFieldAutoFilled(this, false);
            employeeValidated = false;
            employeeMismatch = false;
            clearFetchStatus();
            unlockAndClearFields();
            if (empIdInput) empIdInput.value = '';
            if (!isCredentialedUser) {
                lockFields(false);
            }
        });
    }

    // ============================================================
    // DEPARTMENT SELECT CHANGE - Clear validation
    // ============================================================
    if (deptSelect) {
        deptSelect.addEventListener('change', function() {
            // If dept is disabled (locked), don't allow changes
            if (this.hasAttribute('disabled')) {
                var currentVal = this.value;
                var prevVal = this.getAttribute('data-locked-value') || '';
                if (currentVal !== prevVal) {
                    this.value = prevVal;
                }
                return;
            }
            
            markFieldAutoFilled(this, false);
            employeeValidated = false;
            employeeMismatch = false;
            clearFetchStatus();
            unlockAndClearFields();
            if (empIdInput) empIdInput.value = '';
            if (!isCredentialedUser) {
                lockFields(false);
            }
        });
    }

    // ============================================================
    // LOAD DEPARTMENTS BY UNIT
    // ============================================================
    function loadDepartments(unitId, selectedDeptId, lockAfterLoad) {
        lockAfterLoad = lockAfterLoad || false;
        if (!deptSelect) return;
        if (!unitId) {
            deptSelect.innerHTML = '<option value="">Select Unit First</option>';
            if (!isCredentialedUser) {
                deptSelect.removeAttribute('aria-disabled');
                deptSelect.style.pointerEvents = '';
            }
            return;
        }
        if (deptLoading) deptLoading.style.display = 'block';
        if (!isCredentialedUser) {
            deptSelect.setAttribute('aria-disabled', 'true');
            deptSelect.style.pointerEvents = 'none';
        }
        deptSelect.innerHTML = '<option value="">Loading departments...</option>';

        fetch('/ajax/get-departments/?unit_id=' + unitId, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            deptSelect.innerHTML = '<option value="">Select Department</option>';
            if (data.departments && data.departments.length) {
                data.departments.forEach(function(d) {
                    var opt = document.createElement('option');
                    opt.value = d.id;
                    opt.textContent = d.name;
                    if (selectedDeptId && d.id == selectedDeptId) {
                        opt.selected = true;
                        markFieldAutoFilled(deptSelect, true);
                    }
                    deptSelect.appendChild(opt);
                });
                if (selectedDeptId) {
                    var found = false;
                    for (var i = 0; i < deptSelect.options.length; i++) {
                        if (deptSelect.options[i].value == selectedDeptId) {
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        deptSelect.value = selectedDeptId;
                        markFieldAutoFilled(deptSelect, true);
                    }
                }
                
                // Only lock if employee is validated
                if (lockAfterLoad && employeeValidated && !isCredentialedUser) {
                    deptSelect.setAttribute('aria-disabled', 'true');
                    deptSelect.style.pointerEvents = 'none';
                    deptSelect.classList.add('field-locked');
                } else if (!isCredentialedUser) {
                    deptSelect.removeAttribute('aria-disabled');
                    deptSelect.style.pointerEvents = '';
                    deptSelect.classList.remove('field-locked');
                }
                
                if (isCredentialedUser) {
                    deptSelect.setAttribute('aria-disabled', 'true');
                    deptSelect.style.pointerEvents = 'none';
                    deptSelect.classList.add('field-locked');
                }
            } else {
                deptSelect.innerHTML += '<option value="">No departments available</option>';
                if (!isCredentialedUser) {
                    deptSelect.removeAttribute('aria-disabled');
                    deptSelect.style.pointerEvents = '';
                }
            }
            if (deptLoading) deptLoading.style.display = 'none';
        })
        .catch(function(err) {
            deptSelect.innerHTML = '<option value="">Error loading departments</option>';
            if (!isCredentialedUser) {
                deptSelect.removeAttribute('aria-disabled');
                deptSelect.style.pointerEvents = '';
            }
            if (deptLoading) deptLoading.style.display = 'none';
        });
    }

    // Load departments on unit change only if unit is not locked
    if (unitSelect) {
        if (unitSelect.value) {
            loadDepartments(unitSelect.value, deptSelect ? deptSelect.value : null, employeeValidated);
        }
    }

    // ============================================================
    // FETCH SCREENS FOR ERP ID
    // ============================================================
    function fetchScreensForErp(erpUserId) {
        var screenSelect = document.getElementById('id_screen_number');
        if (!screenSelect) return;
        
        screenSelect.innerHTML = '<option value="">Loading screens...</option>';
        
        fetch('/ajax/get-screens-for-erp/?erp_user_id=' + encodeURIComponent(erpUserId))
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.success && data.screens && data.screens.length > 0) {
                    var options = '<option value="">Select Screen/Module</option>';
                    data.screens.forEach(function(s) {
                        options += '<option value="' + s.screen_code + '">' + s.display + '</option>';
                    });
                    screenSelect.innerHTML = options;
                    
                    // Recover previous selection if we had an error validation reload
                    var preVal = "{{ form.screen_number.value|default:'' }}";
                    if (preVal && data.screens.some(function(s) { return s.screen_code === preVal; })) {
                        screenSelect.value = preVal;
                    }
                } else {
                    screenSelect.innerHTML = '<option value="">No screens mapped for this ERP ID</option>';
                }
            })
            .catch(function(err) {
                console.error("Failed to fetch screens", err);
                screenSelect.innerHTML = '<option value="">Error loading screens</option>';
            });
    }

    // ============================================================
    // CHARACTER COUNTERS
    // ============================================================
    function setupCounter(inputId, counterId, maxLen, minLen) {
        maxLen = maxLen || null;
        minLen = minLen || null;
        var input = document.getElementById(inputId);
        var counter = document.getElementById(counterId);
        if (!input || !counter) return;

        var counterNumber = counter.querySelector('.counter-number');

        function updateCounter() {
            var count = input.value.length;
            if (counterNumber) {
                counterNumber.textContent = count;
            } else {
                var text = counter.textContent || counter.innerText;
                var parts = text.split('/');
                if (parts.length > 1) {
                    counter.innerHTML = '<span class="counter-number">' + count + '</span>' + ' / ' + parts[1].trim();
                } else if (text.includes('chars')) {
                    counter.innerHTML = '<span class="counter-number">' + count + '</span> chars' + (minLen ? ' (min ' + minLen + ')' : '');
                } else {
                    counter.innerHTML = '<span class="counter-number">' + count + '</span> chars';
                }
            }

            if (maxLen && count > maxLen) {
                counter.className = 'char-counter danger';
                counter.title = 'Maximum ' + maxLen + ' characters allowed';
                input.style.borderColor = 'var(--danger-color)';
            } else if (maxLen && count > maxLen * 0.85) {
                counter.className = 'char-counter warning';
                counter.title = 'Approaching character limit (' + count + '/' + maxLen + ')';
                input.style.borderColor = '';
            } else if (minLen && count < minLen && count > 0) {
                counter.className = 'char-counter warning';
                counter.title = 'Minimum ' + minLen + ' characters required';
                input.style.borderColor = '';
            } else {
                counter.className = 'char-counter';
                counter.title = '';
                input.style.borderColor = '';
            }
        }

        input.addEventListener('input', updateCounter);
        input.addEventListener('focus', updateCounter);
        setTimeout(updateCounter, 100);
    }

    setupCounter('id_screen_number', 'screen_counter');
    setupCounter('id_subject', 'subject_counter', 150);
    setupCounter('id_description', 'desc_counter', null, 10);

    // ============================================================
    // ATTACHMENT MANAGEMENT
    // ============================================================
    var MAX_ATTACHMENTS = 3;
    
    var attachmentContainer = document.getElementById('attachmentContainer');
    var addAttachmentBtn = document.getElementById('addAttachmentBtn');
    var attachmentCounter = document.getElementById('attachmentCounter');
    
    var wrapper1 = document.getElementById('attachmentWrapper1');
    var wrapper2 = document.getElementById('attachmentWrapper2');
    var wrapper3 = document.getElementById('attachmentWrapper3');
    
    var fileInput1 = document.getElementById('id_attachment_1');
    var fileInput2 = document.getElementById('id_attachment_2');
    var fileInput3 = document.getElementById('id_attachment_3');
    
    var status1 = document.getElementById('status1');
    var status2 = document.getElementById('status2');
    var status3 = document.getElementById('status3');
    
    if (wrapper1) wrapper1.style.display = 'block';
    if (wrapper2) wrapper2.style.display = 'none';
    if (wrapper3) wrapper3.style.display = 'none';
    
    function updateAttachmentStatus(wrapper, fileInput, statusEl, num) {
        if (!wrapper || !fileInput || !statusEl) return;
        
        var hasFile = fileInput.files && fileInput.files.length > 0;
        var statusIcon = statusEl.querySelector('.status-icon');
        var statusText = statusEl.querySelector('.status-text');
        
        if (hasFile) {
            var fileName = fileInput.files[0].name;
            var fileSize = (fileInput.files[0].size / 1024).toFixed(1);
            statusIcon.textContent = '✅';
            if (num === 1) {
                statusText.textContent = fileName + ' (' + fileSize + ' KB)';
                statusText.style.color = '';
                statusText.style.fontWeight = '';
            } else {
                statusText.textContent = fileName + ' (' + fileSize + ' KB)';
                statusText.style.color = '';
                statusText.style.fontWeight = '';
            }
            statusText.className = 'status-text has-file';
            
            var removeBtn = wrapper.querySelector('.remove-attachment');
            if (removeBtn) removeBtn.style.display = 'block';
            
            if (num === 1 && wrapper2.style.display === 'none') {
                checkAndEnableAddButton();
            }
            if (num === 2 && wrapper3.style.display === 'none') {
                checkAndEnableAddButton();
            }
        } else {
            statusIcon.textContent = '⏳';
            if (num === 1) {
                statusText.textContent = 'No file selected (Required)';
                statusText.style.color = '#EF4444';
                statusText.style.fontWeight = '600';
            } else {
                statusText.textContent = 'No file selected';
                statusText.style.color = '';
                statusText.style.fontWeight = '';
            }
            statusText.className = 'status-text';
            
            if (num === 1) {
                if (wrapper2.style.display !== 'none') {
                    wrapper2.style.display = 'none';
                    if (fileInput2) {
                        fileInput2.value = '';
                        updateAttachmentStatus(wrapper2, fileInput2, status2, 2);
                    }
                }
                if (wrapper3.style.display !== 'none') {
                    wrapper3.style.display = 'none';
                    if (fileInput3) {
                        fileInput3.value = '';
                        updateAttachmentStatus(wrapper3, fileInput3, status3, 3);
                    }
                }
            } else if (num === 2) {
                if (wrapper3.style.display !== 'none') {
                    wrapper3.style.display = 'none';
                    if (fileInput3) {
                        fileInput3.value = '';
                        updateAttachmentStatus(wrapper3, fileInput3, status3, 3);
                    }
                }
            }
            
            checkAndEnableAddButton();
        }
    }
    
    function checkAndEnableAddButton() {
        var visibleCount = 0;
        var wrappers = [wrapper1, wrapper2, wrapper3];
        wrappers.forEach(function(w) {
            if (w && w.style.display !== 'none') {
                visibleCount++;
            }
        });
        
        var canAdd = false;
        if (visibleCount < MAX_ATTACHMENTS) {
            var lastVisibleNum = 0;
            for (var i = 1; i <= MAX_ATTACHMENTS; i++) {
                var w = document.getElementById('attachmentWrapper' + i);
                if (w && w.style.display !== 'none') {
                    lastVisibleNum = i;
                }
            }
            var fileInput = document.getElementById('id_attachment_' + lastVisibleNum);
            if (fileInput && fileInput.files && fileInput.files.length > 0) {
                canAdd = true;
            }
        }
        
        if (visibleCount >= MAX_ATTACHMENTS) {
            addAttachmentBtn.disabled = true;
            addAttachmentBtn.innerHTML = '<i class="fa-solid fa-ban"></i> Maximum 3 attachments reached';
            addAttachmentBtn.style.borderColor = '#EF4444';
            addAttachmentBtn.style.color = '#EF4444';
            addAttachmentBtn.style.opacity = '0.6';
            addAttachmentBtn.style.cursor = 'not-allowed';
        } else if (!canAdd) {
            addAttachmentBtn.disabled = true;
            var lastNum = visibleCount;
            addAttachmentBtn.innerHTML = '<i class="fa-solid fa-clock"></i> Add file to Attachment ' + lastNum + ' first';
            addAttachmentBtn.style.borderColor = '#F59E0B';
            addAttachmentBtn.style.color = '#F59E0B';
            addAttachmentBtn.style.opacity = '0.7';
            addAttachmentBtn.style.cursor = 'not-allowed';
        } else {
            addAttachmentBtn.disabled = false;
            addAttachmentBtn.innerHTML = '<i class="fa-solid fa-plus-circle"></i> Add Attachment';
            addAttachmentBtn.style.borderColor = '';
            addAttachmentBtn.style.color = '';
            addAttachmentBtn.style.opacity = '1';
            addAttachmentBtn.style.cursor = 'pointer';
        }
        
        var fileCount = 0;
        for (var i = 1; i <= MAX_ATTACHMENTS; i++) {
            var fi = document.getElementById('id_attachment_' + i);
            if (fi && fi.files && fi.files.length > 0) {
                fileCount++;
            }
        }
        attachmentCounter.innerHTML = '<i class="fa-regular fa-circle-info"></i> ' + fileCount + ' of ' + MAX_ATTACHMENTS + ' attachments selected';
    }
    
    if (fileInput1) {
        fileInput1.addEventListener('change', function() {
            updateAttachmentStatus(wrapper1, fileInput1, status1, 1);
            checkAndEnableAddButton();
        });
    }
    if (fileInput2) {
        fileInput2.addEventListener('change', function() {
            updateAttachmentStatus(wrapper2, fileInput2, status2, 2);
            checkAndEnableAddButton();
        });
    }
    if (fileInput3) {
        fileInput3.addEventListener('change', function() {
            updateAttachmentStatus(wrapper3, fileInput3, status3, 3);
            checkAndEnableAddButton();
        });
    }
    
    addAttachmentBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        var firstHidden = null;
        var wrappers = [wrapper1, wrapper2, wrapper3];
        
        wrappers.forEach(function(w) {
            if (w && w.style.display === 'none' && firstHidden === null) {
                firstHidden = w;
            }
        });
        
        if (!firstHidden) {
            alert('Maximum 3 attachments allowed.');
            return;
        }
        
        firstHidden.style.display = 'block';
        
        var fileInput = firstHidden.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.value = '';
            fileInput.style.display = 'block';
            fileInput.style.width = '100%';
        }
        
        var num = firstHidden.getAttribute('data-attachment-num');
        var statusEl = document.getElementById('status' + num);
        if (statusEl) {
            var icon = statusEl.querySelector('.status-icon');
            var text = statusEl.querySelector('.status-text');
            if (icon) icon.textContent = '⏳';
            if (text) {
                if (num == 1) {
                    text.textContent = 'No file selected (Required)';
                    text.style.color = '#EF4444';
                    text.style.fontWeight = '600';
                } else {
                    text.textContent = 'No file selected';
                    text.style.color = '';
                    text.style.fontWeight = '';
                }
                text.className = 'status-text';
            }
        }
        
        checkAndEnableAddButton();
    });
    
    attachmentContainer.addEventListener('click', function(e) {
        var removeBtn = e.target.closest('.remove-attachment');
        if (!removeBtn) return;
        
        var num = removeBtn.getAttribute('data-attachment-num');
        var wrapper = document.getElementById('attachmentWrapper' + num);
        if (!wrapper) return;
        
        var wrappers = [wrapper1, wrapper2, wrapper3];
        var visibleCount = 0;
        wrappers.forEach(function(w) {
            if (w && w.style.display !== 'none') {
                visibleCount++;
            }
        });
        
        if (num == 1) {
            var fileInput = document.getElementById('id_attachment_' + num);
            if (fileInput) {
                fileInput.value = '';
                updateAttachmentStatus(wrapper, fileInput, document.getElementById('status' + num), parseInt(num));
            }
            checkAndEnableAddButton();
            return;
        }
        
        if (visibleCount <= 1) {
            alert('You must keep at least one attachment field.');
            return;
        }
        
        wrapper.style.display = 'none';
        
        var fileInput = wrapper.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.value = '';
            fileInput.style.display = 'none';
            fileInput.style.width = '100%';
        }
        
        var statusEl = document.getElementById('status' + num);
        if (statusEl) {
            var icon = statusEl.querySelector('.status-icon');
            var text = statusEl.querySelector('.status-text');
            if (icon) icon.textContent = '⏳';
            if (text) {
                text.textContent = 'No file selected';
                text.className = 'status-text';
                text.style.color = '';
                text.style.fontWeight = '';
            }
        }
        
        checkAndEnableAddButton();
    });
    
    if (fileInput1 && wrapper1 && status1) {
        updateAttachmentStatus(wrapper1, fileInput1, status1, 1);
    }
    checkAndEnableAddButton();

    function validateFileInput(fileInput) {
        if (!fileInput) return;
        fileInput.addEventListener('change', function() {
            var file = this.files[0];
            if (!file) return;
            var maxSize = 3 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('File size exceeds 3MB. Please select a smaller file.');
                this.value = '';
                return;
            }
            var validExtensions = /\.(pdf|doc|docx|xls|xlsx|png|jpg|jpeg|txt)$/i;
            if (!validExtensions.test(file.name)) {
                alert('Unsupported file type. Please upload PDF, DOC, XLS, PNG, JPG, or TXT files.');
                this.value = '';
                return;
            }
        });
    }
    
    validateFileInput(fileInput1);
    validateFileInput(fileInput2);
    validateFileInput(fileInput3);

    // ============================================================
    // FORM SUBMISSION VALIDATION - INCLUDES ATTACHMENT CHECK
    // ============================================================
    if (form && submitBtn) {
        form.addEventListener('submit', function(e) {
            if (employeeMismatch) {
                e.preventDefault();
                alert('❌ Cannot create ticket!\n\nThe Employee ID you entered does not belong to your assigned Unit/Department.\n\nPlease enter a valid Employee ID from your department.');
                return false;
            }

            var empId = empIdInput ? empIdInput.value.trim() : '';
            if (empId && !employeeValidated && !isFetching) {
                e.preventDefault();
                alert('⚠️ Employee validation pending.\n\nPlease wait for the employee validation to complete or enter a valid Employee ID.');
                return false;
            }

            if (!empId) {
                e.preventDefault();
                alert('⚠️ Please enter an Employee ID.');
                empIdInput.focus();
                return false;
            }

            if (!employeeValidated) {
                e.preventDefault();
                alert('⚠️ Please enter a valid Employee ID from your department.');
                empIdInput.focus();
                return false;
            }

            // ============================================================
            // VALIDATE: Attachment 1 is required
            // ============================================================
            var attachment1 = document.getElementById('id_attachment_1');
            if (attachment1) {
                if (!attachment1.files || attachment1.files.length === 0) {
                    e.preventDefault();
                    alert('❌ Attachment 1 is required.\n\nPlease select a file to upload before submitting the ticket.');
                    attachment1.focus();
                    return false;
                }
            }

            if (this.checkValidity()) {
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Submitting...';
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.7';
            }
        });
    }

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateFormTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, .form-select, textarea, input[type="text"], input[type="email"], input[type="tel"], input[type="number"], select');

        inputs.forEach(function(input) {
            input.style.display = 'none';
            void input.offsetHeight;
            input.style.display = '';

            if (isDark) {
                input.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                input.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                input.style.color = '#E8EDF5';
            } else {
                input.style.backgroundColor = '#F8FAFF';
                input.style.borderColor = '#DCE3F0';
                input.style.color = '#1A2A6C';
            }
        });
    }

    var themeToggleBtn = document.getElementById('themeToggleFloating');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            setTimeout(updateFormTheme, 100);
        });
    }

    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                updateFormTheme();
            }
        });
    });

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateFormTheme, 200);
});