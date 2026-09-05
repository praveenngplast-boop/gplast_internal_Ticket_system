document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // BULK UPLOAD - Mobile and Email are OPTIONAL
    // ============================================================
    var fileInput = document.getElementById('bulkExcelFile');
    var uploadForm = document.getElementById('bulkUploadForm');
    var errorContainer = document.getElementById('uploadErrorContainer');
    var errorList = document.getElementById('uploadErrorList');
    var errorTitle = document.getElementById('uploadErrorTitle');

    if (fileInput && uploadForm) {
        fileInput.addEventListener('change', function(e) {
            var file = this.files[0];
            if (!file) return;

            var actionUrl = uploadForm.getAttribute('action') || uploadForm.action;

            var validExtensions = ['.xlsx', '.xls', '.csv'];
            var fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!validExtensions.includes(fileExt)) {
                alert('Invalid file format. Only .xlsx, .xls, and .csv files are supported.');
                this.value = '';
                return;
            }

            var formData = new FormData();
            formData.append('excel_file', file);
            formData.append('action', 'bulk_upload');

            var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken.value);
            }

            this.disabled = true;
            if (errorContainer) {
                errorContainer.classList.remove('show');
            }

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    alert(data.message || 'Employees uploaded successfully!');
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                } else {
                    if (errorContainer) {
                        errorContainer.classList.add('show');
                    }
                    if (errorTitle) {
                        errorTitle.textContent = data.message || 'Upload failed';
                    }
                    if (errorList) {
                        errorList.innerHTML = '';

                        if (data.errors && data.errors.length > 0) {
                            data.errors.forEach(function(err) {
                                var li = document.createElement('li');
                                li.innerHTML = `
                                    <i class="fa-solid fa-circle-exclamation"></i>
                                    <span>
                                        <span class="row-info">Row ${err.row}:</span>
                                        ${err.message}
                                    </span>
                                `;
                                errorList.appendChild(li);
                            });
                        } else {
                            var li = document.createElement('li');
                            li.innerHTML = `
                                <i class="fa-solid fa-circle-exclamation"></i>
                                <span>${data.message || 'Unknown error occurred'}</span>
                            `;
                            errorList.appendChild(li);
                        }
                    }

                    if (errorContainer) {
                        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            })
            .catch(function(error) {
                console.error('Upload error:', error);
                if (errorContainer) {
                    errorContainer.classList.add('show');
                }
                if (errorTitle) {
                    errorTitle.textContent = 'Network Error';
                }
                if (errorList) {
                    errorList.innerHTML = `
                        <li>
                            <i class="fa-solid fa-circle-exclamation"></i>
                            <span>Network error. Please try again.</span>
                        </li>
                    `;
                }
            })
            .finally(function() {
                fileInput.disabled = false;
                fileInput.value = '';
            });
        });
    }

    // ============================================================
    // ADD EMPLOYEE - Mobile is OPTIONAL (only validate if provided)
    // ============================================================
    var addEmpMobileInput = document.querySelector('#addEmployeeModal input[name="mobile"]');
    var addEmpForm = document.querySelector('#addEmployeeModal form');
    var addMobileError = document.getElementById('addMobileError');

    if (addEmpMobileInput && addEmpForm) {
        // Allow only digits
        addEmpMobileInput.addEventListener('input', function() {
            var val = this.value;
            this.value = val.replace(/\D/g, '');

            // ✅ Only validate if value is provided
            if (this.value.length > 0 && (this.value.length !== 10 || !/^\d{10}$/.test(this.value))) {
                if (addMobileError) {
                    addMobileError.style.display = 'block';
                    addMobileError.textContent = 'Mobile number must be exactly 10 digits';
                }
                this.style.borderColor = '#EF4444';
            } else {
                if (addMobileError) {
                    addMobileError.style.display = 'none';
                }
                this.style.borderColor = '';
            }
        });

        addEmpForm.addEventListener('submit', function(e) {
            var mobileVal = addEmpMobileInput.value.trim();
            // ✅ Allow empty OR exactly 10 digits
            if (mobileVal.length > 0 && !/^\d{10}$/.test(mobileVal)) {
                e.preventDefault();
                if (addMobileError) {
                    addMobileError.style.display = 'block';
                    addMobileError.textContent = 'Mobile number must be exactly 10 digits';
                }
                addEmpMobileInput.style.borderColor = '#EF4444';
                addEmpMobileInput.focus();
                alert('Please enter exactly 10 digits for Mobile number or leave it empty.');
                return false;
            }
            return true;
        });
    }

    // ============================================================
    // ADD EMPLOYEE - Email is OPTIONAL (only validate if provided)
    // ============================================================
    var addEmpEmailInput = document.querySelector('#addEmployeeModal input[name="email"]');
    var addEmailError = document.getElementById('addEmailError');

    if (addEmpEmailInput) {
        addEmpEmailInput.addEventListener('input', function() {
            var val = this.value.trim();
            // ✅ Only validate if value is provided
            if (val.length > 0 && (val.indexOf('@') === -1 || val.indexOf('.') === -1)) {
                if (addEmailError) {
                    addEmailError.style.display = 'block';
                    addEmailError.textContent = 'Please enter a valid email address';
                }
                this.style.borderColor = '#EF4444';
            } else {
                if (addEmailError) {
                    addEmailError.style.display = 'none';
                }
                this.style.borderColor = '';
            }
        });
    }

    // ============================================================
    // EDIT EMPLOYEE - Mobile is OPTIONAL (only validate if provided)
    // ============================================================
    var editEmpMobileInput = document.getElementById('edit_emp_mobile');
    var editEmpForm = document.querySelector('#editEmployeeModal form');
    var editMobileError = document.getElementById('editMobileError');

    if (editEmpMobileInput && editEmpForm) {
        // Allow only digits
        editEmpMobileInput.addEventListener('input', function() {
            var val = this.value;
            this.value = val.replace(/\D/g, '');

            // ✅ Only validate if value is provided
            if (this.value.length > 0 && (this.value.length !== 10 || !/^\d{10}$/.test(this.value))) {
                if (editMobileError) {
                    editMobileError.style.display = 'block';
                    editMobileError.textContent = 'Mobile number must be exactly 10 digits';
                }
                this.style.borderColor = '#EF4444';
            } else {
                if (editMobileError) {
                    editMobileError.style.display = 'none';
                }
                this.style.borderColor = '';
            }
        });

        editEmpForm.addEventListener('submit', function(e) {
            var mobileVal = editEmpMobileInput.value.trim();
            // ✅ Allow empty OR exactly 10 digits
            if (mobileVal.length > 0 && !/^\d{10}$/.test(mobileVal)) {
                e.preventDefault();
                if (editMobileError) {
                    editMobileError.style.display = 'block';
                    editMobileError.textContent = 'Mobile number must be exactly 10 digits';
                }
                editEmpMobileInput.style.borderColor = '#EF4444';
                editEmpMobileInput.focus();
                alert('Please enter exactly 10 digits for Mobile number or leave it empty.');
                return false;
            }
            return true;
        });
    }

    // ============================================================
    // EDIT EMPLOYEE - Email is OPTIONAL (only validate if provided)
    // ============================================================
    var editEmpEmailInput = document.getElementById('edit_emp_email');
    var editEmailError = document.getElementById('editEmailError');

    if (editEmpEmailInput) {
        editEmpEmailInput.addEventListener('input', function() {
            var val = this.value.trim();
            // ✅ Only validate if value is provided
            if (val.length > 0 && (val.indexOf('@') === -1 || val.indexOf('.') === -1)) {
                if (editEmailError) {
                    editEmailError.style.display = 'block';
                    editEmailError.textContent = 'Please enter a valid email address';
                }
                this.style.borderColor = '#EF4444';
            } else {
                if (editEmailError) {
                    editEmailError.style.display = 'none';
                }
                this.style.borderColor = '';
            }
        });
    }

    // ============================================================
    // DEPARTMENT FETCH FOR ADD EMPLOYEE
    // ============================================================
    var addEmpUnitSelect = document.querySelector('#addEmployeeModal select[name="unit"]');
    var addEmpDeptSelect = document.querySelector('#addEmployeeModal select[name="department"]');

    if (addEmpUnitSelect && addEmpDeptSelect) {
        addEmpUnitSelect.addEventListener('change', function() {
            var unitId = this.value;
            if (!unitId) {
                addEmpDeptSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
                addEmpDeptSelect.disabled = true;
                return;
            }
            addEmpDeptSelect.disabled = true;
            addEmpDeptSelect.innerHTML = '<option value="">Loading...</option>';
            fetch('/ajax/get-departments/?unit_id=' + unitId)
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    addEmpDeptSelect.innerHTML = '<option value="">-- Select Department --</option>';
                    if (data.departments && data.departments.length > 0) {
                        data.departments.forEach(function(d) {
                            var opt = document.createElement('option');
                            opt.value = d.id;
                            opt.textContent = d.name;
                            addEmpDeptSelect.appendChild(opt);
                        });
                        addEmpDeptSelect.disabled = false;
                    } else {
                        addEmpDeptSelect.innerHTML += '<option value="">No departments available</option>';
                        addEmpDeptSelect.disabled = true;
                    }
                })
                .catch(function() {
                    addEmpDeptSelect.innerHTML = '<option value="">Error loading departments</option>';
                    addEmpDeptSelect.disabled = true;
                });
        });
    }

    // ============================================================
    // DEPARTMENT FETCH FOR EDIT EMPLOYEE
    // ============================================================
    var editEmpUnitSelect = document.getElementById('edit_emp_unit');
    var editEmpDeptSelect = document.getElementById('edit_emp_dept');

    if (editEmpUnitSelect && editEmpDeptSelect) {
        editEmpUnitSelect.addEventListener('change', function() {
            var unitId = this.value;
            if (!unitId) {
                editEmpDeptSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
                editEmpDeptSelect.disabled = true;
                return;
            }
            editEmpDeptSelect.disabled = true;
            editEmpDeptSelect.innerHTML = '<option value="">Loading...</option>';
            fetch('/ajax/get-departments/?unit_id=' + unitId)
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    editEmpDeptSelect.innerHTML = '<option value="">-- Select Department --</option>';
                    if (data.departments && data.departments.length > 0) {
                        data.departments.forEach(function(d) {
                            var opt = document.createElement('option');
                            opt.value = d.id;
                            opt.textContent = d.name;
                            editEmpDeptSelect.appendChild(opt);
                        });
                        editEmpDeptSelect.disabled = false;
                    } else {
                        editEmpDeptSelect.innerHTML += '<option value="">No departments available</option>';
                        editEmpDeptSelect.disabled = true;
                    }
                })
                .catch(function() {
                    editEmpDeptSelect.innerHTML = '<option value="">Error loading departments</option>';
                    editEmpDeptSelect.disabled = true;
                });
        });
    }

    // ============================================================
    // PREFILL EDIT EMPLOYEE MODAL
    // ============================================================
    var editModal = document.getElementById('editEmployeeModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function(e) {
            var btn = e.relatedTarget;
            document.getElementById('edit_emp_id').value = btn.getAttribute('data-id');
            document.getElementById('edit_emp_empid').value = btn.getAttribute('data-empid');
            document.getElementById('edit_emp_name').value = btn.getAttribute('data-name');
            document.getElementById('edit_emp_mobile').value = btn.getAttribute('data-mobile') || '';
            document.getElementById('edit_emp_email').value = btn.getAttribute('data-email') || '';
            document.getElementById('edit_emp_unit').value = btn.getAttribute('data-unit') || '';
            document.getElementById('edit_emp_dept').value = btn.getAttribute('data-dept') || '';

            var canAssign = btn.getAttribute('data-canassign');
            var checkbox = document.getElementById('edit_emp_can_assign');
            if (checkbox) {
                checkbox.checked = canAssign === 'true';
            }

            // Trigger department load if unit is set
            var unitSelect = document.getElementById('edit_emp_unit');
            if (unitSelect && unitSelect.value) {
                var event = new Event('change');
                unitSelect.dispatchEvent(event);
                // Set department after load (delayed)
                setTimeout(function() {
                    var deptVal = btn.getAttribute('data-dept') || '';
                    if (deptVal) {
                        var deptSelect = document.getElementById('edit_emp_dept');
                        if (deptSelect) {
                            deptSelect.value = deptVal;
                        }
                    }
                }, 300);
            }
        });
    }

    // ============================================================
    // CONFIRMATION MODAL HANDLING
    // ============================================================
    var confirmModalEl = document.getElementById('confirmModal');
    var confirmBody = document.getElementById('confirmModalBody');
    var confirmYesBtn = document.getElementById('confirmModalYesBtn');
    var confirmCancelBtn = document.getElementById('confirmModalCancelBtn');
    var currentFormToSubmit = null;
    var isProcessing = false;

    function showConfirmModal(message, form) {
        if (!confirmModalEl || !confirmBody) return false;

        confirmBody.textContent = message || 'Are you sure?';
        currentFormToSubmit = form;

        if (window.bootstrap && window.bootstrap.Modal) {
            var modal = new bootstrap.Modal(confirmModalEl, {
                backdrop: 'static',
                keyboard: true,
                focus: true
            });
            modal.show();
            return true;
        } else {
            return confirm(message || 'Are you sure?');
        }
    }

    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var message = this.getAttribute('data-confirm');
            if (message) {
                e.preventDefault();
                e.stopPropagation();

                document.querySelectorAll('.modal.show').forEach(function(m) {
                    if (m.id !== 'confirmModal') {
                        var inst = bootstrap.Modal.getInstance(m);
                        if (inst) inst.hide();
                    }
                });

                showConfirmModal(message, this);
            }
        });
    });

    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (isProcessing || !currentFormToSubmit) return;
            isProcessing = true;

            var form = currentFormToSubmit;
            currentFormToSubmit = null;

            var modalInstance = bootstrap.Modal.getInstance(confirmModalEl);
            if (modalInstance) {
                modalInstance.hide();
            }

            setTimeout(function() {
                if (form && form.tagName === 'FORM') {
                    var submittedInput = document.createElement('input');
                    submittedInput.type = 'hidden';
                    submittedInput.name = '_confirmed';
                    submittedInput.value = 'true';
                    form.appendChild(submittedInput);

                    form.classList.add('confirmed');
                    form.submit();
                }
                isProcessing = false;
            }, 300);
        });
    }

    if (confirmCancelBtn) {
        confirmCancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            currentFormToSubmit = null;
            var modalInstance = bootstrap.Modal.getInstance(confirmModalEl);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }

    if (confirmModalEl) {
        confirmModalEl.addEventListener('hidden.bs.modal', function() {
            currentFormToSubmit = null;
            isProcessing = false;
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && confirmModalEl && confirmModalEl.classList.contains('show')) {
            currentFormToSubmit = null;
            isProcessing = false;
            var modalInstance = bootstrap.Modal.getInstance(confirmModalEl);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    });

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

    console.log('✅ Employees JS loaded - Mobile and Email are OPTIONAL');
});