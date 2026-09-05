// ============================================================
// SCREEN MAPPING - MAIN JAVASCRIPT
// ============================================================

// Make sure everything is defined globally
(function() {
    'use strict';

    // ============================================================
    // URLS - FIXED WITH custom-admin PREFIX
    // ============================================================
    const ADD_URL = '/custom-admin/settings/screen-mapping/add/';
    const REMOVE_URL = '/custom-admin/settings/screen-mapping/remove/';
    const DELETE_ERP_URL = '/custom-admin/settings/screen-mapping/delete-erp/';
    const BULK_UPLOAD_URL = '/custom-admin/settings/screen-mapping/bulk-upload/';
    const GET_SCREENS_FOR_ERP_URL = '/ajax/get-screens-for-erp/';

    // ============================================================
    // CSRF TOKEN - Get from cookie
    // ============================================================
    function getCsrfToken() {
        var name = 'csrftoken';
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue || '';
    }

    // ============================================================
    // TOAST NOTIFICATION - FIXED
    // ============================================================
    function showToast(msg, type) {
        type = type || 'success';
        var tc = document.getElementById('toastContainer');
        
        // Create toast container if it doesn't exist
        if (!tc) {
            var newContainer = document.createElement('div');
            newContainer.id = 'toastContainer';
            newContainer.className = 'toast-container';
            document.body.appendChild(newContainer);
            var container = newContainer;
        } else {
            var container = tc;
        }
        
        var t = document.createElement('div');
        t.className = 'toast ' + type;
        var icon = type === 'success' ? 'check-circle' : 
                   type === 'error' ? 'times-circle' : 
                   type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        t.innerHTML = '<i class="fas fa-' + icon + ' me-2"></i>' + msg;
        container.appendChild(t);
        
        // Auto remove after 4 seconds
        setTimeout(function() {
            t.style.opacity = '0';
            t.style.transform = 'translateX(30px)';
            t.style.transition = 'all 0.4s ease';
            setTimeout(function() { 
                if (t.parentNode) t.remove(); 
            }, 400);
        }, 4000);
    }

    // ============================================================
    // VIEW SCREENS MODAL
    // ============================================================
    function viewScreens(erpId) {
        if (!erpId) {
            showToast('Invalid ERP User ID', 'error');
            return;
        }

        var viewModal = document.getElementById('viewModal');
        var viewModalBody = document.getElementById('viewModalBody');
        var viewModalTitle = document.getElementById('viewModalTitle');
        var viewModalErpId = document.getElementById('viewModalErpId');

        viewModalTitle.innerHTML = '<i class="fas fa-id-badge" style="color:var(--smap-orange);"></i> Screens for ERP ID: ' + erpId;
        viewModalErpId.value = erpId;
        viewModalBody.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--smap-text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:2rem;"></i><p>Loading screens...</p></div>';
        viewModal.classList.add('active');

        fetch(GET_SCREENS_FOR_ERP_URL + '?erp_user_id=' + encodeURIComponent(erpId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(function(r) {
            if (!r.ok) throw new Error('Network response was not ok: ' + r.status);
            return r.json();
        })
        .then(function(data) {
            if (data.success) {
                var html = '';
                var screens = data.screens || [];

                if (screens.length === 0) {
                    html = '<div class="empty-state" style="padding:2rem;"><i class="fas fa-desktop"></i><p style="font-size:0.85rem; color:var(--smap-text-secondary);">No screens mapped for this ERP ID.</p></div>';
                } else {
                    html = '<ul style="list-style:none; padding:0; margin:0;">';
                    screens.forEach(function(screen) {
                        html += '<li style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0.6rem; border-bottom:1px solid var(--smap-border);">';
                        html += '<span><strong>' + screen.screen_code + '</strong> - ' + screen.screen_name + ' <span style="font-size:0.6rem; color:var(--smap-text-muted);">(' + screen.screen_type + ')</span></span>';
                        html += '<button class="btn-sm btn-sm-delete" onclick="openRemoveModal(' + screen.mapping_id + ', \'' + screen.screen_code + ' - ' + screen.screen_name + '\', \'' + erpId + '\')" style="font-size:0.55rem; padding:0.05rem 0.4rem; min-height:20px;">';
                        html += '<i class="fas fa-unlink"></i> Remove</button>';
                        html += '</li>';
                    });
                    html += '</ul>';
                }
                viewModalBody.innerHTML = html;
            } else {
                viewModalBody.innerHTML = '<div class="empty-state" style="padding:2rem;"><i class="fas fa-circle-exclamation" style="color:#ef4444; opacity:0.4;"></i><p style="font-size:0.85rem; color:var(--smap-text-secondary);">' + (data.message || 'Error loading screens') + '</p></div>';
            }
        })
        .catch(function(error) {
            console.error('Error loading screens:', error);
            viewModalBody.innerHTML = '<div class="empty-state" style="padding:2rem;"><i class="fas fa-circle-exclamation" style="color:#ef4444; opacity:0.4;"></i><p style="font-size:0.85rem; color:var(--smap-text-secondary);">Network error. Please try again.</p></div>';
            showToast('Error loading screens: ' + error.message, 'error');
        });
    }

    function closeViewModal() {
        var viewModal = document.getElementById('viewModal');
        if (viewModal) viewModal.classList.remove('active');
    }

    function addScreenFromModal() {
        var viewModalErpId = document.getElementById('viewModalErpId');
        var erpId = viewModalErpId ? viewModalErpId.value : '';
        if (erpId) {
            closeViewModal();
            setTimeout(function() {
                openAddModal(erpId);
            }, 300);
        }
    }

    // ============================================================
    // ADD MODAL - COMPLETELY FIXED
    // ============================================================
    function openAddModal(prefillErp) {
        console.log('openAddModal called with:', prefillErp);
        
        var addModal = document.getElementById('addModal');
        var addErpId = document.getElementById('addErpId');
        var addScreen = document.getElementById('addScreen');
        
        if (!addModal) {
            console.error('Add modal not found!');
            showToast('Error: Modal not found', 'error');
            return;
        }
        
        // Reset the form
        if (addScreen) {
            addScreen.value = '';
        }
        
        // Pre-fill ERP if provided
        if (prefillErp && addErpId) {
            var found = false;
            for (var i = 0; i < addErpId.options.length; i++) {
                if (addErpId.options[i].value === prefillErp) {
                    addErpId.options[i].selected = true;
                    found = true;
                    break;
                }
            }
            if (!found) {
                console.warn('ERP ID not found in dropdown:', prefillErp);
                // Try to add it as a new option
                var newOption = document.createElement('option');
                newOption.value = prefillErp;
                newOption.textContent = prefillErp;
                newOption.selected = true;
                addErpId.appendChild(newOption);
            }
        } else if (addErpId) {
            // Reset to first option (-- Select ERP User ID --)
            addErpId.selectedIndex = 0;
        }
        
        // Show the modal - using CSS classes
        addModal.style.display = 'flex';
        addModal.classList.add('active');
        console.log('Modal opened, classes:', addModal.className);
        
        // Focus on the ERP select after a small delay
        setTimeout(function() {
            if (addErpId) {
                addErpId.focus();
            }
        }, 200);
    }

    function closeAddModal() {
        var addModal = document.getElementById('addModal');
        if (addModal) {
            addModal.style.display = 'none';
            addModal.classList.remove('active');
        }
    }

    function submitAdd() {
        console.log('submitAdd called');
        
        var addErpId = document.getElementById('addErpId');
        var addScreen = document.getElementById('addScreen');
        
        var erpId = addErpId ? addErpId.value.trim() : '';
        var screenId = addScreen ? addScreen.value : '';

        if (!erpId) {
            showToast('Please select an ERP User ID', 'error');
            if (addErpId) addErpId.focus();
            return;
        }
        if (!screenId) {
            showToast('Please select a screen', 'error');
            if (addScreen) addScreen.focus();
            return;
        }

        // Get CSRF token
        var csrfToken = getCsrfToken();
        
        if (!csrfToken) {
            showToast('Security error: CSRF token missing. Please refresh the page.', 'error');
            return;
        }
        
        var formData = new FormData();
        formData.append('erp_user_id', erpId);
        formData.append('screen_id', screenId);

        console.log('Submitting mapping:', { erpId: erpId, screenId: screenId });

        // Disable submit button
        var submitBtn = document.querySelector('#addModal .btn-orange');
        var originalText = '';
        if (submitBtn) {
            originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        }

        fetch(ADD_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(function(response) {
            if (!response.ok) {
                return response.text().then(function(text) {
                    console.error('Server error response:', text);
                    throw new Error('Server returned ' + response.status + ': ' + text.substring(0, 200));
                });
            }
            return response.json();
        })
        .then(function(data) {
            console.log('Add response:', data);
            if (data.success) {
                showToast(data.message || '✅ Mapping added successfully!', 'success');
                closeAddModal();
                // Reload after a short delay to show the new mapping
                setTimeout(function() { 
                    location.reload(); 
                }, 1200);
            } else {
                showToast('❌ ' + (data.message || 'Failed to add mapping'), 'error');
                // Re-enable submit button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText || '<i class="fas fa-save"></i> Add Mapping';
                }
            }
        })
        .catch(function(error) {
            console.error('Add error:', error);
            showToast('Error: ' + error.message, 'error');
            // Re-enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText || '<i class="fas fa-save"></i> Add Mapping';
            }
        });
    }

    // ============================================================
    // REMOVE MODAL
    // ============================================================
    function openRemoveModal(mappingId, screenName, erpId) {
        var removeModal = document.getElementById('removeModal');
        var removeId = document.getElementById('removeId');
        var removeScreen = document.getElementById('removeScreen');
        var removeErp = document.getElementById('removeErp');
        
        if (removeId) removeId.value = mappingId;
        if (removeScreen) removeScreen.textContent = screenName;
        if (removeErp) removeErp.textContent = erpId;
        if (removeModal) {
            removeModal.style.display = 'flex';
            removeModal.classList.add('active');
        }
    }

    function closeRemoveModal() {
        var removeModal = document.getElementById('removeModal');
        if (removeModal) {
            removeModal.style.display = 'none';
            removeModal.classList.remove('active');
        }
    }

    function submitRemove() {
        var removeId = document.getElementById('removeId');
        var mappingId = removeId ? removeId.value : '';
        var csrfToken = getCsrfToken();

        var formData = new FormData();
        formData.append('mapping_id', mappingId);

        // Disable remove button
        var removeBtn = document.querySelector('#removeModal button[onclick="submitRemove()"]');
        if (removeBtn) {
            removeBtn.disabled = true;
            removeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Removing...';
        }

        fetch(REMOVE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
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
                showToast(d.message || '✅ Screen removed successfully!', 'success');
                closeRemoveModal();
                setTimeout(function() { location.reload(); }, 1000);
            } else {
                showToast('❌ ' + (d.message || 'Failed to remove screen'), 'error');
                if (removeBtn) {
                    removeBtn.disabled = false;
                    removeBtn.innerHTML = '<i class="fas fa-unlink"></i> Remove';
                }
            }
        })
        .catch(function(e) { 
            showToast('Error: ' + e.message, 'error');
            if (removeBtn) {
                removeBtn.disabled = false;
                removeBtn.innerHTML = '<i class="fas fa-unlink"></i> Remove';
            }
        });
    }

    // ============================================================
    // DELETE ALL SCREENS FOR ERP
    // ============================================================
    function confirmDeleteErp(erpId, screenCount) {
        if (confirm('Are you sure you want to delete all ' + screenCount + ' screen mapping(s) for ERP ID "' + erpId + '"? This action cannot be undone.')) {
            var csrfToken = getCsrfToken();
            var formData = new FormData();
            formData.append('erp_user_id', erpId);

            fetch(DELETE_ERP_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
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
                    showToast(d.message || 'All mappings deleted successfully!', 'success');
                    setTimeout(function() { location.reload(); }, 1000);
                } else {
                    showToast(d.message || 'Failed to delete mappings', 'error');
                }
            })
            .catch(function(e) { 
                showToast('Error: ' + e.message, 'error'); 
            });
        }
    }

    // ============================================================
    // BULK UPLOAD
    // ============================================================
    var selectedFile = null;

    function openBulkUploadModal() {
        var bulkModal = document.getElementById('bulkUploadModal');
        if (bulkModal) {
            bulkModal.style.display = 'flex';
            bulkModal.classList.add('active');
        }
        
        var fileName = document.getElementById('bulkFileName');
        if (fileName) fileName.textContent = 'No file selected';
        
        var resultDiv = document.getElementById('bulkUploadResult');
        if (resultDiv) resultDiv.innerHTML = '';
        
        var progressBar = document.getElementById('bulkProgressBar');
        if (progressBar) progressBar.classList.remove('active');
        
        var progressFill = document.getElementById('bulkProgressFill');
        if (progressFill) progressFill.style.width = '0%';
        
        selectedFile = null;
        var fileInput = document.getElementById('bulkFile');
        if (fileInput) fileInput.value = '';
    }

    function closeBulkUploadModal() {
        var bulkModal = document.getElementById('bulkUploadModal');
        if (bulkModal) {
            bulkModal.style.display = 'none';
            bulkModal.classList.remove('active');
        }
    }

    function handleBulkFileSelect(event) {
        var file = event.target.files[0];
        var fileName = document.getElementById('bulkFileName');
        if (file) {
            selectedFile = file;
            if (fileName) fileName.textContent = file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
            var resultDiv = document.getElementById('bulkUploadResult');
            if (resultDiv) resultDiv.innerHTML = '';
        } else {
            selectedFile = null;
            if (fileName) fileName.textContent = 'No file selected';
        }
    }

    function submitBulkUpload() {
        if (!selectedFile) {
            showToast('Please select an Excel/CSV file to upload', 'error');
            return;
        }

        var csrfToken = getCsrfToken();
        var formData = new FormData();
        formData.append('excel_file', selectedFile);
        formData.append('csrfmiddlewaretoken', csrfToken);

        var btn = document.getElementById('bulkUploadBtn');
        var progressBar = document.getElementById('bulkProgressBar');
        var progressFill = document.getElementById('bulkProgressFill');
        var resultDiv = document.getElementById('bulkUploadResult');

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Uploading...';
        }
        if (progressBar) progressBar.classList.add('active');
        if (progressFill) progressFill.style.width = '30%';
        if (resultDiv) resultDiv.innerHTML = '';

        fetch(BULK_UPLOAD_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(function(response) {
            if (progressFill) progressFill.style.width = '70%';
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            if (progressFill) progressFill.style.width = '100%';
            setTimeout(function() {
                if (progressBar) progressBar.classList.remove('active');
                if (progressFill) progressFill.style.width = '0%';
            }, 1000);

            if (data.success) {
                var html = '<div style="font-weight:600; margin-bottom:0.5rem;">Upload Complete</div>';
                if (data.added_count > 0) {
                    html += '<div class="success-item">✅ ' + data.added_count + ' mappings added successfully</div>';
                }
                if (data.skipped_count > 0) {
                    html += '<div class="error-item">⚠️ ' + data.skipped_count + ' rows skipped</div>';
                }
                if (data.errors && data.errors.length > 0) {
                    html += '<div style="margin-top:0.5rem;"><strong>Errors:</strong></div>';
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">❌ ' + err + '</div>';
                    });
                }
                if (resultDiv) resultDiv.innerHTML = html;
                showToast(data.message || 'Bulk upload completed successfully!', 'success');
                setTimeout(function() {
                    location.reload();
                }, 2000);
            } else {
                var html = '<div style="font-weight:600; color:var(--smap-danger); margin-bottom:0.5rem;">Upload Failed</div>';
                if (data.errors && data.errors.length > 0) {
                    data.errors.forEach(function(err) {
                        html += '<div class="error-item">❌ ' + err + '</div>';
                    });
                } else {
                    html += '<div class="error-item">❌ ' + (data.message || 'Unknown error occurred') + '</div>';
                }
                if (resultDiv) resultDiv.innerHTML = html;
                showToast(data.message || 'Bulk upload failed', 'error');
            }

            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload';
            }
        })
        .catch(function(error) {
            if (progressFill) progressFill.style.width = '100%';
            setTimeout(function() {
                if (progressBar) progressBar.classList.remove('active');
                if (progressFill) progressFill.style.width = '0%';
            }, 1000);
            if (resultDiv) resultDiv.innerHTML = '<div class="error-item">❌ Error: ' + error.message + '</div>';
            showToast('Error: ' + error.message, 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload';
            }
        });
    }

    // ============================================================
    // CLOSE MODALS ON OVERLAY CLICK
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {
        var modals = ['viewModal', 'addModal', 'removeModal', 'bulkUploadModal'];
        modals.forEach(function(id) {
            var el = document.getElementById(id);
            if (el) {
                el.addEventListener('click', function(e) {
                    if (e.target === this) {
                        this.style.display = 'none';
                        this.classList.remove('active');
                    }
                });
            }
        });
    });

    // ============================================================
    // KEYBOARD SUPPORT
    // ============================================================
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            var modalIds = ['viewModal', 'addModal', 'removeModal', 'bulkUploadModal'];
            modalIds.forEach(function(id) {
                var el = document.getElementById(id);
                if (el && el.classList.contains('active')) {
                    el.style.display = 'none';
                    el.classList.remove('active');
                }
            });
        }
        if (e.key === 'Enter') {
            var addModalEl = document.getElementById('addModal');
            if (addModalEl && addModalEl.classList.contains('active')) {
                e.preventDefault();
                submitAdd();
            }
        }
    });

    // ============================================================
    // SPINNER STYLES
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
        .success-item { color: #22C55E; font-size: 0.8rem; margin: 0.2rem 0; }
        .error-item { color: #EF4444; font-size: 0.8rem; margin: 0.2rem 0; }
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-width: 400px;
        }
        .toast {
            padding: 12px 20px;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: slideInRight 0.3s ease;
        }
        .toast.success { background: linear-gradient(135deg, #16a34a, #22c55e); }
        .toast.error { background: linear-gradient(135deg, #dc2626, #ef4444); }
        .toast.warning { background: linear-gradient(135deg, #d97706, #f59e0b); }
        .toast.info { background: linear-gradient(135deg, #2563eb, #3b82f6); }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .modal-overlay {
            display: none !important;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1050;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }
        .modal-overlay.active {
            display: flex !important;
        }
        .modal-box {
            background: var(--smap-bg-card, #fff);
            border-radius: 18px;
            padding: 1.5rem 2rem 2rem;
            width: 90%;
            max-width: 750px;
            max-height: 85vh;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: modalIn 0.3s ease;
            border: 1px solid var(--smap-border, #e5e7eb);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }
        @keyframes modalIn {
            from { opacity: 0; transform: scale(0.92) translateY(20px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.3rem;
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--smap-text-secondary, #4a5568);
        }
        .form-control {
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid var(--smap-border, #e5e7eb);
            border-radius: 8px;
            font-size: 0.85rem;
            background: var(--smap-bg-card, #fff);
            color: var(--smap-text-primary, #1a202c);
        }
        .form-control:focus {
            outline: none;
            border-color: var(--smap-orange, #ff6b00);
            box-shadow: 0 0 0 3px rgba(255,107,0,0.1);
        }
        [data-theme="dark"] .form-control {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.1);
            color: #e8edf5;
        }
        [data-theme="dark"] .form-control option {
            background: #1a1a2e;
        }
    `;
    document.head.appendChild(style);

    // ============================================================
    // EXPOSE FUNCTIONS GLOBALLY
    // ============================================================
    window.openAddModal = openAddModal;
    window.closeAddModal = closeAddModal;
    window.submitAdd = submitAdd;
    window.viewScreens = viewScreens;
    window.closeViewModal = closeViewModal;
    window.addScreenFromModal = addScreenFromModal;
    window.openRemoveModal = openRemoveModal;
    window.closeRemoveModal = closeRemoveModal;
    window.submitRemove = submitRemove;
    window.confirmDeleteErp = confirmDeleteErp;
    window.openBulkUploadModal = openBulkUploadModal;
    window.closeBulkUploadModal = closeBulkUploadModal;
    window.handleBulkFileSelect = handleBulkFileSelect;
    window.submitBulkUpload = submitBulkUpload;
    window.showToast = showToast;

    // ============================================================
    // INITIALIZATION - FIX MODAL DISPLAY
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ Screen Mapping JS loaded successfully');
        
        // Ensure all modals are hidden initially
        var modalIds = ['viewModal', 'addModal', 'removeModal', 'bulkUploadModal'];
        modalIds.forEach(function(id) {
            var el = document.getElementById(id);
            if (el) {
                el.style.display = 'none';
                el.classList.remove('active');
            }
        });
        
        // Debug: Check if elements exist
        console.log('📌 Add Modal:', document.getElementById('addModal'));
        console.log('📌 Add ERP Select:', document.getElementById('addErpId'));
        console.log('📌 Add Screen Select:', document.getElementById('addScreen'));
        console.log('📌 Toast Container:', document.getElementById('toastContainer'));
        
        // Test toast
        // showToast('✅ Screen Mapping loaded successfully!', 'success');
    });

})(); // End of IIFE