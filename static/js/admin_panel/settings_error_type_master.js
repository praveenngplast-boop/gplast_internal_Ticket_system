// ============================================================
// GPLAST — ERROR TYPE MASTER
// Admin page · Main + Sub error type CRUD
// ============================================================

(function () {
    'use strict';


    // ============================================================
    // API ENDPOINTS
    // ============================================================
    var API = {
        mainAdd:     '/custom-admin/settings/error-types/main/add/',
        mainEdit:    '/custom-admin/settings/error-types/main/edit/',
        mainDelete:  '/custom-admin/settings/error-types/main/delete/',
        mainToggle:  '/custom-admin/settings/error-types/main/toggle/',
        subAdd:      '/custom-admin/settings/error-types/sub/add/',
        subEdit:     '/custom-admin/settings/error-types/sub/edit/',
        subDelete:   '/custom-admin/settings/error-types/sub/delete/',
        subToggle:   '/custom-admin/settings/error-types/sub/toggle/',
        subsForMain: '/custom-admin/settings/error-types/subs-for/'
    };


    // ============================================================
    // STATE
    // ============================================================
    var state = {
        mains: [],                 // Array of { id, name, display_order, is_active, subs: [] }
        selectedMainId: null,      // Currently selected main id
        mainSearchTerm: '',        // Left list search
        subSearchTerm: '',         // Right list search
        pendingDeleteMain: null,   // { id, name, subsCount }
        pendingDeleteSub: null     // { id, name }
    };


    // ============================================================
    // HELPERS
    // ============================================================
    function $(sel, root) { return (root || document).querySelector(sel); }
    function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

    function escapeHtml(s) {
        var d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    function toInt(v, fallback) {
        var n = parseInt(v, 10);
        return isNaN(n) ? (fallback || 0) : n;
    }

    function getCSRF() {
        // Prefer shell helper if available
        if (typeof window.getCSRFToken === 'function') {
            try { return window.getCSRFToken(); } catch (e) {}
        }
        // Fallback: read cookie
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        if (m) return m[1];
        // Fallback: hidden input
        var el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function postForm(url, data) {
        var fd = new FormData();
        Object.keys(data).forEach(function (k) {
            fd.append(k, data[k]);
        });
        return fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: fd,
            credentials: 'same-origin'
        }).then(function (r) {
            // Parse JSON even on non-2xx so we can show the message
            return r.json().catch(function () {
                return { success: false, message: 'Invalid server response (' + r.status + ')' };
            });
        });
    }


    // ============================================================
    // TOASTS
    // ============================================================
    function showToast(message, type) {
        type = type || 'success';
        var container = $('#etmToasts');
        if (!container) return;

        var iconMap = {
            success: 'fa-check-circle',
            error:   'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info:    'fa-info-circle'
        };
        var clsMap = {
            success: 'etm-toast-success',
            error:   'etm-toast-error',
            warning: 'etm-toast-warning',
            info:    'etm-toast-info'
        };

        var el = document.createElement('div');
        el.className = 'etm-toast ' + (clsMap[type] || clsMap.info);
        el.innerHTML = '<i class="fas ' + (iconMap[type] || iconMap.info) + '"></i><span>'
                     + escapeHtml(message) + '</span>';
        container.appendChild(el);

        setTimeout(function () {
            el.style.opacity = '0';
            el.style.transform = 'translateX(30px)';
            setTimeout(function () {
                if (el.parentNode) el.parentNode.removeChild(el);
            }, 350);
        }, 4000);
    }


    // ============================================================
    // MODALS
    // ============================================================
    function openModal(id) {
        var m = document.getElementById(id);
        if (m) {
            m.classList.add('etm-modal-open');
            m.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeModal(id) {
        var m = document.getElementById(id);
        if (m) {
            m.classList.remove('etm-modal-open');
            m.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }
    }

    function closeAllModals() {
        ['mainModal', 'subModal', 'deleteMainModal', 'deleteSubModal'].forEach(closeModal);
    }


    // ============================================================
    // STATE LOOKUP HELPERS
    // ============================================================
    function findMainById(id) {
        id = String(id);
        for (var i = 0; i < state.mains.length; i++) {
            if (String(state.mains[i].id) === id) return state.mains[i];
        }
        return null;
    }

    function findSubById(mainId, subId) {
        var main = findMainById(mainId);
        if (!main) return null;
        subId = String(subId);
        for (var i = 0; i < main.subs.length; i++) {
            if (String(main.subs[i].id) === subId) return main.subs[i];
        }
        return null;
    }


    // ============================================================
    // STATS UPDATE
    // ============================================================
    function updateStats() {
        var totalMains = state.mains.length;
        var totalSubs = 0;
        var activeMains = 0;
        var activeSubs = 0;

        state.mains.forEach(function (m) {
            if (m.is_active) activeMains++;
            totalSubs += m.subs.length;
            m.subs.forEach(function (s) { if (s.is_active) activeSubs++; });
        });

        var set = function (id, val) {
            var el = document.getElementById(id);
            if (el) el.textContent = val;
        };
        set('statTotalMains', totalMains);
        set('statTotalSubs', totalSubs);
        set('statActiveMains', activeMains);
        set('statActiveSubs', activeSubs);

        set('mainsCount', totalMains);
    }


    // ============================================================
    // RENDER — MAIN LIST
    // ============================================================
    function renderMains() {
        var list = $('#mainsList');
        if (!list) return;

        var q = state.mainSearchTerm.trim().toLowerCase();
        var visible = state.mains.filter(function (m) {
            if (!q) return true;
            return m.name.toLowerCase().indexOf(q) !== -1;
        });

        if (visible.length === 0) {
            var isEmptyOverall = state.mains.length === 0;
            list.innerHTML = ''
                + '<div class="etm-empty">'
                +   '<i class="fas fa-layer-group"></i>'
                +   '<p class="etm-empty-title">'
                +     (isEmptyOverall ? 'No main error types yet' : 'No matches')
                +   '</p>'
                +   '<p class="etm-empty-sub">'
                +     (isEmptyOverall
                        ? 'Click <strong>Add Main Type</strong> to get started.'
                        : 'Try a different search term.')
                +   '</p>'
                + '</div>';
            return;
        }

        var html = '';
        visible.forEach(function (m) {
            var isSelected = String(m.id) === String(state.selectedMainId);
            var cls = 'etm-main-item';
            if (isSelected) cls += ' etm-selected';
            if (!m.is_active) cls += ' etm-item-inactive';

            var subsCount = m.subs.length;
            var inactiveTag = m.is_active ? '' : '<span class="etm-tag etm-tag-muted">Inactive</span>';

            html += ''
                + '<article class="' + cls + '"'
                + ' data-main-id="' + m.id + '"'
                + ' data-main-name="' + escapeHtml(m.name) + '"'
                + ' data-main-order="' + m.display_order + '"'
                + ' data-main-active="' + (m.is_active ? '1' : '0') + '"'
                + ' role="option"'
                + ' aria-selected="' + (isSelected ? 'true' : 'false') + '">'

                +   '<div class="etm-main-marker"></div>'

                +   '<div class="etm-main-content">'
                +     '<div class="etm-main-name">' + escapeHtml(m.name) + inactiveTag + '</div>'
                +     '<div class="etm-main-meta">'
                +       '<span class="etm-main-subs-count">'
                +         '<i class="fas fa-list-ul"></i> '
                +         subsCount + ' sub type' + (subsCount === 1 ? '' : 's')
                +       '</span>'
                +       '<span class="etm-main-order">Order: ' + m.display_order + '</span>'
                +     '</div>'
                +   '</div>'

                +   '<div class="etm-main-actions">'
                +     '<button type="button" class="etm-icon-btn" title="Toggle active"'
                +     ' data-action="toggle-main" data-id="' + m.id + '"'
                +     ' data-active="' + (m.is_active ? '1' : '0') + '">'
                +       '<i class="fas ' + (m.is_active ? 'fa-toggle-on' : 'fa-toggle-off') + '"></i>'
                +     '</button>'
                +     '<button type="button" class="etm-icon-btn" title="Edit main"'
                +     ' data-action="edit-main" data-id="' + m.id + '"'
                +     ' data-name="' + escapeHtml(m.name) + '"'
                +     ' data-order="' + m.display_order + '"'
                +     ' data-active="' + (m.is_active ? '1' : '0') + '">'
                +       '<i class="fas fa-pen"></i>'
                +     '</button>'
                +     '<button type="button" class="etm-icon-btn etm-icon-danger" title="Delete main"'
                +     ' data-action="delete-main" data-id="' + m.id + '"'
                +     ' data-name="' + escapeHtml(m.name) + '"'
                +     ' data-subs-count="' + subsCount + '">'
                +       '<i class="fas fa-trash"></i>'
                +     '</button>'
                +   '</div>'

                + '</article>';
        });

        list.innerHTML = html;
    }


    // ============================================================
    // RENDER — SUB LIST
    // ============================================================
    function renderSubs() {
        var placeholder = $('#subsPlaceholder');
        var wrapper = $('#subsWrapper');
        var list = $('#subsList');
        var label = $('#subsPanelMainName');
        var countEl = $('#subsCount');
        var addBtn = $('#addSubBtn');

        var main = state.selectedMainId ? findMainById(state.selectedMainId) : null;

        if (!main) {
            if (placeholder) placeholder.hidden = false;
            if (wrapper) wrapper.hidden = true;
            if (label) label.textContent = '';
            if (countEl) countEl.textContent = '0';
            if (addBtn) addBtn.disabled = true;
            return;
        }

        if (placeholder) placeholder.hidden = true;
        if (wrapper) wrapper.hidden = false;
        if (label) label.textContent = '— ' + main.name;
        if (addBtn) addBtn.disabled = false;

        var q = state.subSearchTerm.trim().toLowerCase();
        var visible = main.subs.filter(function (s) {
            if (!q) return true;
            return s.name.toLowerCase().indexOf(q) !== -1;
        });

        if (countEl) countEl.textContent = main.subs.length;

        if (visible.length === 0) {
            var isEmpty = main.subs.length === 0;
            list.innerHTML = ''
                + '<div class="etm-empty">'
                +   '<i class="fas fa-list-ul"></i>'
                +   '<p class="etm-empty-title">'
                +     (isEmpty ? 'No sub types yet' : 'No matches')
                +   '</p>'
                +   '<p class="etm-empty-sub">'
                +     (isEmpty
                        ? 'Click <strong>Add Sub</strong> to add the first one.'
                        : 'Try a different search term.')
                +   '</p>'
                + '</div>';
            return;
        }

        var html = '';
        visible.forEach(function (s, idx) {
            var cls = 'etm-sub-item';
            if (!s.is_active) cls += ' etm-item-inactive';

            var inactiveTag = s.is_active ? '' : '<span class="etm-tag etm-tag-muted">Inactive</span>';

            html += ''
                + '<article class="' + cls + '"'
                + ' data-sub-id="' + s.id + '"'
                + ' data-sub-main-id="' + main.id + '"'
                + ' data-sub-name="' + escapeHtml(s.name) + '"'
                + ' data-sub-order="' + s.display_order + '"'
                + ' data-sub-active="' + (s.is_active ? '1' : '0') + '"'
                + ' role="option">'

                +   '<div class="etm-sub-index">' + (idx + 1) + '</div>'

                +   '<div class="etm-sub-content">'
                +     '<div class="etm-sub-name">' + escapeHtml(s.name) + inactiveTag + '</div>'
                +     '<div class="etm-sub-meta">Order: ' + s.display_order + '</div>'
                +   '</div>'

                +   '<div class="etm-sub-actions">'
                +     '<button type="button" class="etm-icon-btn" title="Toggle active"'
                +     ' data-action="toggle-sub" data-id="' + s.id + '"'
                +     ' data-main-id="' + main.id + '"'
                +     ' data-active="' + (s.is_active ? '1' : '0') + '">'
                +       '<i class="fas ' + (s.is_active ? 'fa-toggle-on' : 'fa-toggle-off') + '"></i>'
                +     '</button>'
                +     '<button type="button" class="etm-icon-btn" title="Edit sub"'
                +     ' data-action="edit-sub" data-id="' + s.id + '"'
                +     ' data-main-id="' + main.id + '"'
                +     ' data-name="' + escapeHtml(s.name) + '"'
                +     ' data-order="' + s.display_order + '"'
                +     ' data-active="' + (s.is_active ? '1' : '0') + '">'
                +       '<i class="fas fa-pen"></i>'
                +     '</button>'
                +     '<button type="button" class="etm-icon-btn etm-icon-danger" title="Delete sub"'
                +     ' data-action="delete-sub" data-id="' + s.id + '"'
                +     ' data-main-id="' + main.id + '"'
                +     ' data-name="' + escapeHtml(s.name) + '">'
                +       '<i class="fas fa-trash"></i>'
                +     '</button>'
                +   '</div>'

                + '</article>';
        });

        list.innerHTML = html;
    }


    // ============================================================
    // RENDER EVERYTHING
    // ============================================================
    function renderAll() {
        renderMains();
        renderSubs();
        updateStats();
    }


    // ============================================================
    // SELECT MAIN
    // ============================================================
    function selectMain(id) {
        state.selectedMainId = id;
        state.subSearchTerm = '';
        var subSearchInput = $('#subSearchInput');
        if (subSearchInput) subSearchInput.value = '';
        renderAll();
    }


    // ============================================================
    // MAIN — OPEN ADD MODAL
    // ============================================================
    function openAddMain() {
        $('#mainFormId').value = '';
        $('#mainFormName').value = '';
        $('#mainFormOrder').value = '0';
        $('#mainFormActive').checked = true;
        $('#mainFormActiveLabel').textContent = 'Active';

        $('#mainModalTitleText').textContent = 'Add Main Error Type';
        $('#mainFormSubmitText').textContent = 'Save Main Type';

        openModal('mainModal');
        setTimeout(function () { $('#mainFormName').focus(); }, 200);
    }


    // ============================================================
    // MAIN — OPEN EDIT MODAL
    // ============================================================
    function openEditMain(btn) {
        var id = btn.getAttribute('data-id');
        var main = findMainById(id);
        if (!main) return;

        $('#mainFormId').value = main.id;
        $('#mainFormName').value = main.name;
        $('#mainFormOrder').value = main.display_order;
        $('#mainFormActive').checked = !!main.is_active;
        $('#mainFormActiveLabel').textContent = main.is_active ? 'Active' : 'Inactive';

        $('#mainModalTitleText').textContent = 'Edit Main Error Type';
        $('#mainFormSubmitText').textContent = 'Update Main Type';

        openModal('mainModal');
        setTimeout(function () { $('#mainFormName').focus(); }, 200);
    }


    // ============================================================
    // MAIN — SUBMIT FORM (ADD or EDIT)
    // ============================================================
    function submitMainForm(e) {
        if (e) e.preventDefault();

        var id = $('#mainFormId').value;
        var name = $('#mainFormName').value.trim();
        var order = toInt($('#mainFormOrder').value, 0);
        var isActive = $('#mainFormActive').checked;

        if (!name) {
            showToast('Please enter a name.', 'error');
            $('#mainFormName').focus();
            return;
        }

        var submitBtn = $('#mainFormSubmit');
        var originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving…';

        var isEdit = !!id;
        var url = isEdit ? API.mainEdit : API.mainAdd;
        var payload = {
            name: name,
            display_order: order,
            is_active: isActive ? 'true' : 'false'
        };
        if (isEdit) payload.id = id;

        postForm(url, payload)
            .then(function (res) {
                if (!res.success) {
                    showToast(res.message || 'Failed to save.', 'error');
                    return;
                }
                showToast(res.message || 'Saved.', 'success');
                closeModal('mainModal');
                return refreshMainListThenMaybeSelect(isEdit ? null : res.main);
            })
            .catch(function (err) {
                showToast('Network error: ' + err.message, 'error');
            })
            .finally(function () {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            });
    }


    // ============================================================
    // MAIN — TOGGLE ACTIVE
    // ============================================================
    function toggleMainActive(btn) {
        var id = btn.getAttribute('data-id');
        var main = findMainById(id);
        if (!main) return;

        btn.disabled = true;

        postForm(API.mainToggle, { id: main.id })
            .then(function (res) {
                if (!res.success) {
                    showToast(res.message || 'Failed to toggle.', 'error');
                    return;
                }
                // Optimistic update
                main.is_active = !!res.is_active;
                renderAll();
                showToast(res.message, res.is_active ? 'success' : 'info');
            })
            .catch(function (err) {
                showToast('Network error: ' + err.message, 'error');
            })
            .finally(function () {
                btn.disabled = false;
            });
    }


    // ============================================================
    // MAIN — OPEN DELETE CONFIRM
    // ============================================================
    function openDeleteMain(btn) {
        var id = btn.getAttribute('data-id');
        var main = findMainById(id);
        if (!main) return;

        state.pendingDeleteMain = main;

        var nameEl = $('#deleteMainName');
        var countEl = $('#deleteMainSubsCount');
        var warn = $('#deleteMainWarning');

        if (nameEl) nameEl.textContent = '"' + main.name + '"';
        var subCount = main.subs.length;
        if (countEl) countEl.textContent = subCount;

        // Hide warning box if no subs
        if (warn) warn.style.display = subCount === 0 ? 'none' : 'flex';

        openModal('deleteMainModal');
    }


    // ============================================================
    // MAIN — SUBMIT DELETE
    // ============================================================
    function submitDeleteMain() {
        if (!state.pendingDeleteMain) return;

        var main = state.pendingDeleteMain;
        var btn = $('#confirmDeleteMainBtn');
        var originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting…';

        postForm(API.mainDelete, { id: main.id })
            .then(function (res) {
                if (!res.success) {
                    showToast(res.message || 'Failed to delete.', 'error');
                    return;
                }
                showToast(res.message || 'Deleted.', 'success');
                closeModal('deleteMainModal');

                // Remove from state
                state.mains = state.mains.filter(function (m) { return String(m.id) !== String(main.id); });

                // If the deleted main was selected, clear selection
                if (String(state.selectedMainId) === String(main.id)) {
                    state.selectedMainId = state.mains.length ? state.mains[0].id : null;
                }

                state.pendingDeleteMain = null;
                renderAll();
            })
            .catch(function (err) {
                showToast('Network error: ' + err.message, 'error');
            })
            .finally(function () {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            });
    }


    // ============================================================
    // SUB — OPEN ADD MODAL
    // ============================================================
    function openAddSub() {
        var main = state.selectedMainId ? findMainById(state.selectedMainId) : null;
        if (!main) {
            showToast('Select a main type first.', 'warning');
            return;
        }

        $('#subFormId').value = '';
        $('#subFormMainId').value = main.id;
        $('#subFormParentName').textContent = main.name;
        $('#subFormName').value = '';
        $('#subFormOrder').value = '0';
        $('#subFormActive').checked = true;
        $('#subFormActiveLabel').textContent = 'Active';

        $('#subModalTitleText').textContent = 'Add Sub Error Type';
        $('#subFormSubmitText').textContent = 'Save Sub Type';

        openModal('subModal');
        setTimeout(function () { $('#subFormName').focus(); }, 200);
    }


    // ============================================================
    // SUB — OPEN EDIT MODAL
    // ============================================================
    function openEditSub(btn) {
        var id = btn.getAttribute('data-id');
        var mainId = btn.getAttribute('data-main-id');
        var main = findMainById(mainId);
        var sub = findSubById(mainId, id);
        if (!main || !sub) return;

        $('#subFormId').value = sub.id;
        $('#subFormMainId').value = main.id;
        $('#subFormParentName').textContent = main.name;
        $('#subFormName').value = sub.name;
        $('#subFormOrder').value = sub.display_order;
        $('#subFormActive').checked = !!sub.is_active;
        $('#subFormActiveLabel').textContent = sub.is_active ? 'Active' : 'Inactive';

        $('#subModalTitleText').textContent = 'Edit Sub Error Type';
        $('#subFormSubmitText').textContent = 'Update Sub Type';

        openModal('subModal');
        setTimeout(function () { $('#subFormName').focus(); }, 200);
    }


    // ============================================================
    // SUB — SUBMIT FORM (ADD or EDIT)
    // ============================================================
    function submitSubForm(e) {
        if (e) e.preventDefault();

        var id = $('#subFormId').value;
        var mainId = $('#subFormMainId').value;
        var name = $('#subFormName').value.trim();
        var order = toInt($('#subFormOrder').value, 0);
        var isActive = $('#subFormActive').checked;

        if (!mainId) {
            showToast('Missing parent main type.', 'error');
            return;
        }
        if (!name) {
            showToast('Please enter a name.', 'error');
            $('#subFormName').focus();
            return;
        }

        var submitBtn = $('#subFormSubmit');
        var originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving…';

        var isEdit = !!id;
        var url = isEdit ? API.subEdit : API.subAdd;
        var payload = {
            main_id: mainId,
            name: name,
            display_order: order,
            is_active: isActive ? 'true' : 'false'
        };
        if (isEdit) payload.id = id;

        postForm(url, payload)
            .then(function (res) {
                if (!res.success) {
                    showToast(res.message || 'Failed to save.', 'error');
                    return;
                }
                showToast(res.message || 'Saved.', 'success');
                closeModal('subModal');
                return refreshSubsForSelectedMain();
            })
            .catch(function (err) {
                showToast('Network error: ' + err.message, 'error');
            })
            .finally(function () {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            });
    }


    // ============================================================
    // SUB — TOGGLE ACTIVE
    // ============================================================
    function toggleSubActive(btn) {
        var id = btn.getAttribute('data-id');
        var mainId = btn.getAttribute('data-main-id');
        var sub = findSubById(mainId, id);
        if (!sub) return;

        btn.disabled = true;

        postForm(API.subToggle, { id: sub.id })
            .then(function (res) {
                if (!res.success) {
                    showToast(res.message || 'Failed to toggle.', 'error');
                    return;
                }
                sub.is_active = !!res.is_active;
                renderAll();
                showToast(res.message, res.is_active ? 'success' : 'info');
            })
            .catch(function (err) {
                showToast('Network error: ' + err.message, 'error');
            })
            .finally(function () {
                btn.disabled = false;
            });
    }


    // ============================================================
    // SUB — OPEN DELETE CONFIRM
    // ============================================================
    function openDeleteSub(btn) {
        var id = btn.getAttribute('data-id');
        var mainId = btn.getAttribute('data-main-id');
        var sub = findSubById(mainId, id);
        if (!sub) return;

        state.pendingDeleteSub = sub;

        var nameEl = $('#deleteSubName');
        if (nameEl) nameEl.textContent = '"' + sub.name + '"';

        openModal('deleteSubModal');
    }


    // ============================================================
    // SUB — SUBMIT DELETE
    // ============================================================
    function submitDeleteSub() {
        if (!state.pendingDeleteSub) return;

        var sub = state.pendingDeleteSub;
        var btn = $('#confirmDeleteSubBtn');
        var originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting…';

        postForm(API.subDelete, { id: sub.id })
            .then(function (res) {
                if (!res.success) {
                    showToast(res.message || 'Failed to delete.', 'error');
                    return;
                }
                showToast(res.message || 'Deleted.', 'success');
                closeModal('deleteSubModal');
                state.pendingDeleteSub = null;
                return refreshSubsForSelectedMain();
            })
            .catch(function (err) {
                showToast('Network error: ' + err.message, 'error');
            })
            .finally(function () {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            });
    }


    // ============================================================
    // REFRESH HELPERS
    // ============================================================
    // Re-fetch subs for the selected main, keeping server as source of truth
    function refreshSubsForSelectedMain() {
        if (!state.selectedMainId) {
            renderAll();
            return Promise.resolve();
        }
        return fetch(API.subsForMain + state.selectedMainId + '/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) return;
            var main = findMainById(state.selectedMainId);
            if (main) {
                main.subs = data.subs || [];
            }
            renderAll();
        })
        .catch(function (err) {
            console.warn('refresh subs failed:', err);
            renderAll();
        });
    }

    // After adding a new main, re-fetch the mains list from the page (reload)
    // Simplest robust way: reload page data. But that's heavy.
    // Instead: we already inserted the main via the API response, so just
    // push to state and optionally auto-select it.
    function refreshMainListThenMaybeSelect(newMain) {
        if (newMain && newMain.id) {
            // If this main is not already in state (add flow), push it
            var exists = findMainById(newMain.id);
            if (!exists) {
                state.mains.push({
                    id: newMain.id,
                    name: newMain.name,
                    display_order: newMain.display_order,
                    is_active: newMain.is_active,
                    subs: []
                });
            } else {
                // Edit flow — merge changes
                exists.name = newMain.name;
                exists.display_order = newMain.display_order;
                exists.is_active = newMain.is_active;
            }
            // Sort
            state.mains.sort(function (a, b) {
                if (a.display_order !== b.display_order) return a.display_order - b.display_order;
                return a.name.localeCompare(b.name);
            });

            // Auto-select new main on add
            state.selectedMainId = newMain.id;
            state.subSearchTerm = '';
            var subSearchInput = $('#subSearchInput');
            if (subSearchInput) subSearchInput.value = '';
        }

        renderAll();
    }


    // ============================================================
    // CLICK DELEGATION
    // ============================================================
    function handleClick(e) {
        // Close-modal triggers (backdrop, close button, cancel)
        var closeTarget = e.target.closest('[data-close-modal]');
        if (closeTarget) {
            e.preventDefault();
            var id = closeTarget.getAttribute('data-close-modal');
            if (id) closeModal(id);
            return;
        }

        // data-action triggers
        var actionTarget = e.target.closest('[data-action]');
        if (actionTarget) {
            e.preventDefault();
            var action = actionTarget.getAttribute('data-action');

            switch (action) {
                case 'open-add-main':
                    openAddMain();
                    return;
                case 'open-add-sub':
                    openAddSub();
                    return;
                case 'edit-main':
                    openEditMain(actionTarget);
                    return;
                case 'delete-main':
                    openDeleteMain(actionTarget);
                    return;
                case 'toggle-main':
                    toggleMainActive(actionTarget);
                    return;
                case 'edit-sub':
                    openEditSub(actionTarget);
                    return;
                case 'delete-sub':
                    openDeleteSub(actionTarget);
                    return;
                case 'toggle-sub':
                    toggleSubActive(actionTarget);
                    return;
            }
        }

        // Main row click — select the main
        // (but NOT when clicking an action button inside)
        var mainRow = e.target.closest('.etm-main-item');
        if (mainRow) {
            // Ignore if the click was on an action button
            if (e.target.closest('.etm-main-actions')) return;
            var mainId = mainRow.getAttribute('data-main-id');
            if (mainId && String(mainId) !== String(state.selectedMainId)) {
                selectMain(mainId);
            }
        }
    }


    // ============================================================
    // SEARCH
    // ============================================================
    function handleMainSearch(e) {
        state.mainSearchTerm = e.target.value || '';
        renderMains();
    }

    function handleSubSearch(e) {
        state.subSearchTerm = e.target.value || '';
        renderSubs();
    }


    // ============================================================
    // TOGGLE SWITCH LABEL UPDATE
    // ============================================================
    function bindToggleLabel(checkboxId, labelId) {
        var cb = document.getElementById(checkboxId);
        var lbl = document.getElementById(labelId);
        if (!cb || !lbl) return;
        cb.addEventListener('change', function () {
            lbl.textContent = this.checked ? 'Active' : 'Inactive';
        });
    }


    // ============================================================
    // BOOT
    // ============================================================
    function boot() {
        // Load bootstrap data
        var dataEl = document.getElementById('etmBootstrapData');
        if (dataEl) {
            try {
                var parsed = JSON.parse(dataEl.textContent || '[]');
                state.mains = Array.isArray(parsed) ? parsed : [];
            } catch (err) {
                console.error('Failed to parse bootstrap data', err);
                state.mains = [];
            }
        }

        // Auto-select first main (if any)
        if (state.mains.length > 0) {
            state.selectedMainId = state.mains[0].id;
        }

        // Initial render
        renderAll();

        // Wire up all events
        document.addEventListener('click', handleClick);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeAllModals();
        });

        // Search
        var mainSearch = $('#mainSearchInput');
        if (mainSearch) mainSearch.addEventListener('input', handleMainSearch);

        var subSearch = $('#subSearchInput');
        if (subSearch) subSearch.addEventListener('input', handleSubSearch);

        // Form submission
        var mainForm = $('#mainForm');
        if (mainForm) mainForm.addEventListener('submit', submitMainForm);

        var subForm = $('#subForm');
        if (subForm) subForm.addEventListener('submit', submitSubForm);

        // Delete confirm buttons
        var delMainBtn = $('#confirmDeleteMainBtn');
        if (delMainBtn) delMainBtn.addEventListener('click', submitDeleteMain);

        var delSubBtn = $('#confirmDeleteSubBtn');
        if (delSubBtn) delSubBtn.addEventListener('click', submitDeleteSub);

        // Toggle labels (live update while typing)
        bindToggleLabel('mainFormActive', 'mainFormActiveLabel');
        bindToggleLabel('subFormActive', 'subFormActiveLabel');
    }


    // ============================================================
    // ENTRY POINT
    // ============================================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

})();