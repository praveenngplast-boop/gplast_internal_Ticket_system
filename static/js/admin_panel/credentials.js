document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // PASSWORD TOGGLE
    // ============================================================
    document.querySelectorAll('.password-toggle-icon').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            var inputId = this.getAttribute('data-target');
            if (!inputId) return;

            var input = document.getElementById(inputId);
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
    // DEPARTMENT FETCH FOR ADD CREDENTIAL
    // ============================================================
    var credUnitSelect = document.getElementById('credUnit');
    var credDeptSelect = document.getElementById('credDept');

    if (credUnitSelect && credDeptSelect) {
        credUnitSelect.addEventListener('change', function() {
            var unitId = this.value;
            if (!unitId) {
                credDeptSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
                credDeptSelect.disabled = true;
                return;
            }
            credDeptSelect.disabled = true;
            credDeptSelect.innerHTML = '<option value="">Loading...</option>';
            fetch('/ajax/get-departments/?unit_id=' + unitId)
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    credDeptSelect.innerHTML = '<option value="">-- Select --</option>';
                    if (data.departments && data.departments.length > 0) {
                        data.departments.forEach(function(d) {
                            var opt = document.createElement('option');
                            opt.value = d.id;
                            opt.textContent = d.name;
                            credDeptSelect.appendChild(opt);
                        });
                        credDeptSelect.disabled = false;
                    } else {
                        credDeptSelect.innerHTML += '<option value="">No departments</option>';
                        credDeptSelect.disabled = true;
                    }
                })
                .catch(function() {
                    credDeptSelect.innerHTML = '<option value="">Error loading departments</option>';
                    credDeptSelect.disabled = true;
                });
        });
    }

    // ============================================================
    // PREFILL EDIT CREDENTIAL MODAL
    // ============================================================
    var editCredentialModal = document.getElementById('editCredentialModal');
    if (editCredentialModal) {
        editCredentialModal.addEventListener('show.bs.modal', function(e) {
            var btn = e.relatedTarget;
            document.getElementById('edit_cred_id').value = btn.getAttribute('data-id');
            document.getElementById('edit_cred_username').value = btn.getAttribute('data-username');
            document.getElementById('edit_cred_password').value = btn.getAttribute('data-password');
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
    // BULK UPLOAD - CREDENTIALS
    // ============================================================
    var selectedFile = null;
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    function getCsrfToken() {
        var name = 'csrftoken';
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return '';
    }

    csrfToken = getCsrfToken();

    window.handleBulkFileSelect = function(event) {
        var file = event.target.files[0];
        if (file) {
            selectedFile = file;
            var fileNameDisplay = document.getElementById('bulkFileName');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
            }
            var resultDiv = document.getElementById('bulkUploadResult');
            if (resultDiv) {
                resultDiv.innerHTML = '';
            }
        } else {
            selectedFile = null;
            var fileNameDisplay = document.getElementById('bulkFileName');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = 'No file selected';
            }
        }
    };

    // Drag and drop support
    var uploadArea = document.getElementById('bulkUploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--settings-primary)';
            this.style.background = 'rgba(255,107,0,0.05)';
        });
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
        });
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
            var files = e.dataTransfer.files;
            if (files.length > 0) {
                var file = files[0];
                if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv')) {
                    selectedFile = file;
                    var fileInput = document.getElementById('bulkFile');
                    if (fileInput) {
                        fileInput.files = files;
                    }
                    var fileNameDisplay = document.getElementById('bulkFileName');
                    if (fileNameDisplay) {
                        fileNameDisplay.textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
                    }
                    var resultDiv = document.getElementById('bulkUploadResult');
                    if (resultDiv) {
                        resultDiv.innerHTML = '';
                    }
                } else {
                    showAlert('Please upload an Excel or CSV file.', 'error');
                }
            }
        });
    }

    window.submitBulkUpload = function() {
        if (!selectedFile) {
            showAlert('Please select an Excel/CSV file to upload', 'error');
            return;
        }

        var formData = new FormData();
        formData.append('excel_file', selectedFile);
        formData.append('csrfmiddlewaretoken', csrfToken);

        var btn = document.getElementById('bulkUploadBtn');
        var progressBar = document.getElementById('bulkProgressBar');
        var progressFill = document.getElementById('bulkProgressFill');
        var resultDiv = document.getElementById('bulkUploadResult');

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Uploading...';
        if (progressBar) {
            progressBar.classList.add('active');
        }
        if (progressFill) {
            progressFill.style.width = '30%';
        }
        if (resultDiv) {
            resultDiv.innerHTML = '';
        }

        fetch("/custom-admin/settings/credentials/bulk-upload/", {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(function(response) {
            if (progressFill) {
                progressFill.style.width = '70%';
            }
            if (!response.ok) {
                return response.json().then(function(data) {
                    throw new Error(data.message || 'Server error: ' + response.status);
                }).catch(function() {
                    throw new Error('Network response was not ok: ' + response.status);
                });
            }
            return response.json();
        })
        .then(function(data) {
            if (progressFill) {
                progressFill.style.width = '100%';
            }
            setTimeout(function() {
                if (progressBar) {
                    progressBar.classList.remove('active');
                }
                if (progressFill) {
                    progressFill.style.width = '0%';
                }
            }, 1000);

            if (data.success) {
                var html = '<div style="font-weight:600; margin-bottom:0.5rem;">Upload Complete</div>';
                if (data.added_count > 0) {
                    html += '<div class="success-item">' + data.added_count + ' credentials added successfully</div>';
                    if (data.added_creds && data.added_creds.length > 0) {
                        html += '<div style="font-size:0.7rem; color:var(--text-muted); margin-top:0.2rem;">Added: ' + data.added_creds.join(', ') + '</div>';
                    }
                }
                if (data.skipped_count > 0) {
                    html += '<div class="warning-item">' + data.skipped_count + ' entries skipped</div>';
                    if (data.errors && data.errors.length > 0) {
                        html += '<div style="margin-top:0.5rem;"><strong>Errors:</strong></div>';
                        data.errors.forEach(function(err) {
                            html += '<div class="error-item">' + err + '</div>';
                        });
                    }
                }
                if (data.added_count === 0 && data.skipped_count === 0) {
                    html += '<div class="warning-item">No credentials were added or skipped. Please check your file.</div>';
                }
                if (resultDiv) {
                    resultDiv.innerHTML = html;
                }
                showAlert(data.message || 'Bulk upload completed successfully!', 'success');
                setTimeout(function() {
                    location.reload();
                }, 2000);
            } else {
                var html = '<div style="font-weight:600; color:var(--danger-color); margin-bottom:0.5rem;">Upload Failed</div>';
                if (data.errors && data.errors.length > 0) {
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">' + err + '</div>';
                    });
                } else {
                    html += '<div class="error-item">' + (data.message || 'Unknown error occurred') + '</div>';
                }
                if (resultDiv) {
                    resultDiv.innerHTML = html;
                }
                showAlert(data.message || 'Bulk upload failed', 'error');
            }

            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-upload me-1"></i> Upload';
        })
        .catch(function(error) {
            if (progressFill) {
                progressFill.style.width = '100%';
            }
            setTimeout(function() {
                if (progressBar) {
                    progressBar.classList.remove('active');
                }
                if (progressFill) {
                    progressFill.style.width = '0%';
                }
            }, 1000);
            if (resultDiv) {
                resultDiv.innerHTML = '<div class="error-item">Error: ' + error.message + '</div>';
            }
            showAlert('Error: ' + error.message, 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-upload me-1"></i> Upload';
        });
    };

    function showAlert(message, type) {
        var alertContainer = document.querySelector('.alert-container');
        if (!alertContainer) {
            var container = document.createElement('div');
            container.className = 'alert-container';
            container.style.cssText = 'position:fixed; top:20px; right:20px; z-index:9999; max-width:400px; width:100%;';
            document.body.appendChild(container);
            alertContainer = container;
        }

        var alertDiv = document.createElement('div');
        var bgColor = type === 'success' ? '#22C55E' : type === 'error' ? '#EF4444' : '#F59E0B';
        var textColor = type === 'warning' ? '#1A1A2E' : '#FFFFFF';
        alertDiv.style.cssText = 'padding:0.75rem 1rem; border-radius:12px; margin-bottom:0.5rem; box-shadow:0 4px 20px rgba(0,0,0,0.15); display:flex; align-items:center; gap:0.5rem; animation:slideIn 0.3s ease; font-size:0.85rem; background:' + bgColor + '; color:' + textColor + ';';

        var iconMap = {
            'success': 'fa-circle-check',
            'error': 'fa-circle-xmark',
            'warning': 'fa-triangle-exclamation'
        };
        var icon = iconMap[type] || 'fa-circle-info';

        alertDiv.innerHTML =
            '<i class="fa-solid ' + icon + '"></i>' +
            '<span style="white-space:pre-line;">' + message + '</span>' +
            '<button onclick="this.parentElement.remove()" style="background:transparent; border:none; color:inherit; cursor:pointer; font-size:1rem; margin-left:auto; opacity:0.7;">&times;</button>';

        alertContainer.appendChild(alertDiv);

        setTimeout(function() {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
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
});