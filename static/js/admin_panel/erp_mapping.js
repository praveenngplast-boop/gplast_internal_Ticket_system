document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // CSRF TOKEN - Get from cookie
    // ============================================================
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

    var csrfToken = getCsrfToken();
    var alertContainer = document.getElementById('alertContainer');
    var addMappingUrl = alertContainer.dataset.addUrl;
    var removeMappingUrl = alertContainer.dataset.removeUrl;
    var unmapMappingUrl = alertContainer.dataset.unmapUrl;

    // ============================================================
    // MANUAL ADD
    // ============================================================
    var addBtn = document.getElementById('addMappingBtn');
    var erpUserIdInput = document.getElementById('erpUserId');
    var employeeSelect = document.getElementById('employeeSelect');

    addBtn.addEventListener('click', function() {
        var erpUserId = erpUserIdInput.value.trim();
        var employeeId = employeeSelect.value;

        if (!erpUserId) {
            showAlert('Please enter an ERP User ID.', 'error');
            erpUserIdInput.focus();
            return;
        }

        this.disabled = true;
        this.innerHTML = '<span class="spinner"></span> Adding...';
        this.style.opacity = '0.6';

        var formData = new FormData();
        formData.append('erp_user_id', erpUserId);
        if (employeeId) {
            formData.append('employee_id', employeeId);
            formData.append('action', 'map');
        } else {
            formData.append('action', 'add');
        }
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(addMappingUrl, {
            method: 'POST',
            body: formData,
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
            if (data.success) {
                showAlert(data.message, 'success');
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to add.', 'error');
                addBtn.disabled = false;
                addBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Add ERP ID';
                addBtn.style.opacity = '1';
            }
        })
        .catch(function(error) {
            console.error('Add error:', error);
            showAlert('Error: ' + error.message, 'error');
            addBtn.disabled = false;
            addBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Add ERP ID';
            addBtn.style.opacity = '1';
        });
    });

    erpUserIdInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { addBtn.click(); }
    });
    employeeSelect.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { addBtn.click(); }
    });

    // ============================================================
    // REMOVE SINGLE MAPPING (AJAX)
    // ============================================================
    window.removeMapping = function(mappingId) {
        if (!confirm('Are you sure you want to permanently delete this ERP ID mapping?')) {
            return;
        }

        var row = document.querySelector('tr[data-id="' + mappingId + '"]');
        var formData = new FormData();
        formData.append('mapping_id', mappingId);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(removeMappingUrl, {
            method: 'POST',
            body: formData,
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
            if (data.success) {
                showAlert(data.message, 'success');
                if (row) { row.remove(); }
                updateCount();
            } else {
                showAlert(data.message || 'Failed to remove.', 'error');
            }
        })
        .catch(function(error) {
            console.error('Remove error:', error);
            showAlert('Error: ' + error.message, 'error');
        });
    };

    // ============================================================
    // UNMAP SINGLE EMPLOYEE FROM ERP ID (AJAX)
    // ============================================================
    window.unmapMapping = function(mappingId, erpUserId) {
        if (!confirm('Remove employee mapping from ERP ID "' + erpUserId + '"?')) {
            return;
        }

        var row = document.querySelector('tr[data-id="' + mappingId + '"]');
        var formData = new FormData();
        formData.append('mapping_id', mappingId);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(unmapMappingUrl, {
            method: 'POST',
            body: formData,
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
            if (data.success) {
                showAlert(data.message, 'success');
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to unmap.', 'error');
            }
        })
        .catch(function(error) {
            console.error('Unmap error:', error);
            showAlert('Error: ' + error.message, 'error');
        });
    };

    // ============================================================
    // UNMAP ALL EMPLOYEES FROM ERP ID (AJAX)
    // ============================================================
    window.unmapAllMappings = function(erpUserId) {
        if (!confirm('Are you sure you want to unmap ALL employees from ERP ID "' + erpUserId + '"? This will keep the ERP ID entries but remove all employee mappings.')) {
            return;
        }

        var formData = new FormData();
        formData.append('erp_user_id', erpUserId);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch('/custom-admin/settings/erp-mapping/unmap-all/', {
            method: 'POST',
            body: formData,
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
            if (data.success) {
                showAlert(data.message, 'success');
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to unmap all.', 'error');
            }
        })
        .catch(function(error) {
            console.error('Unmap all error:', error);
            showAlert('Error: ' + error.message, 'error');
        });
    };

    // ============================================================
    // DELETE ALL MAPPINGS FOR ERP ID (AJAX)
    // ============================================================
    window.removeAllMappings = function(erpUserId) {
        if (!confirm('⚠️ Are you sure you want to permanently delete ALL mappings for ERP ID "' + erpUserId + '"? This action cannot be undone!')) {
            return;
        }

        var formData = new FormData();
        formData.append('erp_user_id', erpUserId);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch('/custom-admin/settings/erp-mapping/delete-all/', {
            method: 'POST',
            body: formData,
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
            if (data.success) {
                showAlert(data.message, 'success');
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to delete mappings.', 'error');
            }
        })
        .catch(function(error) {
            console.error('Delete all error:', error);
            showAlert('Error: ' + error.message, 'error');
        });
    };

    // ============================================================
    // OPEN MAP MODAL
    // ============================================================
    window.openMapModal = function(erpUserId) {
        document.getElementById('mapErpUserId').value = erpUserId;
        document.getElementById('mapErpUserIdDisplay').value = erpUserId;
        document.getElementById('mapEmployeeSelect').value = '';
        var modal = new bootstrap.Modal(document.getElementById('mapModal'));
        modal.show();
    };

    // ============================================================
    // MAP ERP ID TO EMPLOYEE
    // ============================================================
    document.getElementById('mapSubmitBtn').addEventListener('click', function() {
        var erpUserId = document.getElementById('mapErpUserId').value;
        var employeeId = document.getElementById('mapEmployeeSelect').value;

        if (!employeeId) {
            showAlert('Please select an employee.', 'error');
            return;
        }

        this.disabled = true;
        this.innerHTML = '<span class="spinner"></span> Mapping...';

        var formData = new FormData();
        formData.append('erp_user_id', erpUserId);
        formData.append('employee_id', employeeId);
        formData.append('action', 'map');
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(addMappingUrl, {
            method: 'POST',
            body: formData,
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
            if (data.success) {
                showAlert(data.message, 'success');
                var modal = bootstrap.Modal.getInstance(document.getElementById('mapModal'));
                if (modal) modal.hide();
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to map.', 'error');
                this.disabled = false;
                this.innerHTML = '<i class="fa-solid fa-link me-1"></i> Map';
            }
        }.bind(this))
        .catch(function(error) {
            console.error('Map error:', error);
            showAlert('Error: ' + error.message, 'error');
            this.disabled = false;
            this.innerHTML = '<i class="fa-solid fa-link me-1"></i> Map';
        }.bind(this));
    });

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================
    function updateCount() {
        var rows = document.querySelectorAll('#mappingsBody tr:not(:has(.empty-state))');
        var count = rows.length;
        var badge = document.querySelector('.count-badge');
        if (badge) {
            badge.innerHTML = '<i class="fa-regular fa-circle-check"></i> ' + count + ' ERP IDs';
        }
        rows.forEach(function(row, index) {
            var td = row.querySelector('td:first-child');
            if (td) { td.textContent = index + 1; }
        });
    }

    function showAlert(message, type) {
        var container = alertContainer;
        var alertDiv = document.createElement('div');
        alertDiv.className = 'alert-item alert-' + type;

        var iconMap = {
            'success': 'fa-circle-check',
            'error': 'fa-circle-xmark',
            'warning': 'fa-triangle-exclamation',
            'info': 'fa-circle-info'
        };
        var icon = iconMap[type] || 'fa-circle-info';

        alertDiv.innerHTML =
            '<i class="fa-solid ' + icon + '"></i>' +
            '<span style="white-space: pre-line;">' + message + '</span>' +
            '<button class="alert-close" onclick="this.parentElement.remove()">&times;</button>';

        container.appendChild(alertDiv);

        setTimeout(function() {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // ============================================================
    // BULK UPLOAD
    // ============================================================
    var selectedFile = null;
    var BULK_UPLOAD_URL = '/custom-admin/settings/erp-mapping/bulk-upload/';

    window.openBulkUploadModal = function() {
        var modal = new bootstrap.Modal(document.getElementById('bulkUploadModal'));
        modal.show();
        document.getElementById('bulkFileName').textContent = 'No file selected';
        document.getElementById('bulkUploadResult').innerHTML = '';
        document.getElementById('bulkProgressBar').classList.remove('active');
        document.getElementById('bulkProgressFill').style.width = '0%';
        selectedFile = null;
        document.getElementById('bulkFile').value = '';
    };

    window.handleBulkFileSelect = function(event) {
        var file = event.target.files[0];
        if (file) {
            selectedFile = file;
            document.getElementById('bulkFileName').textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
            document.getElementById('bulkUploadResult').innerHTML = '';
        } else {
            selectedFile = null;
            document.getElementById('bulkFileName').textContent = 'No file selected';
        }
    };

    // Drag and drop support
    var uploadArea = document.getElementById('bulkUploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--erp-primary)';
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
                    document.getElementById('bulkFile').files = files;
                    document.getElementById('bulkFileName').textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
                    document.getElementById('bulkUploadResult').innerHTML = '';
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
        progressBar.classList.add('active');
        progressFill.style.width = '30%';
        resultDiv.innerHTML = '';

        fetch(BULK_UPLOAD_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(function(response) {
            progressFill.style.width = '70%';
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            progressFill.style.width = '100%';
            setTimeout(function() {
                progressBar.classList.remove('active');
                progressFill.style.width = '0%';
            }, 1000);

            if (data.success) {
                var html = '<div style="font-weight:600; margin-bottom:0.5rem;">Upload Complete</div>';
                if (data.added_count > 0) {
                    html += '<div class="success-item">' + data.added_count + ' ERP IDs added successfully</div>';
                }
                if (data.skipped_count > 0) {
                    html += '<div class="error-item">' + data.skipped_count + ' entries skipped</div>';
                }
                if (data.errors && data.errors.length > 0) {
                    html += '<div style="margin-top:0.5rem;"><strong>Errors:</strong></div>';
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">' + err + '</div>';
                    });
                }
                resultDiv.innerHTML = html;
                showAlert(data.message || 'Bulk upload completed successfully!', 'success');
                setTimeout(function() {
                    location.reload();
                }, 2000);
            } else {
                var html = '<div style="font-weight:600; color:var(--erp-danger); margin-bottom:0.5rem;">Upload Failed</div>';
                if (data.errors && data.errors.length > 0) {
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">' + err + '</div>';
                    });
                } else {
                    html += '<div class="error-item">' + (data.message || 'Unknown error occurred') + '</div>';
                }
                resultDiv.innerHTML = html;
                showAlert(data.message || 'Bulk upload failed', 'error');
            }

            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-upload me-1"></i> Upload';
        })
        .catch(function(error) {
            progressFill.style.width = '100%';
            setTimeout(function() {
                progressBar.classList.remove('active');
                progressFill.style.width = '0%';
            }, 1000);
            resultDiv.innerHTML = '<div class="error-item">Error: ' + error.message + '</div>';
            showAlert('Error: ' + error.message, 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-upload me-1"></i> Upload';
        });
    };

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, .modal-body .form-control');
        var selects = document.querySelectorAll('select.form-control, .modal-body select.form-control');
        
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

        selects.forEach(function(select) {
            if (isDark) {
                select.style.backgroundColor = 'rgba(255,255,255,0.05)';
                select.style.borderColor = 'rgba(255,255,255,0.08)';
                select.style.color = '#E8EDF5';
                select.style.webkitTextFillColor = '#E8EDF5';
                var options = select.querySelectorAll('option');
                options.forEach(function(option) {
                    option.style.backgroundColor = '#1A1A2E';
                    option.style.color = '#E8EDF5';
                });
            } else {
                select.style.backgroundColor = '';
                select.style.borderColor = '';
                select.style.color = '';
                select.style.webkitTextFillColor = '';
                var options = select.querySelectorAll('option');
                options.forEach(function(option) {
                    option.style.backgroundColor = '';
                    option.style.color = '';
                });
            }
        });

        var modalSelects = document.querySelectorAll('#mapModal .form-control, #bulkUploadModal .form-control');
        modalSelects.forEach(function(select) {
            if (isDark) {
                select.style.backgroundColor = 'rgba(255,255,255,0.05)';
                select.style.borderColor = 'rgba(255,255,255,0.08)';
                select.style.color = '#E8EDF5';
                select.style.webkitTextFillColor = '#E8EDF5';
                var options = select.querySelectorAll('option');
                options.forEach(function(option) {
                    option.style.backgroundColor = '#1A1A2E';
                    option.style.color = '#E8EDF5';
                });
            } else {
                select.style.backgroundColor = '';
                select.style.borderColor = '';
                select.style.color = '';
                select.style.webkitTextFillColor = '';
                var options = select.querySelectorAll('option');
                options.forEach(function(option) {
                    option.style.backgroundColor = '';
                    option.style.color = '';
                });
            }
        });
    }

    var themeToggle = document.getElementById('themeToggleFloating');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            setTimeout(updateThemeStyles, 100);
        });
    }

    var observer = new MutationObserver(function() {
        updateThemeStyles();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateThemeStyles, 200);

    var mapModal = document.getElementById('mapModal');
    if (mapModal) {
        mapModal.addEventListener('shown.bs.modal', function() {
            setTimeout(updateThemeStyles, 50);
        });
    }

    console.log('ERP Mapping JS loaded with grouped view support');
    console.log('Bulk Upload URL:', BULK_UPLOAD_URL);
});