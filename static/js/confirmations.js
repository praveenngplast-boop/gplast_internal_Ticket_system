// ============================================
// CONFIRMATION INTERCEPTOR - COMPLETE REWRITE
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    let currentFormToSubmit = null;

    // Grab confirmation modal elements
    const modalEl = document.getElementById('confirmModal');
    if (!modalEl) {
        console.warn('Confirm modal not found in DOM');
        return;
    }

    const confirmModalBody = document.getElementById('confirmModalBody');
    const confirmModalYesBtn = document.getElementById('confirmModalYesBtn');

    if (!confirmModalBody || !confirmModalYesBtn) {
        console.warn('Confirmation modal elements are incomplete.');
        return;
    }

    // ============================================
    // FIX: Use Bootstrap 5 Modal correctly
    // ============================================
    let bsConfirmModal = null;
    
    // Wait for Bootstrap to be available
    function initModal() {
        if (window.bootstrap && window.bootstrap.Modal) {
            bsConfirmModal = new bootstrap.Modal(modalEl, {
                backdrop: 'static',
                keyboard: true
            });
            console.log('Bootstrap modal initialized');
            return true;
        }
        return false;
    }

    // Try to initialize immediately, if not, wait
    if (!initModal()) {
        // Check again after a short delay
        setTimeout(function() {
            initModal();
        }, 500);
    }

    // ============================================
    // FIX: Intercept Form Submissions
    // ============================================
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        // If it's already confirmed, let it submit
        if (form.classList.contains('confirmed')) {
            setTimeout(() => {
                form.classList.remove('confirmed');
            }, 100);
            return;
        }

        let confirmMsg = "";

        // Check by form ID
        if (form.id === 'holdForm') {
            confirmMsg = "Move this ticket to Hold?";
        } else if (form.id === 'escalateForm') {
            confirmMsg = "Are you sure you want to escalate this ticket to the ERP vendor?";
        } else if (form.id === 'reopenForm') {
            confirmMsg = "Are you sure you want to reopen this ticket?";
        } else if (form.id === 'addUnitForm') {
            confirmMsg = "Are you sure you want to add this unit?";
        } else if (form.id === 'editUnitForm') {
            confirmMsg = "Are you sure you want to save changes to this unit?";
        } else if (form.id === 'addDeptForm') {
            confirmMsg = "Are you sure you want to add this department?";
        } else if (form.id === 'editDeptForm') {
            confirmMsg = "Are you sure you want to save changes to this department?";
        } else if (form.id === 'contactForm') {
            confirmMsg = "Are you sure you want to save these settings?";
        } else if (form.id === 'addEmailForm') {
            confirmMsg = "Are you sure you want to add this email?";
        } else if (form.id === 'changePasswordForm') {
            confirmMsg = "Are you sure you want to update your password?";
        } else if (form.id === 'resetPasswordForm') {
            confirmMsg = "Are you sure you want to reset this user's password?";
        }

        // Generic data-confirm attribute
        if (form.hasAttribute('data-confirm')) {
            confirmMsg = form.getAttribute('data-confirm');
        }

        if (confirmMsg) {
            e.preventDefault();
            e.stopPropagation();
            
            currentFormToSubmit = form;
            confirmModalBody.textContent = confirmMsg;
            
            // Show modal - this will add the backdrop
            if (bsConfirmModal) {
                bsConfirmModal.show();
            } else {
                // Fallback: try re-initializing
                if (initModal()) {
                    bsConfirmModal.show();
                } else {
                    // Ultra fallback - use jQuery if available
                    if (typeof $ !== 'undefined') {
                        $(modalEl).modal('show');
                    }
                }
            }
        }
    }, true);

    // ============================================
    // FIX: Handle Yes Button Click
    // ============================================
    confirmModalYesBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!currentFormToSubmit) return;

        const target = currentFormToSubmit;

        // Hide the modal first
        if (bsConfirmModal) {
            bsConfirmModal.hide();
        } else if (typeof $ !== 'undefined') {
            $(modalEl).modal('hide');
        }

        // Remove any stuck backdrops
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        document.body.classList.remove('modal-open');

        // Mark as confirmed and submit
        if (target.tagName === 'FORM') {
            target.classList.add('confirmed');
            setTimeout(function() {
                target.submit();
                currentFormToSubmit = null;
            }, 200);
        } else if (target.tagName === 'A') {
            setTimeout(function() {
                window.location.href = target.href;
                currentFormToSubmit = null;
            }, 200);
        }
    });

    // ============================================
    // FIX: Handle No Button Click
    // ============================================
    document.querySelectorAll('#confirmModal .btn-no, #confirmModal [data-bs-dismiss="modal"]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            currentFormToSubmit = null;
            if (bsConfirmModal) {
                bsConfirmModal.hide();
            } else if (typeof $ !== 'undefined') {
                $(modalEl).modal('hide');
            }
            
            // Remove any stuck backdrops
            document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                backdrop.remove();
            });
            document.body.classList.remove('modal-open');
        });
    });

    // ============================================
    // FIX: Handle modal close button (X)
    // ============================================
    const closeBtn = modalEl.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            currentFormToSubmit = null;
            if (bsConfirmModal) {
                bsConfirmModal.hide();
            } else if (typeof $ !== 'undefined') {
                $(modalEl).modal('hide');
            }
            
            document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                backdrop.remove();
            });
            document.body.classList.remove('modal-open');
        });
    }

    // ============================================
    // FIX: Handle inline anchor actions
    // ============================================
    document.addEventListener('click', function(e) {
        const anchor = e.target.closest('.confirm-link');
        if (anchor) {
            e.preventDefault();
            const href = anchor.getAttribute('href');
            if (href && href !== '#') {
                currentFormToSubmit = anchor;
                const msg = anchor.getAttribute('data-confirm') || "Are you sure you want to perform this action?";
                confirmModalBody.textContent = msg;
                if (bsConfirmModal) {
                    bsConfirmModal.show();
                }
            }
        }
    });

    // ============================================
    // FIX: Clean up when modal is hidden
    // ============================================
    modalEl.addEventListener('hidden.bs.modal', function() {
        currentFormToSubmit = null;
        document.querySelectorAll('form.confirmed').forEach(function(form) {
            form.classList.remove('confirmed');
        });
        // Remove any stuck backdrops
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        document.body.classList.remove('modal-open');
    });

    // ============================================
    // FIX: Handle Escape key
    // ============================================
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (modalEl.classList.contains('show')) {
                currentFormToSubmit = null;
                if (bsConfirmModal) {
                    bsConfirmModal.hide();
                }
                document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                    backdrop.remove();
                });
                document.body.classList.remove('modal-open');
            }
        }
    });

    // ============================================
    // FIX: Click outside modal - close it
    // ============================================
    modalEl.addEventListener('click', function(e) {
        if (e.target === modalEl) {
            currentFormToSubmit = null;
            if (bsConfirmModal) {
                bsConfirmModal.hide();
            }
            document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                backdrop.remove();
            });
            document.body.classList.remove('modal-open');
        }
    });

    console.log('Confirmation interceptor initialized successfully.');
});