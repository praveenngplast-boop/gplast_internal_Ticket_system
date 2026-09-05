document.addEventListener('DOMContentLoaded', function() {

    const CSRF = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // ✅ FIXED: Use correct URLs with custom-admin prefix
    const ADD_URL = '/custom-admin/settings/screen-master/add/';
    const EDIT_URL = '/custom-admin/settings/screen-master/edit/';
    const DELETE_URL = '/custom-admin/settings/screen-master/delete/';
    const BULK_UPLOAD_URL = '/custom-admin/settings/screen-master/bulk-upload/';

    // ============================================================
    // TOAST NOTIFICATION
    // ============================================================
    function showToast(msg, type) {
        type = type || 'success';
        const tc = document.getElementById('toastContainer');
        if (!tc) return;
        const t = document.createElement('div');
        t.className = 'toast ' + type;
        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle';
        t.innerHTML = '<i class="fas fa-' + icon + ' me-2"></i>' + msg;
        tc.appendChild(t);
        setTimeout(function() {
            t.style.opacity = '0';
            t.style.transform = 'translateX(30px)';
            setTimeout(function() { if (t.parentNode) t.remove(); }, 400);
        }, 4000);
    }

    window.showToast = showToast;

    // ============================================================
    // ADD MODAL
    // ============================================================
    window.openAddModal = function() {
        document.getElementById('addCode').value = '';
        document.getElementById('addName').value = '';
        document.getElementById('addModal').classList.add('active');
        setTimeout(function() { document.getElementById('addCode').focus(); }, 200);
    };

    window.closeAddModal = function() {
        document.getElementById('addModal').classList.remove('active');
    };

    window.submitAdd = function() {
        const code = document.getElementById('addCode').value.trim();
        const name = document.getElementById('addName').value.trim();
        const type = document.getElementById('addType').value;
        if (!code || !name) {
            showToast('Both Screen Code and Name are required', 'error');
            return;
        }

        var formData = new FormData();
        formData.append('screen_code', code);
        formData.append('screen_name', name);
        formData.append('screen_type', type);

        fetch(ADD_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(function(r) {
            if (!r.ok) throw new Error('Network response was not ok: ' + r.status);
            return r.json();
        })
        .then(function(d) {
            if (d.success) {
                showToast(d.message);
                closeAddModal();
                setTimeout(function() { location.reload(); }, 1000);
            } else {
                showToast(d.message, 'error');
            }
        })
        .catch(function(e) { showToast('Error: ' + e.message, 'error'); });
    };

    // ============================================================
    // EDIT MODAL
    // ============================================================
    window.openEditModal = function(id, code, name, type) {
        document.getElementById('editId').value = id;
        document.getElementById('editCode').value = code;
        document.getElementById('editName').value = name;
        document.getElementById('editType').value = type;
        document.getElementById('editModal').classList.add('active');
        setTimeout(function() { document.getElementById('editCode').focus(); }, 200);
    };

    window.closeEditModal = function() {
        document.getElementById('editModal').classList.remove('active');
    };

    window.submitEdit = function() {
        const id = document.getElementById('editId').value;
        const code = document.getElementById('editCode').value.trim();
        const name = document.getElementById('editName').value.trim();
        const type = document.getElementById('editType').value;
        if (!code || !name) {
            showToast('Both Screen Code and Name are required', 'error');
            return;
        }

        var formData = new FormData();
        formData.append('screen_id', id);
        formData.append('screen_code', code);
        formData.append('screen_name', name);
        formData.append('screen_type', type);

        fetch(EDIT_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(function(r) {
            if (!r.ok) throw new Error('Network response was not ok: ' + r.status);
            return r.json();
        })
        .then(function(d) {
            if (d.success) {
                showToast(d.message);
                closeEditModal();
                setTimeout(function() { location.reload(); }, 1000);
            } else {
                showToast(d.message, 'error');
            }
        })
        .catch(function(e) { showToast('Error: ' + e.message, 'error'); });
    };

    // ============================================================
    // DELETE MODAL
    // ============================================================
    window.confirmDelete = function(id, name) {
        document.getElementById('deleteId').value = id;
        document.getElementById('deleteName').textContent = name;
        document.getElementById('deleteModal').classList.add('active');
    };

    window.closeDeleteModal = function() {
        document.getElementById('deleteModal').classList.remove('active');
    };

    window.submitDelete = function() {
        const id = document.getElementById('deleteId').value;

        var formData = new FormData();
        formData.append('screen_id', id);

        fetch(DELETE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(function(r) {
            if (!r.ok) throw new Error('Network response was not ok: ' + r.status);
            return r.json();
        })
        .then(function(d) {
            if (d.success) {
                showToast(d.message);
                closeDeleteModal();
                var row = document.getElementById('row-' + id);
                if (row) row.remove();
            } else {
                showToast(d.message, 'error');
            }
        })
        .catch(function(e) { showToast('Error: ' + e.message, 'error'); });
    };

    // ============================================================
    // BULK UPLOAD
    // ============================================================
    var selectedFile = null;

    window.openBulkModal = function() {
        document.getElementById('bulkModal').classList.add('active');
        document.getElementById('fileName').textContent = 'No file selected';
        document.getElementById('uploadResult').innerHTML = '';
        document.getElementById('progressBar').classList.remove('active');
        document.getElementById('progressFill').style.width = '0%';
        selectedFile = null;
        document.getElementById('bulkFile').value = '';
    };

    window.closeBulkModal = function() {
        document.getElementById('bulkModal').classList.remove('active');
    };

    window.handleFileSelect = function(event) {
        const file = event.target.files[0];
        if (file) {
            selectedFile = file;
            document.getElementById('fileName').textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
            document.getElementById('uploadResult').innerHTML = '';
        } else {
            selectedFile = null;
            document.getElementById('fileName').textContent = 'No file selected';
        }
    };

    // Drag and drop support
    var uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--sm-orange)';
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
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                    selectedFile = file;
                    document.getElementById('bulkFile').files = files;
                    document.getElementById('fileName').textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
                    document.getElementById('uploadResult').innerHTML = '';
                } else {
                    showToast('Please upload an Excel file (.xlsx or .xls)', 'error');
                }
            }
        });
    }

    window.submitBulkUpload = function() {
        if (!selectedFile) {
            showToast('Please select an Excel file to upload', 'error');
            return;
        }

        var formData = new FormData();
        formData.append('excel_file', selectedFile);
        formData.append('csrfmiddlewaretoken', CSRF);

        var btn = document.getElementById('bulkUploadBtn');
        var progressBar = document.getElementById('progressBar');
        var progressFill = document.getElementById('progressFill');
        var resultDiv = document.getElementById('uploadResult');

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
                    html += '<div class="success-item">' + data.added_count + ' screens added successfully</div>';
                }
                if (data.skipped_count > 0) {
                    html += '<div class="error-item">' + data.skipped_count + ' rows skipped</div>';
                }
                if (data.errors && data.errors.length > 0) {
                    html += '<div style="margin-top:0.5rem;"><strong>Errors:</strong></div>';
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">' + err + '</div>';
                    });
                }
                resultDiv.innerHTML = html;
                showToast(data.message || 'Bulk upload completed successfully!', 'success');
                setTimeout(function() {
                    location.reload();
                }, 2000);
            } else {
                var html = '<div style="font-weight:600; color:var(--sm-danger); margin-bottom:0.5rem;">Upload Failed</div>';
                if (data.errors && data.errors.length > 0) {
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">' + err + '</div>';
                    });
                } else {
                    html += '<div class="error-item">' + (data.message || 'Unknown error occurred') + '</div>';
                }
                resultDiv.innerHTML = html;
                showToast(data.message || 'Bulk upload failed', 'error');
            }

            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload';
        })
        .catch(function(error) {
            progressFill.style.width = '100%';
            setTimeout(function() {
                progressBar.classList.remove('active');
                progressFill.style.width = '0%';
            }, 1000);
            resultDiv.innerHTML = '<div class="error-item">Error: ' + error.message + '</div>';
            showToast('Error: ' + error.message, 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload';
        });
    };

    // ============================================================
    // SEARCH / FILTER
    // ============================================================
    window.filterTable = function() {
        const q = document.getElementById('screenSearch').value.toLowerCase();
        document.querySelectorAll('#screenTable tbody tr').forEach(function(row) {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    };

    // ============================================================
    // CLOSE MODALS ON OVERLAY CLICK
    // ============================================================
    ['addModal','editModal','deleteModal','bulkModal'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) {
            el.addEventListener('click', function(e) {
                if (e.target === this) this.classList.remove('active');
            });
        }
    });

    // ============================================================
    // KEYBOARD SUPPORT
    // ============================================================
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            if (document.getElementById('addModal').classList.contains('active')) {
                window.submitAdd();
            } else if (document.getElementById('editModal').classList.contains('active')) {
                window.submitEdit();
            }
        }
        if (e.key === 'Escape') {
            ['addModal','editModal','deleteModal','bulkModal'].forEach(function(id) {
                var el = document.getElementById(id);
                if (el) el.classList.remove('active');
            });
        }
    });

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, input, select');
        inputs.forEach(function(el) {
            if (isDark) {
                el.style.backgroundColor = 'rgba(255,255,255,0.04)';
                el.style.borderColor = 'rgba(255,255,255,0.08)';
                el.style.color = '#E8EDF5';
                el.style.webkitTextFillColor = '#E8EDF5';
            } else {
                el.style.backgroundColor = '';
                el.style.borderColor = '';
                el.style.color = '';
                el.style.webkitTextFillColor = '';
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

    // ============================================================
    // SPINNER STYLES (for upload button)
    // ============================================================
    var style = document.createElement('style');
    style.textContent = `
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.6s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    console.log('Screen Master JS loaded with fixed URLs');
    console.log('Add URL:', ADD_URL);
    console.log('Edit URL:', EDIT_URL);
    console.log('Delete URL:', DELETE_URL);
    console.log('Bulk Upload URL:', BULK_UPLOAD_URL);
});