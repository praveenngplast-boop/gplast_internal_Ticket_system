// ============================================================
// GPLAST — SCREEN MASTER
// Table view · Pagination · Bulk select/edit/delete · Upload
// ============================================================

(function () {
    'use strict';

    // ============================================================
    // CONFIG
    // ============================================================
    var API = {
        add:         '/custom-admin/settings/screen-master/add/',
        edit:        '/custom-admin/settings/screen-master/edit/',
        del:         '/custom-admin/settings/screen-master/delete/',
        bulkUpload:  '/custom-admin/settings/screen-master/bulk-upload/',
        bulkEdit:    '/custom-admin/settings/screen-master/bulk-edit/',
        bulkDelete:  '/custom-admin/settings/screen-master/bulk-delete/'
    };


    // ============================================================
    // STATE
    // ============================================================
    var selectedIds = new Set();
    var selectedMeta = new Map();
    var selectedFiles = [];


    // ============================================================
    // HELPERS
    // ============================================================
    function $(sel, root) { return (root || document).querySelector(sel); }
    function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

    function getCSRF() {
        var el = $('[name=csrfmiddlewaretoken]');
        if (el) return el.value;
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    function escapeHtml(s) {
        var d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    function formatBytes(n) {
        if (n < 1024) return n + ' B';
        if (n < 1048576) return (n / 1024).toFixed(1) + ' KB';
        return (n / 1048576).toFixed(2) + ' MB';
    }


    // ============================================================
    // TOASTS
    // ============================================================
    function showToast(msg, type) {
        type = type || 'info';
        var container = $('#toastContainer');
        if (!container) return;
        var t = document.createElement('div');
        t.className = 'sm-toast ' + type;
        var icon = type === 'success' ? 'check-circle'
                 : type === 'error'   ? 'times-circle'
                 : type === 'warning' ? 'triangle-exclamation'
                 : 'info-circle';
        t.innerHTML = '<i class="fas fa-' + icon + '"></i><span>' + escapeHtml(msg) + '</span>';
        container.appendChild(t);
        setTimeout(function () {
            t.style.opacity = '0';
            t.style.transform = 'translateX(30px)';
            setTimeout(function () {
                if (t.parentNode) t.parentNode.removeChild(t);
            }, 350);
        }, 4000);
    }


    // ============================================================
    // MODALS
    // ============================================================
    function openModal(id) {
        var m = document.getElementById(id);
        if (m) {
            m.classList.add('active');
            m.setAttribute('aria-hidden', 'false');
        }
    }

    function closeModal(id) {
        var m = document.getElementById(id);
        if (m) {
            m.classList.remove('active');
            m.setAttribute('aria-hidden', 'true');
        }
    }

    function closeAllModals() {
        ['addModal', 'editModal', 'deleteModal', 'bulkEditModal', 'bulkDeleteModal', 'bulkModal']
            .forEach(closeModal);
    }


    // ============================================================
    // SELECTION
    // ============================================================
    function updateSelectionUI() {
        var bar = $('#bulkActionBar');
        var countEl = $('#bulkCount');
        var n = selectedIds.size;

        if (bar) bar.hidden = n === 0;
        if (countEl) countEl.textContent = n;

        var header = $('#selectAllCheckbox');
        if (header) {
            var boxes = $$('.sm-row-checkbox');
            var checked = boxes.filter(function (cb) { return cb.checked; }).length;

            if (boxes.length === 0 || checked === 0) {
                header.checked = false;
                header.indeterminate = false;
            } else if (checked === boxes.length) {
                header.checked = true;
                header.indeterminate = false;
            } else {
                header.checked = false;
                header.indeterminate = true;
            }
        }
    }

    function clearSelection() {
        selectedIds.clear();
        selectedMeta.clear();

        $$('.sm-row-checkbox').forEach(function (cb) {
            cb.checked = false;
            var row = cb.closest('tr');
            if (row) row.classList.remove('sm-row-selected');
        });

        var header = $('#selectAllCheckbox');
        if (header) {
            header.checked = false;
            header.indeterminate = false;
        }

        updateSelectionUI();
    }

    function setRowSelected(checkbox, isSelected) {
        var id = checkbox.value;
        var row = checkbox.closest('tr');

        checkbox.checked = isSelected;
        if (row) row.classList.toggle('sm-row-selected', isSelected);

        if (isSelected) {
            selectedIds.add(id);
            selectedMeta.set(id, {
                code: checkbox.dataset.code || '',
                name: checkbox.dataset.name || ''
            });
        } else {
            selectedIds.delete(id);
            selectedMeta.delete(id);
        }
    }

    function toggleSelectAll(headerCheckbox) {
        var select = headerCheckbox.checked;
        $$('.sm-row-checkbox').forEach(function (cb) {
            setRowSelected(cb, select);
        });
        updateSelectionUI();
    }


    // ============================================================
    // SELECTED LIST HTML
    // ============================================================
    function buildSelectedListHtml(max) {
        max = max || 20;
        var items = Array.from(selectedMeta.entries());
        var shown = items.slice(0, max);

        var html = shown.map(function (entry) {
            var meta = entry[1];
            return '' +
                '<div class="sm-selected-item">' +
                    '<i class="fas fa-desktop"></i>' +
                    '<span class="scode">' + escapeHtml(meta.code || '—') + '</span>' +
                    '<span class="sname">' + escapeHtml(meta.name || '') + '</span>' +
                '</div>';
        }).join('');

        if (items.length > max) {
            html += '<div class="sm-selected-more">+ ' + (items.length - max) + ' more…</div>';
        }
        return html || '<div class="sm-selected-item">No items</div>';
    }


    // ============================================================
    // ADD
    // ============================================================
    function openAdd() {
        $('#addCode').value = '';
        $('#addName').value = '';
        $('#addType').value = 'ALL';
        openModal('addModal');
        setTimeout(function () { $('#addCode').focus(); }, 200);
    }

    function submitAdd() {
        var code = $('#addCode').value.trim();
        var name = $('#addName').value.trim();
        var type = $('#addType').value;

        if (!code || !name) {
            showToast('Screen Code and Name are required', 'error');
            return;
        }

        var fd = new FormData();
        fd.append('screen_code', code);
        fd.append('screen_name', name);
        fd.append('screen_type', type);

        fetch(API.add, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd,
            credentials: 'same-origin'
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (d.success) {
                showToast(d.message, 'success');
                closeModal('addModal');
                setTimeout(function () { location.reload(); }, 900);
            } else {
                showToast(d.message, 'error');
            }
        })
        .catch(function (e) { showToast('Error: ' + e.message, 'error'); });
    }


    // ============================================================
    // EDIT
    // ============================================================
    function openEdit(id, code, name, type) {
        $('#editId').value = id;
        $('#editCode').value = code;
        $('#editName').value = name;
        $('#editType').value = type;
        openModal('editModal');
        setTimeout(function () { $('#editCode').focus(); }, 200);
    }

    function submitEdit() {
        var id = $('#editId').value;
        var code = $('#editCode').value.trim();
        var name = $('#editName').value.trim();
        var type = $('#editType').value;

        if (!code || !name) {
            showToast('Screen Code and Name are required', 'error');
            return;
        }

        var fd = new FormData();
        fd.append('screen_id', id);
        fd.append('screen_code', code);
        fd.append('screen_name', name);
        fd.append('screen_type', type);

        fetch(API.edit, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd,
            credentials: 'same-origin'
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (d.success) {
                showToast(d.message, 'success');
                closeModal('editModal');
                setTimeout(function () { location.reload(); }, 900);
            } else {
                showToast(d.message, 'error');
            }
        })
        .catch(function (e) { showToast('Error: ' + e.message, 'error'); });
    }


    // ============================================================
    // DELETE (single)
    // ============================================================
    function openDelete(id, name) {
        $('#deleteId').value = id;
        $('#deleteName').textContent = name;
        openModal('deleteModal');
    }

    function submitDelete() {
        var id = $('#deleteId').value;

        var fd = new FormData();
        fd.append('screen_id', id);

        fetch(API.del, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd,
            credentials: 'same-origin'
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (d.success) {
                showToast(d.message, 'success');
                closeModal('deleteModal');
                setTimeout(function () { location.reload(); }, 700);
            } else {
                showToast(d.message, 'error');
            }
        })
        .catch(function (e) { showToast('Error: ' + e.message, 'error'); });
    }


    // ============================================================
    // BULK EDIT
    // ============================================================
    function openBulkEdit() {
        if (selectedIds.size === 0) return;
        $('#bulkEditSelectedList').innerHTML = buildSelectedListHtml();
        $('#bulkEditType').value = '';
        $('#bulkEditBtnText').textContent = 'Apply to ' + selectedIds.size + ' screen' + (selectedIds.size > 1 ? 's' : '');
        openModal('bulkEditModal');
    }

    function submitBulkEdit() {
        var type = $('#bulkEditType').value;
        if (!type) {
            showToast('Select a Screen Type to apply', 'error');
            return;
        }
        if (selectedIds.size === 0) {
            showToast('No screens selected', 'error');
            return;
        }

        var btn = $('#bulkEditSubmitBtn');
        var original = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Applying…';

        var fd = new FormData();
        fd.append('screen_ids', Array.from(selectedIds).join(','));
        fd.append('screen_type', type);

        fetch(API.bulkEdit, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd,
            credentials: 'same-origin'
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (d.success) {
                showToast(d.message || 'Screens updated', 'success');
                closeModal('bulkEditModal');
                clearSelection();
                setTimeout(function () { location.reload(); }, 1000);
            } else {
                showToast(d.message || 'Failed', 'error');
            }
        })
        .catch(function (e) { showToast('Error: ' + e.message, 'error'); })
        .finally(function () {
            btn.disabled = false;
            btn.innerHTML = original;
        });
    }


    // ============================================================
    // BULK DELETE
    // ============================================================
    function openBulkDelete() {
        if (selectedIds.size === 0) return;
        $('#bulkDeleteSelectedList').innerHTML = buildSelectedListHtml();
        $('#bulkDeleteCount').textContent = selectedIds.size;
        $('#bulkDeleteBtnText').textContent = 'Delete ' + selectedIds.size + ' screen' + (selectedIds.size > 1 ? 's' : '');
        openModal('bulkDeleteModal');
    }

    function submitBulkDelete() {
        if (selectedIds.size === 0) {
            showToast('No screens selected', 'error');
            return;
        }

        var btn = $('#bulkDeleteSubmitBtn');
        var original = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Deleting…';

        var fd = new FormData();
        fd.append('screen_ids', Array.from(selectedIds).join(','));

        fetch(API.bulkDelete, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd,
            credentials: 'same-origin'
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            if (d.success) {
                showToast(d.message || 'Screens deleted', 'success');
                closeModal('bulkDeleteModal');
                clearSelection();
                setTimeout(function () { location.reload(); }, 1000);
            } else {
                showToast(d.message || 'Failed', 'error');
            }
        })
        .catch(function (e) { showToast('Error: ' + e.message, 'error'); })
        .finally(function () {
            btn.disabled = false;
            btn.innerHTML = original;
        });
    }


    // ============================================================
    // BULK UPLOAD
    // ============================================================
    function openBulkUpload() {
        selectedFiles = [];
        renderFilePreview();

        var fileInput = $('#bulkFile');
        if (fileInput) fileInput.value = '';

        var result = $('#uploadResult');
        if (result) result.innerHTML = '';

        var pb = $('#progressBar');
        if (pb) pb.classList.remove('active');

        var pf = $('#progressFill');
        if (pf) pf.style.width = '0%';

        openModal('bulkModal');
    }

    function addFiles(fileList) {
        var validExt = /\.(xlsx|xls)$/i;
        Array.prototype.slice.call(fileList).forEach(function (f) {
            if (!validExt.test(f.name)) {
                showToast('Skipped "' + f.name + '" — only .xlsx/.xls', 'error');
                return;
            }
            var duplicate = selectedFiles.some(function (s) {
                return s.name === f.name && s.size === f.size;
            });
            if (duplicate) {
                showToast('"' + f.name + '" already added', 'info');
                return;
            }
            selectedFiles.push(f);
        });
        renderFilePreview();
    }

    function renderFilePreview() {
        var list = $('#filePreviewList');
        var label = $('#fileName');
        if (!list) return;

        if (selectedFiles.length === 0) {
            if (label) label.textContent = 'No files selected';
            list.innerHTML = '';
            return;
        }

        var total = selectedFiles.reduce(function (s, f) { return s + f.size; }, 0);
        if (label) {
            label.textContent = selectedFiles.length + ' file' +
                (selectedFiles.length > 1 ? 's' : '') + ' selected · ' + formatBytes(total);
        }

        list.innerHTML = selectedFiles.map(function (f, i) {
            return '' +
                '<div class="sm-file-item">' +
                    '<div class="fname"><i class="fas fa-file-excel" style="color:#22c55e;"></i><span>' +
                        escapeHtml(f.name) + '</span></div>' +
                    '<span class="fsize">' + formatBytes(f.size) + '</span>' +
                    '<button type="button" class="fremove" data-index="' + i + '">' +
                        '<i class="fas fa-times"></i>' +
                    '</button>' +
                '</div>';
        }).join('');

        $$('.fremove', list).forEach(function (btn) {
            btn.addEventListener('click', function () {
                var idx = parseInt(this.dataset.index, 10);
                selectedFiles.splice(idx, 1);
                renderFilePreview();
            });
        });
    }

    function submitBulkUpload() {
        if (selectedFiles.length === 0) {
            showToast('Select at least one file', 'error');
            return;
        }

        var btn = $('#bulkUploadBtn');
        var progressBar = $('#progressBar');
        var progressFill = $('#progressFill');
        var resultDiv = $('#uploadResult');

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Uploading…';
        progressBar.classList.add('active');
        progressFill.style.width = '0%';
        resultDiv.innerHTML = '';

        var totalAdded = 0;
        var totalSkipped = 0;
        var allErrors = [];
        var perFile = [];
        var i = 0;

        function next() {
            if (i >= selectedFiles.length) return finish();

            var file = selectedFiles[i];
            var fd = new FormData();
            fd.append('excel_file', file);

            fetch(API.bulkUpload, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRF(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: fd,
                credentials: 'same-origin'
            })
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (d) {
                perFile.push({
                    name: file.name,
                    success: !!d.success,
                    added: d.added_count || 0,
                    skipped: d.skipped_count || 0
                });
                if (d.success) {
                    totalAdded += d.added_count || 0;
                    totalSkipped += d.skipped_count || 0;
                    if (d.errors && d.errors.length) {
                        d.errors.forEach(function (e) {
                            allErrors.push('[' + file.name + '] ' + e);
                        });
                    }
                } else {
                    allErrors.push('[' + file.name + '] ' + (d.message || 'Upload failed'));
                }
            })
            .catch(function (err) {
                perFile.push({ name: file.name, success: false, added: 0, skipped: 0 });
                allErrors.push('[' + file.name + '] ' + err.message);
            })
            .finally(function () {
                i++;
                progressFill.style.width = Math.round((i / selectedFiles.length) * 100) + '%';
                setTimeout(next, 80);
            });
        }

        function finish() {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-upload"></i> Upload';

            var html = '<div style="font-weight:600;margin-bottom:0.5rem;">' +
                '<i class="fas fa-check-circle" style="color:#22c55e;"></i> ' +
                totalAdded + ' added, ' + totalSkipped + ' skipped</div>';

            html += '<div>';
            perFile.forEach(function (r) {
                var icon = r.success
                    ? '<i class="fas fa-check" style="color:#22c55e;"></i>'
                    : '<i class="fas fa-times" style="color:#ef4444;"></i>';
                html += '<div style="padding:0.25rem 0;">' + icon + ' ' +
                    escapeHtml(r.name) + ' — ' + r.added + ' added, ' + r.skipped + ' skipped</div>';
            });
            html += '</div>';

            if (allErrors.length) {
                html += '<details style="margin-top:0.5rem;">' +
                    '<summary style="cursor:pointer;color:#ef4444;font-weight:600;font-size:0.78rem;">' +
                    allErrors.length + ' error(s)</summary>' +
                    '<ul style="margin:0.5rem 0 0 1rem;font-size:0.72rem;color:#64748b;">' +
                    allErrors.slice(0, 30).map(function (e) {
                        return '<li>' + escapeHtml(e) + '</li>';
                    }).join('') +
                    '</ul></details>';
            }

            resultDiv.innerHTML = html;

            if (totalAdded > 0) {
                showToast('Added ' + totalAdded + ' screen(s)', 'success');
                setTimeout(function () { location.reload(); }, 2000);
            } else {
                showToast('No screens were added', 'error');
            }
        }

        next();
    }


    // ============================================================
    // BIND EVENTS
    // ============================================================
    function bindEvents() {
        // ---- Filter form: search input submits on Enter ----
        var searchInput = $('#smSearchInput');
        var filterForm = $('#smFilterForm');
        if (searchInput && filterForm) {
            searchInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    filterForm.submit();
                }
            });
        }

        // ---- Filter form: type select auto-submits on change ----
        var typeSelect = $('#smTypeSelect');
        if (typeSelect && filterForm) {
            typeSelect.addEventListener('change', function () {
                filterForm.submit();
            });
        }

        // ---- Header checkbox ----
        var header = $('#selectAllCheckbox');
        if (header) {
            header.addEventListener('change', function () {
                toggleSelectAll(this);
            });
        }

        // ---- Row checkboxes ----
        $$('.sm-row-checkbox').forEach(function (cb) {
            cb.addEventListener('change', function () {
                setRowSelected(this, this.checked);
                updateSelectionUI();
            });
        });

        // ---- Delegated click for data-action / data-close ----
        document.addEventListener('click', function (e) {
            var target = e.target.closest('[data-action], [data-close]');
            if (!target) return;

            var closeId = target.getAttribute('data-close');
            if (closeId) {
                e.preventDefault();
                closeModal(closeId);
                return;
            }

            var action = target.getAttribute('data-action');
            if (!action) return;
            e.preventDefault();

            switch (action) {
                case 'open-add':
                    openAdd();
                    break;
                case 'open-bulk-upload':
                    openBulkUpload();
                    break;
                case 'submit-add':
                    submitAdd();
                    break;
                case 'submit-edit':
                    submitEdit();
                    break;
                case 'submit-delete':
                    submitDelete();
                    break;
                case 'submit-bulk-edit':
                    submitBulkEdit();
                    break;
                case 'submit-bulk-delete':
                    submitBulkDelete();
                    break;
                case 'submit-bulk-upload':
                    submitBulkUpload();
                    break;
                case 'edit':
                    openEdit(
                        target.dataset.id,
                        target.dataset.code,
                        target.dataset.name,
                        target.dataset.type
                    );
                    break;
                case 'delete':
                    openDelete(target.dataset.id, target.dataset.name);
                    break;
            }
        });

        // ---- Bulk bar ----
        var clearBtn = $('#bulkClearBtn');
        if (clearBtn) clearBtn.addEventListener('click', clearSelection);

        var bulkEditBtn = $('#bulkEditBtn');
        if (bulkEditBtn) bulkEditBtn.addEventListener('click', openBulkEdit);

        var bulkDeleteBtn = $('#bulkDeleteBtn');
        if (bulkDeleteBtn) bulkDeleteBtn.addEventListener('click', openBulkDelete);

        // ---- File input ----
        var fileInput = $('#bulkFile');
        if (fileInput) {
            fileInput.addEventListener('change', function () {
                addFiles(this.files);
                this.value = '';
            });
        }

        // ---- Upload area ----
        var uploadArea = $('#uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('click', function () {
                var fi = $('#bulkFile');
                if (fi) fi.click();
            });

            uploadArea.addEventListener('dragover', function (e) {
                e.preventDefault();
                this.style.borderColor = 'var(--sm-orange)';
                this.style.background = 'rgba(255,107,0,0.05)';
            });
            uploadArea.addEventListener('dragleave', function (e) {
                e.preventDefault();
                this.style.borderColor = '';
                this.style.background = '';
            });
            uploadArea.addEventListener('drop', function (e) {
                e.preventDefault();
                this.style.borderColor = '';
                this.style.background = '';
                if (e.dataTransfer.files.length) {
                    addFiles(e.dataTransfer.files);
                }
            });
        }

        // ---- Close modal on backdrop click ----
        $$('.sm-modal').forEach(function (m) {
            m.addEventListener('click', function (e) {
                if (e.target === this) {
                    this.classList.remove('active');
                    this.setAttribute('aria-hidden', 'true');
                }
            });
        });

        // ---- Keyboard ----
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                var addOpen = $('#addModal');
                var editOpen = $('#editModal');
                if (addOpen && addOpen.classList.contains('active')) {
                    e.preventDefault();
                    submitAdd();
                } else if (editOpen && editOpen.classList.contains('active')) {
                    e.preventDefault();
                    submitEdit();
                }
            }
            if (e.key === 'Escape') {
                closeAllModals();
            }
        });
    }


    // ============================================================
    // BOOT
    // ============================================================
    function boot() {
        bindEvents();
        updateSelectionUI();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

})();