document.addEventListener('DOMContentLoaded', function() {
    // ============================================================
    // FIX: Notification URL - Use correct custom-admin path
    // ============================================================
    function fixNotificationUrl() {
        var originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (typeof url === 'string' && url.includes('/notifications/')) {
                url = url.replace('/notifications/', '/custom-admin/notifications/');
            }
            return originalFetch.call(this, url, options);
        };
        
        var originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
            if (typeof url === 'string' && url.includes('/notifications/')) {
                url = url.replace('/notifications/', '/custom-admin/notifications/');
            }
            return originalOpen.call(this, method, url, async !== false, user, password);
        };
    }
    fixNotificationUrl();

    // ============================================================
    // DOM ELEMENTS
    // ============================================================
    var empIdInput = document.getElementById('id_employee_id');
    var empNameInput = document.getElementById('id_employee_name');
    var empMobileInput = document.getElementById('id_mobile');
    var empEmailInput = document.getElementById('id_email');
    var erpUserIdInput = document.getElementById('erp_user_id');
    var erpAutoFillBadge = document.getElementById('erpAutoFillBadge');
    var empFetchStatus = document.getElementById('empFetchStatus');
    var empFetchMessage = document.getElementById('empFetchMessage');
    var autoFillBadge = document.getElementById('autoFillBadge');
    var employeeValid = document.getElementById('employeeValid');
    var departmentSelect = document.getElementById('id_department');
    var unitSelect = document.getElementById('id_unit');
    var errorTypeSelect = document.getElementById('id_error_type');
    
    var fetchTimeout = null;
    var isEmployeeFetched = false;

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

        // ERP User ID - always readonly (manage the class)
        if (erpUserIdInput) {
            if (lock) {
                erpUserIdInput.classList.add('field-locked');
            } else {
                erpUserIdInput.classList.remove('field-locked');
            }
        }

        // Keep auto-filled selects locked visually, but enabled so their values submit.
        var selectFields = [unitSelect, departmentSelect];
        selectFields.forEach(function(field) {
            if (field) {
                if (lock) {
                    field.setAttribute('aria-disabled', 'true');
                    field.style.pointerEvents = 'none';
                    field.classList.add('field-locked');
                } else {
                    field.removeAttribute('aria-disabled');
                    field.style.pointerEvents = '';
                    field.classList.remove('field-locked');
                }
            }
        });

        // Show/hide lock badges on labels
        var unitLabel = document.querySelector('label[for="id_unit"]');
        var deptLabel = document.querySelector('label[for="id_department"]');
        
        if (unitLabel) {
            var existingBadge = unitLabel.querySelector('.badge-locked');
            if (lock) {
                if (!existingBadge) {
                    var badge = document.createElement('span');
                    badge.className = 'badge-locked';
                    badge.innerHTML = '<i class="fa-solid fa-lock me-1"></i>Locked';
                    unitLabel.appendChild(badge);
                }
            } else {
                if (existingBadge) existingBadge.remove();
            }
        }
        
        if (deptLabel) {
            var existingBadge = deptLabel.querySelector('.badge-locked');
            if (lock) {
                if (!existingBadge) {
                    var badge = document.createElement('span');
                    badge.className = 'badge-locked';
                    badge.innerHTML = '<i class="fa-solid fa-lock me-1"></i>Locked';
                    deptLabel.appendChild(badge);
                }
            } else {
                if (existingBadge) existingBadge.remove();
            }
        }

        // Error Type - NEVER locked (user can always change)
        if (errorTypeSelect) {
            errorTypeSelect.classList.remove('field-locked');
            errorTypeSelect.removeAttribute('disabled');
        }
        var errorLabel = document.querySelector('label[for="id_error_type"]');
        if (errorLabel) {
            var badge = errorLabel.querySelector('.badge-locked');
            if (badge) badge.remove();
        }
    }

    /**
     * Unlock all fields and clear auto-filled values
     */
    function unlockAndClearFields() {
        // Unlock fields
        lockFields(false);
        
        // Clear auto-filled values
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
        if (departmentSelect) {
            departmentSelect.value = '';
            departmentSelect.classList.remove('field-auto-filled');
            departmentSelect.removeAttribute('data-auto-filled');
        }
        
        // Clear ERP User ID
        if (erpUserIdInput) {
            erpUserIdInput.value = '';
            erpUserIdInput.style.borderColor = '';
            erpUserIdInput.style.color = '';
            erpUserIdInput.classList.remove('field-auto-filled');
        }
        if (erpAutoFillBadge) erpAutoFillBadge.style.display = 'none';
        
        isEmployeeFetched = false;
    }

    /**
     * Mark a field as auto-filled
     */
    function markAutoFilled(field, isAuto) {
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
    // EMPLOYEE FETCH FUNCTIONS
    // ============================================================
    function showFetchStatus(status, message) {
        empFetchStatus.className = 'emp-fetch-status';
        empFetchMessage.className = 'fetch-message';
        empFetchMessage.style.display = 'none';
        employeeValid.style.display = 'none';
        erpAutoFillBadge.style.display = 'none';
        
        if (status === 'loading') {
            empFetchStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            empFetchStatus.classList.add('loading');
            autoFillBadge.style.display = 'none';
            // Unlock fields while loading
            lockFields(false);
        } else if (status === 'found') {
            empFetchStatus.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            empFetchStatus.classList.add('found');
            empFetchMessage.textContent = message || 'Employee verified. Details auto-filled.';
            empFetchMessage.className = 'fetch-message show success';
            autoFillBadge.style.display = 'inline-flex';
            employeeValid.style.display = 'block';
            isEmployeeFetched = true;
            
            // LOCK fields after successful validation
            lockFields(true);
            
        } else if (status === 'not-found') {
            empFetchStatus.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
            empFetchStatus.classList.add('not-found');
            empFetchMessage.textContent = message || 'Employee not found.';
            empFetchMessage.className = 'fetch-message show error';
            autoFillBadge.style.display = 'none';
            isEmployeeFetched = false;
            
            // UNLOCK on not found
            lockFields(false);
            
        } else {
            empFetchStatus.innerHTML = '';
            empFetchMessage.className = 'fetch-message';
            empFetchMessage.style.display = 'none';
            autoFillBadge.style.display = 'none';
            isEmployeeFetched = false;
            
            // UNLOCK on clear
            lockFields(false);
        }
    }
    
    function fetchEmployeeDetails(employeeId) {
        if (!employeeId || employeeId.length < 2) {
            showFetchStatus('');
            unlockAndClearFields();
            return;
        }
        
        showFetchStatus('loading');
        
        fetch('/ajax/get-employee/?employee_id=' + encodeURIComponent(employeeId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.found && data.employee) {
                showFetchStatus('found', 'Employee verified. Details auto-filled.');
                
                if (data.employee.employee_name) {
                    empNameInput.value = data.employee.employee_name;
                    markAutoFilled(empNameInput, true);
                }
                if (data.employee.mobile) {
                    empMobileInput.value = data.employee.mobile;
                    markAutoFilled(empMobileInput, true);
                }
                if (data.employee.email) {
                    empEmailInput.value = data.employee.email;
                    markAutoFilled(empEmailInput, true);
                }
                
                // Auto-fill ERP User ID
                if (data.employee.erp_user_id && erpUserIdInput) {
                    erpUserIdInput.value = data.employee.erp_user_id;
                    erpUserIdInput.style.borderColor = 'var(--admin-success, #10B981)';
                    erpUserIdInput.style.color = 'var(--admin-success, #10B981)';
                    erpAutoFillBadge.style.display = 'inline-flex';
                } else if (erpUserIdInput) {
                    erpUserIdInput.value = 'Not mapped';
                    erpUserIdInput.style.borderColor = 'var(--admin-warning, #F59E0B)';
                    erpUserIdInput.style.color = 'var(--admin-warning, #F59E0B)';
                    erpAutoFillBadge.style.display = 'none';
                }
                
                if (data.employee.unit_id && unitSelect) {
                    unitSelect.value = data.employee.unit_id;
                    markAutoFilled(unitSelect, true);
                    loadDepartments(data.employee.unit_id, data.employee.department_id, true);
                }
                // Auto-fill Error Type if available (but user can change it)
                if (data.employee.error_type && errorTypeSelect) {
                    errorTypeSelect.value = data.employee.error_type;
                }
                
                // Lock fields after auto-fill
                lockFields(true);
                
            } else {
                showFetchStatus('not-found', data.message || 'Employee not found.');
                unlockAndClearFields();
                if (erpUserIdInput) {
                    erpUserIdInput.value = '';
                    erpUserIdInput.style.borderColor = '';
                    erpUserIdInput.style.color = '';
                }
                lockFields(false);
            }
        })
        .catch(function() {
            showFetchStatus('not-found', 'Error fetching employee.');
            unlockAndClearFields();
            if (erpUserIdInput) {
                erpUserIdInput.value = '';
                erpUserIdInput.style.borderColor = '';
                erpUserIdInput.style.color = '';
            }
            lockFields(false);
        });
    }
    
    function loadDepartments(unitId, selectedDeptId, lockAfterLoad) {
        lockAfterLoad = lockAfterLoad || false;
        var deptLoading = document.getElementById('dept_loading');
        
        if (!unitId) {
            departmentSelect.innerHTML = '<option value="">Select Unit First</option>';
            return;
        }
        
        if (deptLoading) deptLoading.style.display = 'block';
        departmentSelect.innerHTML = '<option value="">Loading...</option>';
        
        fetch('/ajax/get-departments/?unit_id=' + unitId, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            departmentSelect.innerHTML = '<option value="">Select Department</option>';
            if (data.departments && data.departments.length) {
                data.departments.forEach(function(d) {
                    var opt = document.createElement('option');
                    opt.value = d.id;
                    opt.textContent = d.name;
                    if (selectedDeptId && d.id == selectedDeptId) {
                        opt.selected = true;
                    }
                    departmentSelect.appendChild(opt);
                });
                // Lock department if employee is fetched and lockAfterLoad is true
                if (lockAfterLoad && isEmployeeFetched) {
                    departmentSelect.setAttribute('aria-disabled', 'true');
                    departmentSelect.style.pointerEvents = 'none';
                    departmentSelect.classList.add('field-locked');
                } else {
                    departmentSelect.removeAttribute('aria-disabled');
                    departmentSelect.style.pointerEvents = '';
                    departmentSelect.classList.remove('field-locked');
                }
            } else {
                departmentSelect.innerHTML += '<option value="">No departments available</option>';
                departmentSelect.removeAttribute('aria-disabled');
                departmentSelect.style.pointerEvents = '';
                departmentSelect.classList.remove('field-locked');
            }
            if (deptLoading) deptLoading.style.display = 'none';
        })
        .catch(function() {
            departmentSelect.innerHTML = '<option value="">Error loading departments</option>';
            if (deptLoading) deptLoading.style.display = 'none';
        });
    }
    
    // ============================================================
    // EVENT LISTENERS
    // ============================================================
    
    // Unit select change - load departments
    if (unitSelect) {
        unitSelect.addEventListener('change', function() {
            // If unit is disabled (locked), don't allow changes
            if (this.hasAttribute('disabled')) {
                var currentVal = this.value;
                var prevVal = this.getAttribute('data-locked-value') || '';
                if (currentVal !== prevVal) {
                    this.value = prevVal;
                }
                return;
            }
            
            if (!isEmployeeFetched) {
                loadDepartments(this.value, null, false);
            } else {
                loadDepartments(this.value, departmentSelect.value, true);
            }
        });
    }
    
    // Employee ID input
    if (empIdInput) {
        empIdInput.addEventListener('input', function() {
            clearTimeout(fetchTimeout);
            var value = this.value.trim();
            if (value.length >= 2) {
                fetchTimeout = setTimeout(function() {
                    fetchEmployeeDetails(value);
                }, 500);
            } else {
                showFetchStatus('');
                unlockAndClearFields();
                lockFields(false);
                isEmployeeFetched = false;
                if (erpUserIdInput) {
                    erpUserIdInput.value = '';
                    erpUserIdInput.style.borderColor = '';
                    erpUserIdInput.style.color = '';
                }
            }
        });
        
        empIdInput.addEventListener('blur', function() {
            var value = this.value.trim();
            if (value.length >= 2) {
                fetchEmployeeDetails(value);
            }
        });
    }
    
    // Prevent editing locked fields - revert to previous value if user tries to change
    [unitSelect, departmentSelect].forEach(function(field) {
        if (field) {
            field.addEventListener('change', function() {
                if (this.hasAttribute('disabled')) {
                    var currentVal = this.value;
                    var prevVal = this.getAttribute('data-locked-value') || '';
                    if (currentVal !== prevVal) {
                        this.value = prevVal;
                    }
                } else {
                    // Store current value as locked value when not locked
                    this.setAttribute('data-locked-value', this.value);
                }
            });
        }
    });
    
    // ============================================================
    // COUNTERS - Counts characters, NOT words
    // ============================================================
    function setupCounter(inputId, counterId, maxLen) {
        maxLen = maxLen || null;
        var input = document.getElementById(inputId);
        var counter = document.getElementById(counterId);
        if (!input || !counter) return;
        
        input.addEventListener('input', function() {
            var text = this.value;
            
            if (inputId === 'id_description') {
                var charCount = text.length;
                counter.textContent = charCount + ' characters (minimum 10)';
                counter.className = charCount < 10 ? 'char-counter danger' : 'char-counter';
            } else {
                var count = text.length;
                if (maxLen) {
                    counter.textContent = count + ' / ' + maxLen;
                    counter.className = count > maxLen * 0.85 ? 'char-counter danger' : 'char-counter';
                } else {
                    counter.textContent = count + ' characters';
                }
            }
        });
        input.dispatchEvent(new Event('input'));
    }
    
    setupCounter('id_screen_number', 'screen_counter');
    setupCounter('id_subject', 'subject_counter', 150);
    setupCounter('id_description', 'desc_counter');
    
    // ============================================================
    // ROLE TOGGLE - Show/Hide Admin Reason
    // ============================================================
    var roleRadios = document.querySelectorAll('input[name="created_by_role"]');
    var reasonContainer = document.getElementById('admin_reason_container');
    
    if (roleRadios.length && reasonContainer) {
        function toggleReason() {
            var selected = document.querySelector('input[name="created_by_role"]:checked');
            reasonContainer.style.display = (selected && selected.value === 'Admin') ? 'block' : 'none';
        }
        roleRadios.forEach(function(r) {
            r.addEventListener('change', toggleReason);
        });
        toggleReason();
    }

    // ============================================================
    // ATTACHMENT MANAGEMENT - WITH VALIDATION
    // ============================================================
    const MAX_ATTACHMENTS = 3;
    
    const attachmentContainer = document.getElementById('attachmentContainer');
    const addAttachmentBtn = document.getElementById('addAttachmentBtn');
    const attachmentCounter = document.getElementById('attachmentCounter');
    
    const wrapper1 = document.getElementById('attachmentWrapper1');
    const wrapper2 = document.getElementById('attachmentWrapper2');
    const wrapper3 = document.getElementById('attachmentWrapper3');
    
    const fileInput1 = document.getElementById('id_attachment_1');
    const fileInput2 = document.getElementById('id_attachment_2');
    const fileInput3 = document.getElementById('id_attachment_3');
    
    const status1 = document.getElementById('status1');
    const status2 = document.getElementById('status2');
    const status3 = document.getElementById('status3');
    
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
            statusText.textContent = fileName + ' (' + fileSize + ' KB)';
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
            statusText.textContent = 'No file selected';
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
    
    fileInput1.addEventListener('change', function() {
        updateAttachmentStatus(wrapper1, fileInput1, status1, 1);
        checkAndEnableAddButton();
    });
    
    fileInput2.addEventListener('change', function() {
        updateAttachmentStatus(wrapper2, fileInput2, status2, 2);
        checkAndEnableAddButton();
    });
    
    fileInput3.addEventListener('change', function() {
        updateAttachmentStatus(wrapper3, fileInput3, status3, 3);
        checkAndEnableAddButton();
    });
    
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
                text.textContent = 'No file selected';
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
            }
        }
        
        checkAndEnableAddButton();
    });
    
    updateAttachmentStatus(wrapper1, fileInput1, status1, 1);
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
    // FORM SUBMISSION VALIDATION - Minimum 10 characters
    // ============================================================
    var form = document.getElementById('ticketForm');
    var submitBtn = document.getElementById('submitBtn');
    
    if (form && submitBtn) {
        form.addEventListener('submit', function(e) {
            var description = document.getElementById('id_description');
            if (description) {
                var charCount = description.value.length;
                if (charCount < 10) {
                    e.preventDefault();
                    alert('Description must contain at least 10 characters. Current: ' + charCount + ' characters.');
                    description.focus();
                    return false;
                }
            }
            
            var roleSelect = document.querySelector('input[name="created_by_role"]:checked');
            var adminReason = document.getElementById('id_admin_creation_reason');
            if (roleSelect && roleSelect.value === 'Admin' && adminReason) {
                if (!adminReason.value.trim()) {
                    e.preventDefault();
                    alert('Admin Creation Reason is required when creating ticket as Admin.');
                    adminReason.focus();
                    return false;
                }
            }
            
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.7';
        });
    }
    
    // ============================================================
    // THEME SYNC - FIXED for dropdown visibility
    // ============================================================
    function syncInputTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, .form-select, textarea, input[type="text"], input[type="email"], input[type="tel"], input[type="number"], select, input[type="file"]');
        
        inputs.forEach(function(input) {
            input.style.display = 'none';
            void input.offsetHeight;
            input.style.display = '';
            
            if (isDark) {
                if (!input.classList.contains('field-auto-filled') && !input.classList.contains('field-locked')) {
                    input.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
                    input.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    input.style.color = '#E8EDF5';
                }
                if (input.tagName === 'SELECT') {
                    input.style.backgroundColor = '#1A1A2E';
                    input.style.color = '#E8EDF5';
                    input.style.backgroundImage = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%238A9AB8' d='M6 8L0 0h12z'/%3E%3C/svg%3E\")";
                    input.style.backgroundRepeat = 'no-repeat';
                    input.style.backgroundPosition = 'right 12px center';
                    input.style.backgroundSize = '12px 8px';
                    input.style.paddingRight = '35px';
                    input.style.webkitAppearance = 'none';
                    input.style.mozAppearance = 'none';
                    input.style.appearance = 'none';
                }
            } else {
                if (!input.classList.contains('field-auto-filled') && !input.classList.contains('field-locked')) {
                    input.style.backgroundColor = '';
                    input.style.borderColor = '';
                    input.style.color = '';
                }
                if (input.tagName === 'SELECT') {
                    input.style.backgroundColor = '';
                    input.style.color = '';
                    input.style.backgroundImage = '';
                    input.style.backgroundRepeat = '';
                    input.style.backgroundPosition = '';
                    input.style.backgroundSize = '';
                    input.style.paddingRight = '';
                    input.style.webkitAppearance = '';
                    input.style.mozAppearance = '';
                    input.style.appearance = '';
                }
            }
        });
        
        if (isDark) {
            var selectElements = document.querySelectorAll('select');
            selectElements.forEach(function(select) {
                select.style.colorScheme = 'dark';
                var options = select.querySelectorAll('option');
                options.forEach(function(opt) {
                    opt.style.backgroundColor = '#1A1A2E';
                    opt.style.color = '#E8EDF5';
                });
            });
        } else {
            var selectElements = document.querySelectorAll('select');
            selectElements.forEach(function(select) {
                select.style.colorScheme = 'light';
                var options = select.querySelectorAll('option');
                options.forEach(function(opt) {
                    opt.style.backgroundColor = '';
                    opt.style.color = '';
                });
            });
        }
    }
    
    var themeToggleBtn = document.getElementById('themeToggleFloating');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            setTimeout(syncInputTheme, 150);
        });
    }
    
    var themeObserver = new MutationObserver(function() {
        syncInputTheme();
    });
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
    
    var mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', function() {
        setTimeout(syncInputTheme, 150);
    });
    
    setTimeout(syncInputTheme, 300);
});