/**
 * ============================================
 * TICKET FORM HANDLING - COMPLETE SOLUTION
 * ============================================
 * 
 * Handles:
 * - Character counters for subject, description, screen
 * - Dynamic departments dropdown
 * - Attachment file validation
 * - Admin creation fields toggle
 * - Employee ID auto-fetch with ERP User ID
 * - Form submission validation
 * - Unit Head ticket form support
 * 
 * @version 1.1.0
 * @author GPLAST Team
 */

document.addEventListener('DOMContentLoaded', function() {

    // ============================================
    // 1. CHARACTER COUNTERS
    // ============================================
    
    // Subject Counter (max 150)
    const subjectInput = document.getElementById('id_subject');
    const subjectCounter = document.getElementById('subject_counter');
    if (subjectInput && subjectCounter) {
        subjectInput.maxLength = 150;
        subjectInput.addEventListener('input', function() {
            const count = this.value.length;
            const counterSpan = subjectCounter.querySelector('.counter-number');
            if (counterSpan) {
                counterSpan.textContent = count;
            } else {
                subjectCounter.textContent = `${count} / 150`;
            }
            // Add warning when approaching limit
            if (count > 130) {
                subjectCounter.classList.add('text-warning');
                subjectCounter.classList.remove('text-danger');
            }
            if (count > 145) {
                subjectCounter.classList.remove('text-warning');
                subjectCounter.classList.add('text-danger');
            }
            if (count <= 130) {
                subjectCounter.classList.remove('text-warning', 'text-danger');
            }
        });
        // Trigger initial count
        subjectInput.dispatchEvent(new Event('input'));
    }

    // Description Counter (min 10)
    const descInput = document.getElementById('id_description');
    const descCounter = document.getElementById('desc_counter');
    if (descInput && descCounter) {
        descInput.addEventListener('input', function() {
            const count = this.value.length;
            const counterSpan = descCounter.querySelector('.counter-number');
            if (counterSpan) {
                counterSpan.textContent = count;
            } else {
                descCounter.textContent = `${count} characters (minimum 10)`;
            }
            if (count < 10) {
                descCounter.classList.add('text-danger');
                descCounter.classList.remove('text-success');
                descInput.style.borderColor = '#EF4444';
            } else {
                descCounter.classList.remove('text-danger');
                descCounter.classList.add('text-success');
                descInput.style.borderColor = '';
            }
        });
        // Trigger initial count
        descInput.dispatchEvent(new Event('input'));
    }

    // Screen Counter
    const screenInput = document.getElementById('id_screen_number');
    const screenCounter = document.getElementById('screen_counter');
    if (screenInput && screenCounter) {
        screenInput.addEventListener('input', function() {
            const count = this.value.length;
            const counterSpan = screenCounter.querySelector('.counter-number');
            if (counterSpan) {
                counterSpan.textContent = count;
            } else {
                screenCounter.textContent = `${count} characters`;
            }
        });
        // Trigger initial count
        screenInput.dispatchEvent(new Event('input'));
    }

    // ============================================
    // 2. DYNAMIC DEPARTMENTS DROPDOWN
    // ============================================
    const unitSelect = document.getElementById('id_unit');
    const deptSelect = document.getElementById('id_department');
    if (unitSelect && deptSelect) {
        // Function to update departments dropdown
        const updateDepartments = function() {
            const unitId = unitSelect.value;
            // Clear existing options
            deptSelect.innerHTML = '<option value="">---------</option>';
            
            if (!unitId) {
                deptSelect.disabled = true;
                return;
            }

            deptSelect.disabled = true;
            deptSelect.innerHTML = '<option value="">Loading...</option>';

            // Check if we are on the reports page to load both active and inactive depts
            const showAll = deptSelect.getAttribute('data-show-all') === 'true';
            const url = `/ajax/get-departments/?unit_id=${unitId}&show_all=${showAll}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    deptSelect.innerHTML = '<option value="">---------</option>';
                    if (data.departments && data.departments.length > 0) {
                        data.departments.forEach(dept => {
                            const option = document.createElement('option');
                            option.value = dept.id;
                            option.textContent = dept.name;
                            deptSelect.appendChild(option);
                        });
                        deptSelect.disabled = false;
                    } else {
                        deptSelect.innerHTML += '<option value="">No departments available</option>';
                        deptSelect.disabled = true;
                    }
                })
                .catch(err => {
                    console.error("Error fetching departments: ", err);
                    deptSelect.innerHTML = '<option value="">Error loading departments</option>';
                    deptSelect.disabled = true;
                });
        };

        unitSelect.addEventListener('change', updateDepartments);
        
        // If unit is pre-selected but department is empty, load departments
        if (unitSelect.value && deptSelect.children.length <= 1) {
            updateDepartments();
        }
    }

    // ============================================
    // 3. ATTACHMENT FILE VALIDATOR (Client-side)
    // ============================================
    const attachmentInputs = document.querySelectorAll('input[type="file"][name^="attachment_"]');
    attachmentInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;

            // Max 3MB (3 * 1024 * 1024 bytes)
            const maxSize = 3 * 1024 * 1024;
            // Allowed extensions
            const allowedExtensions = /(\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.png|\.jpg|\.jpeg|\.txt|\.csv|\.zip|\.rar)$/i;

            let errorMsg = "";

            if (file.size > maxSize) {
                errorMsg = "File size exceeds 3MB. Please select a smaller file.";
            } else if (!allowedExtensions.exec(file.name)) {
                errorMsg = "Unsupported file extension. Allowed formats: pdf, doc, docx, xls, xlsx, png, jpg, jpeg, txt, csv, zip, rar.";
            }

            if (errorMsg) {
                alert(errorMsg);
                this.value = ""; // Clear selection
                // Update status if exists
                const wrapper = this.closest('.attachment-wrapper');
                if (wrapper) {
                    const statusEl = wrapper.querySelector('.attachment-status');
                    if (statusEl) {
                        const icon = statusEl.querySelector('.status-icon');
                        const text = statusEl.querySelector('.status-text');
                        if (icon) icon.textContent = '❌';
                        if (text) {
                            text.textContent = 'Invalid file';
                            text.style.color = '#EF4444';
                            text.style.fontWeight = '600';
                        }
                    }
                }
            } else {
                // Update status
                const wrapper = this.closest('.attachment-wrapper');
                if (wrapper) {
                    const statusEl = wrapper.querySelector('.attachment-status');
                    if (statusEl) {
                        const icon = statusEl.querySelector('.status-icon');
                        const text = statusEl.querySelector('.status-text');
                        if (icon) icon.textContent = '✅';
                        if (text) {
                            text.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
                            text.style.color = '#22C55E';
                            text.style.fontWeight = '500';
                            text.className = 'status-text has-file';
                        }
                    }
                    // Show remove button
                    const removeBtn = wrapper.querySelector('.remove-attachment');
                    if (removeBtn) removeBtn.style.display = 'block';
                }
            }
        });
    });

    // ============================================
    // 4. ADMIN CREATION FIELDS TOGGLE
    // ============================================
    // In admin creation form, Reason is hidden/visible depending on "Created By"
    const roleRadios = document.getElementsByName('created_by_role');
    const reasonContainer = document.getElementById('admin_reason_container');
    const reasonSelect = document.getElementById('id_admin_creation_reason');

    if (roleRadios.length > 0 && reasonContainer && reasonSelect) {
        const toggleReason = function() {
            let selectedRole = "";
            for (let i = 0; i < roleRadios.length; i++) {
                if (roleRadios[i].checked) {
                    selectedRole = roleRadios[i].value;
                    break;
                }
            }

            if (selectedRole === 'Admin') {
                reasonContainer.style.display = 'block';
                reasonSelect.required = true;
                reasonSelect.disabled = false;
            } else {
                reasonContainer.style.display = 'none';
                reasonSelect.required = false;
                reasonSelect.disabled = true;
                reasonSelect.value = ""; // Clear selection
            }
        };

        for (let i = 0; i < roleRadios.length; i++) {
            roleRadios[i].addEventListener('change', toggleReason);
        }

        // Run once on load to initialize correctly
        toggleReason();
    }

    // ============================================
    // 5. EMPLOYEE ID AUTO-FETCH WITH ERP USER ID
    // ============================================
    const empIdInput = document.getElementById('id_employee_id');
    const empNameInput = document.getElementById('id_employee_name');
    const empMobileInput = document.getElementById('id_mobile');
    const empEmailInput = document.getElementById('id_email');
    const erpUserIdInput = document.getElementById('erp_user_id');
    const erpAutoFillBadge = document.getElementById('erpAutoFillBadge');

    if (empIdInput) {
        let fetchTimeout = null;

        empIdInput.addEventListener('input', function() {
            const value = this.value.trim().toUpperCase();
            
            // Clear previous timeout
            if (fetchTimeout) {
                clearTimeout(fetchTimeout);
                fetchTimeout = null;
            }

            // Only fetch if value has at least 2 characters
            if (value.length < 2) {
                // Clear auto-filled fields
                if (empNameInput) {
                    empNameInput.value = '';
                    empNameInput.classList.remove('field-auto-filled');
                }
                if (empMobileInput) {
                    empMobileInput.value = '';
                    empMobileInput.classList.remove('field-auto-filled');
                }
                if (empEmailInput) {
                    empEmailInput.value = '';
                    empEmailInput.classList.remove('field-auto-filled');
                }
                if (erpUserIdInput) {
                    erpUserIdInput.value = '';
                    erpUserIdInput.style.borderColor = '';
                    erpUserIdInput.style.color = '';
                }
                if (erpAutoFillBadge) {
                    erpAutoFillBadge.style.display = 'none';
                }
                // Clear validation badges
                const validationBadge = document.getElementById('validationBadge');
                if (validationBadge) validationBadge.style.display = 'none';
                const mismatchWarning = document.getElementById('mismatchWarning');
                if (mismatchWarning) mismatchWarning.classList.remove('show');
                const employeeValid = document.getElementById('employeeValid');
                if (employeeValid) employeeValid.classList.remove('show');
                const empNotFound = document.getElementById('empNotFound');
                if (empNotFound) empNotFound.classList.remove('show');
                return;
            }

            // Show loading state
            const fetchStatus = document.getElementById('empFetchStatus');
            if (fetchStatus) {
                fetchStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                fetchStatus.className = 'emp-fetch-status loading';
            }

            // Debounce fetch
            fetchTimeout = setTimeout(function() {
                const unitId = document.getElementById('id_unit') ? document.getElementById('id_unit').value : '';
                const deptId = document.getElementById('id_department') ? document.getElementById('id_department').value : '';
                
                let url = `/ajax/get-employee/?employee_id=${encodeURIComponent(value)}`;
                if (unitId) url += `&unit_id=${encodeURIComponent(unitId)}`;
                if (deptId) url += `&department_id=${encodeURIComponent(deptId)}`;

                fetch(url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    const fetchStatus = document.getElementById('empFetchStatus');
                    const validationBadge = document.getElementById('validationBadge');
                    const mismatchWarning = document.getElementById('mismatchWarning');
                    const employeeValid = document.getElementById('employeeValid');
                    const empNotFound = document.getElementById('empNotFound');

                    if (data.found && !data.mismatch) {
                        // Employee found and matches
                        const emp = data.employee;
                        
                        if (empNameInput) {
                            empNameInput.value = emp.employee_name || '';
                            empNameInput.classList.add('field-auto-filled');
                        }
                        if (empMobileInput && emp.mobile) {
                            empMobileInput.value = emp.mobile;
                            empMobileInput.classList.add('field-auto-filled');
                        } else if (empMobileInput) {
                            empMobileInput.value = '';
                            empMobileInput.classList.remove('field-auto-filled');
                        }
                        if (empEmailInput && emp.email) {
                            empEmailInput.value = emp.email;
                            empEmailInput.classList.add('field-auto-filled');
                        } else if (empEmailInput) {
                            empEmailInput.value = '';
                            empEmailInput.classList.remove('field-auto-filled');
                        }
                        
                        // ✅ NEW: Set ERP User ID
                        if (erpUserIdInput && emp.erp_user_id) {
                            erpUserIdInput.value = emp.erp_user_id;
                            erpUserIdInput.style.borderColor = '#22C55E';
                            erpUserIdInput.style.color = '#22C55E';
                            if (erpAutoFillBadge) {
                                erpAutoFillBadge.style.display = 'inline-block';
                                erpAutoFillBadge.innerHTML = '<i class="fa-solid fa-magic me-1"></i>Auto-filled';
                            }
                        } else if (erpUserIdInput) {
                            erpUserIdInput.value = 'Not mapped';
                            erpUserIdInput.style.borderColor = '#F59E0B';
                            erpUserIdInput.style.color = '#F59E0B';
                            if (erpAutoFillBadge) {
                                erpAutoFillBadge.style.display = 'none';
                            }
                        }

                        if (fetchStatus) {
                            fetchStatus.innerHTML = '<i class="fa-regular fa-circle-check"></i>';
                            fetchStatus.className = 'emp-fetch-status found';
                        }
                        if (validationBadge) {
                            validationBadge.style.display = 'inline-block';
                            validationBadge.className = 'validation-badge valid';
                            validationBadge.innerHTML = '<i class="fa-regular fa-check-circle me-1"></i>Valid';
                        }
                        if (employeeValid) employeeValid.classList.add('show');
                        if (mismatchWarning) mismatchWarning.classList.remove('show');
                        if (empNotFound) empNotFound.classList.remove('show');

                        // ✅ NEW: Fetch screens for ERP ID
                        if (emp.erp_user_id) {
                            fetchScreensForErp(emp.erp_user_id);
                        }

                        // Lock fields if this is a credentialed user
                        const form = document.getElementById('ticketForm');
                        if (form && form.getAttribute('data-is-credentialed') === 'true') {
                            lockFields(true);
                        }

                    } else if (data.found && data.mismatch) {
                        // Employee found but mismatch
                        if (fetchStatus) {
                            fetchStatus.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
                            fetchStatus.className = 'emp-fetch-status mismatch';
                        }
                        if (validationBadge) {
                            validationBadge.style.display = 'inline-block';
                            validationBadge.className = 'validation-badge invalid';
                            validationBadge.innerHTML = '<i class="fa-solid fa-times-circle me-1"></i>Invalid';
                        }
                        if (mismatchWarning) {
                            mismatchWarning.classList.add('show');
                            const msg = mismatchWarning.querySelector('span');
                            if (msg) msg.textContent = data.message || 'Employee belongs to a different department/unit.';
                        }
                        if (employeeValid) employeeValid.classList.remove('show');
                        if (empNotFound) empNotFound.classList.remove('show');
                        
                        // Clear fields on mismatch
                        if (empNameInput) {
                            empNameInput.value = '';
                            empNameInput.classList.remove('field-auto-filled');
                        }
                        if (empMobileInput) {
                            empMobileInput.value = '';
                            empMobileInput.classList.remove('field-auto-filled');
                        }
                        if (empEmailInput) {
                            empEmailInput.value = '';
                            empEmailInput.classList.remove('field-auto-filled');
                        }
                        if (erpUserIdInput) {
                            erpUserIdInput.value = '';
                            erpUserIdInput.style.borderColor = '';
                            erpUserIdInput.style.color = '';
                        }
                        if (erpAutoFillBadge) {
                            erpAutoFillBadge.style.display = 'none';
                        }

                    } else {
                        // Employee not found
                        if (fetchStatus) {
                            fetchStatus.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
                            fetchStatus.className = 'emp-fetch-status not-found';
                        }
                        if (validationBadge) {
                            validationBadge.style.display = 'inline-block';
                            validationBadge.className = 'validation-badge invalid';
                            validationBadge.innerHTML = '<i class="fa-solid fa-times-circle me-1"></i>Invalid';
                        }
                        if (empNotFound) {
                            empNotFound.classList.add('show');
                            const msg = empNotFound.querySelector('span');
                            if (msg) msg.textContent = data.message || 'Employee ID not found. Please check and try again.';
                        }
                        if (employeeValid) employeeValid.classList.remove('show');
                        if (mismatchWarning) mismatchWarning.classList.remove('show');
                        
                        // Clear fields on not found
                        if (empNameInput) {
                            empNameInput.value = '';
                            empNameInput.classList.remove('field-auto-filled');
                        }
                        if (empMobileInput) {
                            empMobileInput.value = '';
                            empMobileInput.classList.remove('field-auto-filled');
                        }
                        if (empEmailInput) {
                            empEmailInput.value = '';
                            empEmailInput.classList.remove('field-auto-filled');
                        }
                        if (erpUserIdInput) {
                            erpUserIdInput.value = '';
                            erpUserIdInput.style.borderColor = '';
                            erpUserIdInput.style.color = '';
                        }
                        if (erpAutoFillBadge) {
                            erpAutoFillBadge.style.display = 'none';
                        }
                        // Clear screens
                        const screenSelect = document.getElementById('id_screen_number');
                        if (screenSelect) {
                            screenSelect.innerHTML = '<option value="">Please enter valid Employee ID first</option>';
                        }
                    }
                })
                .catch(err => {
                    console.error('Error fetching employee details:', err);
                    const fetchStatus = document.getElementById('empFetchStatus');
                    if (fetchStatus) {
                        fetchStatus.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i>';
                        fetchStatus.className = 'emp-fetch-status not-found';
                    }
                });
            }, 500);
        });
    }

    // ============================================
    // 6. FETCH SCREENS FOR ERP ID
    // ============================================
    function fetchScreensForErp(erpUserId) {
        const screenSelect = document.getElementById('id_screen_number');
        if (!screenSelect) return;
        
        screenSelect.innerHTML = '<option value="">Loading screens...</option>';
        
        fetch('/ajax/get-screens-for-erp/?erp_user_id=' + encodeURIComponent(erpUserId))
            .then(res => res.json())
            .then(data => {
                if (data.success && data.screens && data.screens.length > 0) {
                    let options = '<option value="">Select Screen/Module</option>';
                    data.screens.forEach(s => {
                        options += `<option value="${s.screen_code}">${s.display}</option>`;
                    });
                    screenSelect.innerHTML = options;
                } else {
                    screenSelect.innerHTML = '<option value="">No screens mapped for this ERP ID</option>';
                }
            })
            .catch(err => {
                console.error("Failed to fetch screens", err);
                screenSelect.innerHTML = '<option value="">Error loading screens</option>';
            });
    }

    // ============================================
    // 7. LOCK FIELDS FUNCTION (for credentialed users)
    // ============================================
    function lockFields(lock) {
        const fields = ['id_unit', 'id_department', 'id_employee_name', 'id_mobile', 'id_email'];
        fields.forEach(function(fieldId) {
            const field = document.getElementById(fieldId);
            if (field) {
                if (lock) {
                    field.setAttribute('readonly', 'readonly');
                    field.classList.add('field-locked');
                } else {
                    field.removeAttribute('readonly');
                    field.classList.remove('field-locked');
                }
            }
        });
        
        // Lock select fields
        const selects = ['id_unit', 'id_department'];
        selects.forEach(function(selectId) {
            const select = document.getElementById(selectId);
            if (select) {
                if (lock) {
                    select.setAttribute('disabled', 'disabled');
                    select.classList.add('field-locked');
                } else {
                    select.removeAttribute('disabled');
                    select.classList.remove('field-locked');
                }
            }
        });
    }

    // ============================================
    // 8. FORM SUBMISSION VALIDATION
    // ============================================
    const ticketForm = document.getElementById('ticketForm');
    if (ticketForm) {
        ticketForm.addEventListener('submit', function(e) {
            // Check if employee is validated
            const empIdInput = document.getElementById('id_employee_id');
            const validationBadge = document.getElementById('validationBadge');
            
            if (empIdInput && empIdInput.value.trim()) {
                // If validation badge shows invalid, prevent submission
                if (validationBadge && validationBadge.classList.contains('invalid')) {
                    e.preventDefault();
                    alert('⚠️ Please enter a valid Employee ID before submitting.');
                    empIdInput.focus();
                    return false;
                }
            }
            
            // Check if at least one attachment is required (for employee ticket creation)
            const isEmployee = window.location.pathname.includes('/create-ticket/');
            if (isEmployee) {
                const attachment1 = document.getElementById('id_attachment_1');
                if (attachment1 && (!attachment1.files || attachment1.files.length === 0)) {
                    e.preventDefault();
                    alert('❌ Attachment 1 is required. Please select a file to upload.');
                    attachment1.focus();
                    return false;
                }
            }
        });
    }

    // ============================================
    // 9. THEME SYNC FOR FORM ELEMENTS
    // ============================================
    function updateFormTheme() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const inputs = document.querySelectorAll('.form-control, .form-select, input, select, textarea');
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

    const themeToggleBtn = document.getElementById('themeToggleFloating');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            setTimeout(updateFormTheme, 100);
        });
    }

    const observer = new MutationObserver(function(mutations) {
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

    // ============================================
    // 10. UNIT HEAD DASHBOARD CHART SUPPORT
    // ============================================
    // Check if we're on the unit head dashboard
    const isUnitHeadDashboard = window.location.pathname.includes('/unit-head/dashboard/');
    if (isUnitHeadDashboard && window.initCharts) {
        // Charts will be initialized by the dashboard template
        console.log('📊 Unit Head Dashboard - Charts ready for initialization');
    }

    console.log('✅ Ticket form handlers initialized successfully!');

});