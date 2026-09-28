/* ============================================================
   SETTINGS — ADMIN USERS  (settings_admin_users.js)
   Uses BUTTON CLICKS only. No form submits anywhere.
   Neutralizes the site-wide "Are you sure?" confirm dialog.
   ============================================================ */
console.log('=== AdminUsers JS v4 ===');

(function () {
    'use strict';

    // ============================================================
    // NEUTRALIZE BASE CONFIRMATION
    // shell.js defines window.showConfirmation() which opens the
    // orange #confirmModal from base.html. Nothing on this page
    // should trigger it, so we replace it with a pass-through.
    // ============================================================
    window.showConfirmation = function (message, onConfirm) {
        if (typeof onConfirm === 'function') onConfirm();
    };

    // ------------------------------------------------------------
    // CSRF
    // ------------------------------------------------------------
    function getCsrfToken() {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input && input.value) return input.value;
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    // ------------------------------------------------------------
    // Toast
    // ------------------------------------------------------------
    const TOAST_ICONS = {
        success: 'fa-circle-check',
        error:   'fa-circle-exclamation',
        info:    'fa-circle-info',
        warning: 'fa-triangle-exclamation',
    };

    function showToast(message, type = 'info', timeout = 3500) {
        const container = document.getElementById('toast-container');
        if (!container) { console.log(`[${type}] ${message}`); return; }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const icon = document.createElement('i');
        icon.className = `fa-solid ${TOAST_ICONS[type] || TOAST_ICONS.info}`;
        const text = document.createElement('span');
        text.textContent = message;
        toast.appendChild(icon);
        toast.appendChild(text);
        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('toast-hide');
            setTimeout(() => toast.remove(), 250);
        }, timeout);
    }

    // ------------------------------------------------------------
    // POST JSON
    // ------------------------------------------------------------
    async function postJSON(url, payload) {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(payload || {}),
            credentials: 'same-origin',
        });
        let data = {};
        try { data = await res.json(); } catch (e) {
            data = { success: false, error: `Server error (${res.status})` };
        }
        if (!res.ok && data.success === undefined) {
            data.success = false;
            data.error = data.error || `Server error (${res.status})`;
        }
        return data;
    }

    // ------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------
    function openModal(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.hidden = false;
        document.body.style.overflow = 'hidden';
    }

    function closeModal(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.hidden = true;
        document.body.style.overflow = '';
    }

    function closeAllModals() {
        document.querySelectorAll('.modal-overlay').forEach(el => { el.hidden = true; });
        document.body.style.overflow = '';
    }

    function setError(id, message) {
        const el = document.getElementById(id);
        if (!el) return;
        if (message) { el.textContent = message; el.hidden = false; }
        else { el.textContent = ''; el.hidden = true; }
    }

    function setLoading(btn, loading, label) {
        if (!btn) return;
        if (loading) {
            btn.dataset.originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${label || 'Working…'}`;
        } else {
            if (btn.dataset.originalHtml) {
                btn.innerHTML = btn.dataset.originalHtml;
                delete btn.dataset.originalHtml;
            }
            btn.disabled = false;
        }
    }

    function resetForm(id) {
        const form = document.getElementById(id);
        if (form) form.reset();
    }

    function val(id) {
        const el = document.getElementById(id);
        return el ? el.value : '';
    }

    function getRowById(id) {
        return document.querySelector(`tr.admin-row[data-id="${id}"]`);
    }

    function updateRowFromAdmin(row, admin) {
        if (!row || !admin) return;
        row.dataset.username  = admin.username;
        row.dataset.firstName = admin.first_name;
        row.dataset.lastName  = admin.last_name;
        row.dataset.email     = admin.email;
        row.dataset.isActive  = admin.is_active ? 'true' : 'false';

        const nameCell = row.querySelector('.col-name');
        if (nameCell) {
            nameCell.textContent = (admin.full_name && admin.full_name !== admin.username)
                ? admin.full_name : '—';
        }
        const emailCell = row.querySelector('.col-email');
        if (emailCell) emailCell.textContent = admin.email || '—';

        const statusCell = row.querySelector('.col-status');
        if (statusCell) {
            statusCell.innerHTML = admin.is_active
                ? '<span class="status-badge status-active"><i class="fa-solid fa-circle"></i> Active</span>'
                : '<span class="status-badge status-inactive"><i class="fa-solid fa-circle"></i> Inactive</span>';
        }
        row.classList.toggle('row-inactive', !admin.is_active);

        const tBtn = row.querySelector('.btn-toggle');
        if (tBtn) {
            const icon = tBtn.querySelector('i');
            if (icon) {
                icon.className = admin.is_active
                    ? 'fa-solid fa-toggle-on' : 'fa-solid fa-toggle-off';
            }
            tBtn.classList.toggle('btn-warn', admin.is_active);
            tBtn.classList.toggle('btn-ok', !admin.is_active);
            tBtn.title = admin.is_active ? 'Deactivate' : 'Activate';
        }
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // ------------------------------------------------------------
    // Block Enter inside modals from triggering form submit
    // ------------------------------------------------------------
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        const t = e.target;
        if (!t || !t.closest) return;
        if (!t.closest('.modal-overlay')) return;
        if (t.tagName === 'TEXTAREA') return;
        e.preventDefault();
        e.stopImmediatePropagation();
        return false;
    }, true);

    // ------------------------------------------------------------
    // Open Add modal
    // ------------------------------------------------------------
    const btnAdd = document.getElementById('btn-add-admin');
    if (btnAdd) {
        btnAdd.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            resetForm('form-add');
            setError('add-error', '');
            openModal('modal-add');
            setTimeout(() => {
                const el = document.getElementById('add-username');
                if (el) el.focus();
            }, 80);
        });
    }

    // ------------------------------------------------------------
    // Refresh button
    // ------------------------------------------------------------
    const btnRefresh = document.getElementById('btn-refresh');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', () => window.location.reload());
    }

    // ------------------------------------------------------------
    // Close / outside-click / ESC
    // ------------------------------------------------------------
    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            closeModal(btn.dataset.close);
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.hidden = true;
                document.body.style.overflow = '';
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAllModals();
    });

    // ------------------------------------------------------------
    // Password toggles
    // ------------------------------------------------------------
    document.querySelectorAll('.toggle-pw').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = document.getElementById(btn.dataset.target);
            if (!input) return;
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            const icon = btn.querySelector('i');
            if (icon) icon.className = show ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye';
        });
    });

    // ------------------------------------------------------------
    // Row actions
    // ------------------------------------------------------------
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.icon-btn');
        if (!btn) return;
        const id = btn.dataset.id;
        if (!id) return;
        const row = getRowById(id);
        if (!row) return;

        if (btn.classList.contains('btn-edit')) {
            document.getElementById('edit-id').value = id;
            document.getElementById('edit-username').value   = row.dataset.username || '';
            document.getElementById('edit-first-name').value = row.dataset.firstName || '';
            document.getElementById('edit-last-name').value  = row.dataset.lastName || '';
            document.getElementById('edit-email').value      = row.dataset.email || '';
            setError('edit-error', '');
            openModal('modal-edit');
            return;
        }
        if (btn.classList.contains('btn-reset-pw')) {
            document.getElementById('reset-id').value = id;
            document.getElementById('reset-username-label').textContent = row.dataset.username || '';
            resetForm('form-reset-pw');
            document.getElementById('reset-id').value = id;
            setError('reset-error', '');
            openModal('modal-reset-pw');
            return;
        }
        if (btn.classList.contains('btn-toggle')) {
            const isActive = row.dataset.isActive === 'true';
            const username = row.dataset.username || '';
            document.getElementById('toggle-title').innerHTML = isActive
                ? '<i class="fa-solid fa-toggle-on"></i> Deactivate Admin'
                : '<i class="fa-solid fa-toggle-off"></i> Activate Admin';
            document.getElementById('toggle-message').innerHTML = isActive
                ? `Deactivate <strong>${escapeHtml(username)}</strong>? They will no longer be able to log in.`
                : `Activate <strong>${escapeHtml(username)}</strong>? They will be able to log in again.`;
            document.getElementById('btn-toggle-confirm').dataset.id = id;
            openModal('modal-toggle');
            return;
        }
        if (btn.classList.contains('btn-delete')) {
            document.getElementById('delete-username-label').textContent = row.dataset.username || '';
            setError('delete-error', '');
            document.getElementById('btn-delete-confirm').dataset.id = id;
            openModal('modal-delete');
            return;
        }
    });

    // ============================================================
    // BUTTON HANDLERS — click only, no form submits
    // ============================================================

    // ----- ADD -----
    const btnAddSubmit = document.getElementById('btn-add-submit');
    if (btnAddSubmit) {
        btnAddSubmit.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            setError('add-error', '');

            const payload = {
                username:         val('add-username').trim(),
                first_name:       val('add-first-name').trim(),
                last_name:        val('add-last-name').trim(),
                email:            val('add-email').trim(),
                password:         val('add-password'),
                password_confirm: val('add-password-confirm'),
                is_active:        document.getElementById('add-is-active').checked,
            };

            if (!payload.username) { setError('add-error', 'Username is required.'); return; }
            if (!payload.password) { setError('add-error', 'Password is required.'); return; }
            if (payload.password !== payload.password_confirm) {
                setError('add-error', 'Passwords do not match.'); return;
            }

            setLoading(btnAddSubmit, true, 'Creating…');
            try {
                const data = await postJSON(window.ADMIN_USERS_URLS.add, payload);
                if (data.success) {
                    showToast(data.message || 'Admin created.', 'success');
                    closeModal('modal-add');
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    setError('add-error', data.error || 'Could not create admin.');
                }
            } catch (err) {
                setError('add-error', 'Network error. Please try again.');
            } finally {
                setLoading(btnAddSubmit, false);
            }
        });
    }

    // ----- EDIT -----
    const btnEditSubmit = document.getElementById('btn-edit-submit');
    if (btnEditSubmit) {
        btnEditSubmit.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            setError('edit-error', '');

            const id = val('edit-id');
            const payload = {
                id:         id,
                first_name: val('edit-first-name').trim(),
                last_name:  val('edit-last-name').trim(),
                email:      val('edit-email').trim(),
            };

            setLoading(btnEditSubmit, true, 'Saving…');
            try {
                const data = await postJSON(window.ADMIN_USERS_URLS.edit, payload);
                if (data.success) {
                    showToast(data.message || 'Admin updated.', 'success');
                    closeModal('modal-edit');
                    const row = getRowById(id);
                    if (row && data.admin) updateRowFromAdmin(row, data.admin);
                } else {
                    setError('edit-error', data.error || 'Could not update admin.');
                }
            } catch (err) {
                setError('edit-error', 'Network error. Please try again.');
            } finally {
                setLoading(btnEditSubmit, false);
            }
        });
    }

    // ----- RESET PASSWORD -----
    const btnResetSubmit = document.getElementById('btn-reset-submit');
    if (btnResetSubmit) {
        btnResetSubmit.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            setError('reset-error', '');

            const id = val('reset-id');
            const payload = {
                id:               id,
                password:         val('reset-password'),
                password_confirm: val('reset-password-confirm'),
            };

            if (!payload.password) { setError('reset-error', 'Password is required.'); return; }
            if (payload.password !== payload.password_confirm) {
                setError('reset-error', 'Passwords do not match.'); return;
            }
            if (payload.password.length < 4 || payload.password.length > 14) {
                setError('reset-error', 'Password must be 4–14 characters.'); return;
            }

            setLoading(btnResetSubmit, true, 'Resetting…');
            try {
                const data = await postJSON(window.ADMIN_USERS_URLS.resetPassword, payload);
                if (data.success) {
                    showToast(data.message || 'Password reset.', 'success');
                    closeModal('modal-reset-pw');
                    resetForm('form-reset-pw');
                } else {
                    setError('reset-error', data.error || 'Could not reset password.');
                }
            } catch (err) {
                setError('reset-error', 'Network error. Please try again.');
            } finally {
                setLoading(btnResetSubmit, false);
            }
        });
    }

    // ----- TOGGLE CONFIRM -----
    const btnToggleConfirm = document.getElementById('btn-toggle-confirm');
    if (btnToggleConfirm) {
        btnToggleConfirm.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const id = btnToggleConfirm.dataset.id;
            if (!id) return;

            setLoading(btnToggleConfirm, true, 'Updating…');
            try {
                const data = await postJSON(window.ADMIN_USERS_URLS.toggle, { id });
                if (data.success) {
                    showToast(data.message || 'Updated.', 'success');
                    closeModal('modal-toggle');
                    const row = getRowById(id);
                    if (row) {
                        row.dataset.isActive = data.is_active ? 'true' : 'false';
                        const statusCell = row.querySelector('.col-status');
                        if (statusCell) {
                            statusCell.innerHTML = data.is_active
                                ? '<span class="status-badge status-active"><i class="fa-solid fa-circle"></i> Active</span>'
                                : '<span class="status-badge status-inactive"><i class="fa-solid fa-circle"></i> Inactive</span>';
                        }
                        row.classList.toggle('row-inactive', !data.is_active);
                        const tBtn = row.querySelector('.btn-toggle');
                        if (tBtn) {
                            const icon = tBtn.querySelector('i');
                            if (icon) {
                                icon.className = data.is_active
                                    ? 'fa-solid fa-toggle-on' : 'fa-solid fa-toggle-off';
                            }
                            tBtn.classList.toggle('btn-warn', data.is_active);
                            tBtn.classList.toggle('btn-ok', !data.is_active);
                            tBtn.title = data.is_active ? 'Deactivate' : 'Activate';
                        }
                    }
                } else {
                    showToast(data.error || 'Could not toggle.', 'error');
                    closeModal('modal-toggle');
                }
            } catch (err) {
                showToast('Network error. Please try again.', 'error');
            } finally {
                setLoading(btnToggleConfirm, false);
            }
        });
    }

    // ----- DELETE CONFIRM -----
    const btnDeleteConfirm = document.getElementById('btn-delete-confirm');
    if (btnDeleteConfirm) {
        btnDeleteConfirm.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const id = btnDeleteConfirm.dataset.id;
            if (!id) return;

            setError('delete-error', '');
            setLoading(btnDeleteConfirm, true, 'Deleting…');
            try {
                const data = await postJSON(window.ADMIN_USERS_URLS.delete, { id });
                if (data.success) {
                    showToast(data.message || 'Admin deleted.', 'success');
                    closeModal('modal-delete');
                    const row = getRowById(id);
                    if (row) {
                        row.style.transition = 'opacity .3s ease';
                        row.style.opacity = '0';
                        setTimeout(() => row.remove(), 300);
                    }
                } else {
                    setError('delete-error', data.error || 'Could not delete admin.');
                }
            } catch (err) {
                setError('delete-error', 'Network error. Please try again.');
            } finally {
                setLoading(btnDeleteConfirm, false);
            }
        });
    }

    // ------------------------------------------------------------
    // Live search
    // ------------------------------------------------------------
    const searchInput = document.getElementById('admin-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const q = searchInput.value.trim().toLowerCase();
            const rows = document.querySelectorAll('#admin-tbody tr.admin-row');
            rows.forEach(row => {
                const hay = [row.dataset.username, row.dataset.firstName, row.dataset.lastName, row.dataset.email]
                    .filter(Boolean).join(' ').toLowerCase();
                row.style.display = (!q || hay.includes(q)) ? '' : 'none';
            });
            let n = 0;
            document.querySelectorAll('#admin-tbody tr.admin-row').forEach(r => {
                if (r.style.display !== 'none') {
                    n += 1;
                    const idx = r.querySelector('.col-index');
                    if (idx) idx.textContent = n;
                }
            });
        });
    }

})();