document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // PASSWORD TOGGLE FUNCTION
    // ============================================================
    document.querySelectorAll('.password-toggle-icon').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            var targetId = this.getAttribute('data-toggle');
            if (!targetId) return;
            
            var input = document.getElementById(targetId);
            if (!input) return;
            
            var isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');
            
            var icon = this.querySelector('i');
            if (icon) {
                icon.className = isPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
            }
            
            input.focus();
        });
    });

    // ============================================================
    // PREFILL EDIT MODAL
    // ============================================================
    var editModal = document.getElementById('editUnitHeadModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function(e) {
            var btn = e.relatedTarget;
            document.getElementById('edit_uh_id').value = btn.getAttribute('data-id');
            document.getElementById('edit_uh_username').value = btn.getAttribute('data-username');
            document.getElementById('edit_uh_name').value = btn.getAttribute('data-name');
            document.getElementById('edit_uh_email').value = btn.getAttribute('data-email');
            document.getElementById('edit_uh_unit').value = btn.getAttribute('data-unit');
            
            // Reset password fields
            document.getElementById('editPassword').value = '';
            document.getElementById('editConfirmPassword').value = '';
            document.getElementById('editPasswordError').style.display = 'none';
            
            var isActive = btn.getAttribute('data-active') === 'true';
            document.getElementById('edit_is_active').checked = isActive;
        });
    }

    // ============================================================
    // PASSWORD VALIDATION - ADD
    // ============================================================
    var addForm = document.getElementById('addUnitHeadForm');
    var addPassword = document.getElementById('addPassword');
    var addConfirm = document.getElementById('addConfirmPassword');
    var addPasswordError = document.getElementById('addPasswordError');
    var addSubmitBtn = document.getElementById('addSubmitBtn');

    if (addForm && addPassword && addConfirm) {
        // Real-time password validation
        addPassword.addEventListener('input', function() {
            if (this.value.length > 0 && this.value.length < 8) {
                this.style.borderColor = '#F59E0B';
            } else if (this.value.length >= 8) {
                this.style.borderColor = '#22C55E';
            } else {
                this.style.borderColor = '';
            }
            
            // Check if confirm matches
            if (addConfirm.value.length > 0) {
                if (this.value !== addConfirm.value) {
                    addPasswordError.style.display = 'block';
                    addConfirm.style.borderColor = '#EF4444';
                } else {
                    addPasswordError.style.display = 'none';
                    addConfirm.style.borderColor = '#22C55E';
                }
            }
        });

        addConfirm.addEventListener('input', function() {
            if (this.value.length > 0 && this.value !== addPassword.value) {
                addPasswordError.style.display = 'block';
                this.style.borderColor = '#EF4444';
            } else if (this.value.length > 0 && this.value === addPassword.value) {
                addPasswordError.style.display = 'none';
                this.style.borderColor = '#22C55E';
            } else {
                addPasswordError.style.display = 'none';
                this.style.borderColor = '';
            }
        });

        // Form submit validation
        addForm.addEventListener('submit', function(e) {
            var password = addPassword.value;
            var confirm = addConfirm.value;
            var isValid = true;
            var errorMsg = '';

            // Check password length
            if (password.length < 8) {
                isValid = false;
                errorMsg = 'Password must be at least 8 characters.';
                addPassword.style.borderColor = '#EF4444';
            }

            // Check password match
            if (password !== confirm) {
                isValid = false;
                errorMsg = 'Passwords do not match.';
                addPasswordError.style.display = 'block';
                addConfirm.style.borderColor = '#EF4444';
            }

            // Check username
            var username = addForm.querySelector('input[name="username"]');
            if (username && username.value.trim().length < 3) {
                isValid = false;
                errorMsg = 'Username must be at least 3 characters.';
                username.style.borderColor = '#EF4444';
            }

            // Check name
            var name = addForm.querySelector('input[name="name"]');
            if (name && name.value.trim().length === 0) {
                isValid = false;
                errorMsg = 'Name is required.';
                name.style.borderColor = '#EF4444';
            }

            // Check email
            var email = addForm.querySelector('input[name="email"]');
            if (email && email.value.trim().length > 0 && (email.value.indexOf('@') === -1 || email.value.indexOf('.') === -1)) {
                isValid = false;
                errorMsg = 'Please enter a valid email address.';
                email.style.borderColor = '#EF4444';
            }

            // Check unit
            var unit = addForm.querySelector('select[name="unit"]');
            if (unit && !unit.value) {
                isValid = false;
                errorMsg = 'Please select a unit.';
                unit.style.borderColor = '#EF4444';
            }

            if (!isValid) {
                e.preventDefault();
                alert(errorMsg);
                return false;
            }

            // Disable submit button to prevent double submission
            if (addSubmitBtn) {
                addSubmitBtn.disabled = true;
                addSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Adding...';
            }

            return true;
        });
    }

    // ============================================================
    // PASSWORD VALIDATION - EDIT
    // ============================================================
    var editForm = document.getElementById('editUnitHeadForm');
    var editPassword = document.getElementById('editPassword');
    var editConfirm = document.getElementById('editConfirmPassword');
    var editPasswordError = document.getElementById('editPasswordError');
    var editSubmitBtn = document.getElementById('editSubmitBtn');

    if (editForm && editPassword && editConfirm) {
        // Real-time validation for edit
        editPassword.addEventListener('input', function() {
            if (this.value.length > 0 && this.value.length < 8) {
                this.style.borderColor = '#F59E0B';
            } else if (this.value.length >= 8) {
                this.style.borderColor = '#22C55E';
            } else {
                this.style.borderColor = '';
            }
            
            if (editConfirm.value.length > 0) {
                if (this.value !== editConfirm.value) {
                    editPasswordError.style.display = 'block';
                    editConfirm.style.borderColor = '#EF4444';
                } else {
                    editPasswordError.style.display = 'none';
                    editConfirm.style.borderColor = '#22C55E';
                }
            }
        });

        editConfirm.addEventListener('input', function() {
            if (this.value.length > 0 && this.value !== editPassword.value) {
                editPasswordError.style.display = 'block';
                this.style.borderColor = '#EF4444';
            } else if (this.value.length > 0 && this.value === editPassword.value) {
                editPasswordError.style.display = 'none';
                this.style.borderColor = '#22C55E';
            } else {
                editPasswordError.style.display = 'none';
                this.style.borderColor = '';
            }
        });

        // Form submit validation for edit
        editForm.addEventListener('submit', function(e) {
            var password = editPassword.value;
            var confirm = editConfirm.value;
            var isValid = true;
            var errorMsg = '';

            // Only validate if password is provided
            if (password || confirm) {
                if (password.length < 8) {
                    isValid = false;
                    errorMsg = 'Password must be at least 8 characters.';
                    editPassword.style.borderColor = '#EF4444';
                }

                if (password !== confirm) {
                    isValid = false;
                    errorMsg = 'Passwords do not match.';
                    editPasswordError.style.display = 'block';
                    editConfirm.style.borderColor = '#EF4444';
                }
            }

            // Check username
            var username = editForm.querySelector('input[name="username"]');
            if (username && username.value.trim().length < 3) {
                isValid = false;
                errorMsg = 'Username must be at least 3 characters.';
                username.style.borderColor = '#EF4444';
            }

            // Check name
            var name = editForm.querySelector('input[name="name"]');
            if (name && name.value.trim().length === 0) {
                isValid = false;
                errorMsg = 'Name is required.';
                name.style.borderColor = '#EF4444';
            }

            // Check email
            var email = editForm.querySelector('input[name="email"]');
            if (email && email.value.trim().length > 0 && (email.value.indexOf('@') === -1 || email.value.indexOf('.') === -1)) {
                isValid = false;
                errorMsg = 'Please enter a valid email address.';
                email.style.borderColor = '#EF4444';
            }

            // Check unit
            var unit = editForm.querySelector('select[name="unit"]');
            if (unit && !unit.value) {
                isValid = false;
                errorMsg = 'Please select a unit.';
                unit.style.borderColor = '#EF4444';
            }

            if (!isValid) {
                e.preventDefault();
                alert(errorMsg);
                return false;
            }

            // Disable submit button to prevent double submission
            if (editSubmitBtn) {
                editSubmitBtn.disabled = true;
                editSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Saving...';
            }

            return true;
        });
    }

    // ============================================================
    // MODAL CLEANUP - Re-enable buttons when modal is closed
    // ============================================================
    var addModal = document.getElementById('addUnitHeadModal');
    if (addModal) {
        addModal.addEventListener('hidden.bs.modal', function() {
            if (addSubmitBtn) {
                addSubmitBtn.disabled = false;
                addSubmitBtn.innerHTML = 'Add Unit Head';
            }
            // Clear validation styles
            var inputs = addModal.querySelectorAll('.form-control, .form-select');
            inputs.forEach(function(input) {
                input.style.borderColor = '';
            });
            var errors = addModal.querySelectorAll('.text-danger');
            errors.forEach(function(err) {
                err.style.display = 'none';
            });
        });
    }

    var editModalEl = document.getElementById('editUnitHeadModal');
    if (editModalEl) {
        editModalEl.addEventListener('hidden.bs.modal', function() {
            if (editSubmitBtn) {
                editSubmitBtn.disabled = false;
                editSubmitBtn.innerHTML = 'Save Changes';
            }
            var inputs = editModalEl.querySelectorAll('.form-control, .form-select');
            inputs.forEach(function(input) {
                input.style.borderColor = '';
            });
            var errors = editModalEl.querySelectorAll('.text-danger');
            errors.forEach(function(err) {
                err.style.display = 'none';
            });
        });
    }

    // ============================================================
    // CONFIRMATION MODAL
    // ============================================================
    var confirmModalEl = document.getElementById('confirmModal');
    var confirmBody = document.getElementById('confirmModalBody');
    var confirmYesBtn = document.getElementById('confirmModalYesBtn');
    var confirmCancelBtn = document.getElementById('confirmModalCancelBtn');
    var currentFormToSubmit = null;
    var isProcessing = false;

    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var message = this.getAttribute('data-confirm');
            if (message) {
                e.preventDefault();
                e.stopPropagation();
                currentFormToSubmit = this;
                confirmBody.textContent = message || 'Are you sure?';
                var modal = new bootstrap.Modal(confirmModalEl);
                modal.show();
            }
        });
    });

    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', function() {
            if (isProcessing || !currentFormToSubmit) return;
            isProcessing = true;
            var form = currentFormToSubmit;
            currentFormToSubmit = null;
            var modalInstance = bootstrap.Modal.getInstance(confirmModalEl);
            if (modalInstance) modalInstance.hide();
            setTimeout(function() {
                if (form && form.tagName === 'FORM') {
                    form.submit();
                }
                isProcessing = false;
            }, 300);
        });
    }

    if (confirmCancelBtn) {
        confirmCancelBtn.addEventListener('click', function() {
            currentFormToSubmit = null;
            var modalInstance = bootstrap.Modal.getInstance(confirmModalEl);
            if (modalInstance) modalInstance.hide();
        });
    }

    if (confirmModalEl) {
        confirmModalEl.addEventListener('hidden.bs.modal', function() {
            currentFormToSubmit = null;
            isProcessing = false;
        });
    }

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

    console.log('✅ Unit Heads JS loaded successfully');
}); 