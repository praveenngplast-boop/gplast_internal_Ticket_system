/**
 * ============================================
 * CONFIRMATION INTERCEPTOR - COMPLETE SOLUTION
 * ============================================
 * 
 * This module intercepts form submissions and link clicks that have
 * a 'data-confirm' attribute and shows a confirmation modal before
 * proceeding with the action.
 * 
 * Usage:
 *   <form data-confirm="Are you sure?" action="/submit" method="POST">
 *   <a href="/delete/1" data-confirm="Delete this item?" class="confirm-link">
 * 
 * @version 1.1.0
 * @author GPLAST Team
 */

(function() {
    'use strict';

    // ============================================
    // STATE VARIABLES
    // ============================================
    let pendingForm = null;        // The form or link waiting for confirmation
    let isProcessing = false;      // Flag to prevent multiple confirmations
    let bsModal = null;            // Bootstrap modal instance
    let cleanupInterval = null;    // Interval for periodic cleanup

    // ============================================
    // DOM ELEMENTS
    // ============================================
    const modalEl = document.getElementById('confirmModal');
    
    // Exit early if modal element doesn't exist
    if (!modalEl) {
        console.warn('⚠️ Confirmation modal: Element #confirmModal not found in DOM.');
        return;
    }

    const confirmBody = document.getElementById('confirmModalBody');
    const confirmYes = document.getElementById('confirmModalYesBtn');

    if (!confirmBody || !confirmYes) {
        console.warn('⚠️ Confirmation modal: Required elements (body or yes button) not found.');
        return;
    }

    // ============================================
    // CORE FUNCTIONS
    // ============================================

    /**
     * Clean up modal state and remove any leftover backdrops
     */
    function cleanupModal() {
        // Remove all modal backdrops
        document.querySelectorAll('.modal-backdrop').forEach(function(el) {
            el.remove();
        });
        
        // Reset body styles
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        document.body.style.paddingLeft = '';
        
        // Reset modal state
        if (modalEl) {
            modalEl.style.display = 'none';
            modalEl.classList.remove('show');
            modalEl.setAttribute('aria-hidden', 'true');
            modalEl.removeAttribute('aria-modal');
            modalEl.removeAttribute('style');
        }
        
        // Clear pending state
        if (pendingForm) {
            pendingForm.removeAttribute('data-submitting');
            pendingForm = null;
        }
        isProcessing = false;
    }

    /**
     * Initialize the Bootstrap modal
     * @returns {boolean} True if initialization was successful
     */
    function initModal() {
        if (window.bootstrap && window.bootstrap.Modal) {
            // Dispose existing modal instance if any
            if (bsModal) {
                try {
                    bsModal.dispose();
                } catch (e) {
                    // Ignore dispose errors
                }
                bsModal = null;
            }
            
            try {
                bsModal = new bootstrap.Modal(modalEl, {
                    backdrop: 'static',
                    keyboard: true,
                    focus: true
                });
                return true;
            } catch (e) {
                console.warn('⚠️ Failed to initialize Bootstrap modal:', e);
                return false;
            }
        }
        return false;
    }

    /**
     * Show the confirmation modal with a custom message
     * @param {string} message - The confirmation message to display
     * @returns {boolean} True if modal was shown successfully
     */
    function showConfirmation(message) {
        if (!confirmBody) return false;
        
        confirmBody.textContent = message || 'Are you sure you want to proceed?';
        
        // Clean up before showing
        cleanupModal();
        
        // Show modal
        if (bsModal) {
            try {
                bsModal.show();
                return true;
            } catch (e) {
                console.warn('⚠️ Failed to show modal:', e);
                return false;
            }
        } else if (initModal()) {
            try {
                bsModal.show();
                return true;
            } catch (e) {
                console.warn('⚠️ Failed to show modal after init:', e);
                return false;
            }
        }
        return false;
    }

    /**
     * Handle the "Yes" confirmation action
     */
    function handleConfirmYes(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        if (isProcessing || !pendingForm) {
            return;
        }
        
        isProcessing = true;
        const form = pendingForm;
        pendingForm = null;
        
        // Hide modal
        if (bsModal) {
            try {
                bsModal.hide();
            } catch (e) {
                // Ignore
            }
        }
        
        // Clean up after modal hides
        setTimeout(function() {
            cleanupModal();
        }, 50);
        
        // Submit the form or navigate to link
        setTimeout(function() {
            if (form) {
                if (form.tagName === 'FORM') {
                    // It's a form - submit it
                    form.classList.add('confirmed');
                    try {
                        form.submit();
                    } catch (e) {
                        console.warn('⚠️ Form submission error:', e);
                    }
                } else if (form.tagName === 'A' && form.href) {
                    // It's a link - navigate to it
                    window.location.href = form.href;
                }
            }
            isProcessing = false;
            cleanupModal();
        }, 150);
    }

    /**
     * Handle the "Cancel" or "Close" action
     */
    function handleCancel(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Clear pending state
        if (pendingForm) {
            pendingForm.removeAttribute('data-submitting');
        }
        pendingForm = null;
        isProcessing = false;
        
        // Hide modal
        if (bsModal) {
            try {
                bsModal.hide();
            } catch (e) {
                console.warn('⚠️ Failed to hide modal on cancel:', e);
            }
        }
        
        setTimeout(cleanupModal, 50);
    }

    // ============================================
    // EVENT HANDLERS
    // ============================================

    /**
     * Intercept form submissions with data-confirm attribute
     */
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        // Skip if form has no-confirm class
        if (form.classList.contains('no-confirm')) {
            return;
        }

        // Prevent double submission
        if (form.getAttribute('data-submitting') === 'true') {
            e.preventDefault();
            return;
        }
        
        // Skip if already confirmed
        if (form.classList.contains('confirmed')) {
            setTimeout(function() {
                form.classList.remove('confirmed');
            }, 100);
            return;
        }
        
        // Check for confirm message
        const msg = form.getAttribute('data-confirm');
        if (msg) {
            e.preventDefault();
            e.stopPropagation();
            
            // Mark as submitting to prevent double submission
            form.setAttribute('data-submitting', 'true');
            pendingForm = form;
            
            // Show confirmation
            const shown = showConfirmation(msg);
            if (!shown) {
                // If modal fails, submit directly
                form.classList.add('confirmed');
                form.submit();
            }
        }
    });

    /**
     * Intercept link clicks with data-confirm attribute
     */
    document.addEventListener('click', function(e) {
        const anchor = e.target.closest('.confirm-link, [data-confirm]');
        if (!anchor) return;
        
        // Skip if it's a form submit button (handled by form interceptor)
        if (anchor.tagName === 'BUTTON' && anchor.form) return;
        
        const href = anchor.getAttribute('href');
        const msg = anchor.getAttribute('data-confirm');
        
        if (msg && href && href !== '#') {
            e.preventDefault();
            e.stopPropagation();
            
            pendingForm = anchor;
            
            const shown = showConfirmation(msg);
            if (!shown) {
                // If modal fails, navigate directly
                window.location.href = href;
            }
        }
    });

    // ============================================
    // MODAL EVENT BINDINGS
    // ============================================

    // Confirm Yes button
    confirmYes.addEventListener('click', handleConfirmYes);

    // Close buttons (data-bs-dismiss)
    modalEl.querySelectorAll('[data-bs-dismiss="modal"]').forEach(function(btn) {
        btn.addEventListener('click', handleCancel);
    });

    // Close button (btn-close)
    modalEl.querySelectorAll('.btn-close').forEach(function(btn) {
        btn.addEventListener('click', handleCancel);
    });

    // Cancel button
    modalEl.querySelectorAll('.btn-outline-grad, .btn-cancel, .btn-secondary, .btn-confirm-cancel, .btn-modal-close, .btn-no').forEach(function(btn) {
        btn.addEventListener('click', handleCancel);
    });

    // Modal hidden event
    modalEl.addEventListener('hidden.bs.modal', function() {
        if (pendingForm) {
            pendingForm.removeAttribute('data-submitting');
        }
        cleanupModal();
        pendingForm = null;
        isProcessing = false;
    });

    // Modal hide event - handle cleanup
    modalEl.addEventListener('hide.bs.modal', function() {
        if (pendingForm && pendingForm.getAttribute('data-submitting') === 'true') {
            setTimeout(function() {
                if (pendingForm) {
                    pendingForm.removeAttribute('data-submitting');
                }
            }, 100);
        }
    });

    // Click outside the modal (on backdrop)
    modalEl.addEventListener('click', function(e) {
        if (e.target === modalEl) {
            handleCancel(e);
        }
    });

    // ============================================
    // GLOBAL EVENT HANDLERS
    // ============================================

    // Escape key handler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalEl && modalEl.classList.contains('show')) {
            handleCancel(e);
        }
    });

    // ============================================
    // MUTATION OBSERVER FOR ROGUE BACKDROPS
    // ============================================
    if (window.MutationObserver) {
        const observer = new MutationObserver(function() {
            // Check for duplicate backdrops
            const backdrops = document.querySelectorAll('.modal-backdrop');
            if (backdrops.length > 1) {
                // Keep only the first one, remove the rest
                backdrops.forEach(function(backdrop, index) {
                    if (index > 0) {
                        backdrop.remove();
                    }
                });
            }
            
            // If modal is not shown but body has modal-open class, fix it
            if (modalEl && !modalEl.classList.contains('show') && document.body.classList.contains('modal-open')) {
                document.body.classList.remove('modal-open');
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
    }

    // ============================================
    // PERIODIC CLEANUP (Safety net)
    // ============================================
    cleanupInterval = setInterval(function() {
        // Check for stuck backdrops every 5 seconds
        const backdrops = document.querySelectorAll('.modal-backdrop');
        const modalShown = modalEl && modalEl.classList.contains('show');
        
        // If there are backdrops but modal is not shown, clean up
        if (backdrops.length > 0 && !modalShown) {
            cleanupModal();
        }
        
        // Remove duplicate backdrops
        if (backdrops.length > 1) {
            backdrops.forEach(function(backdrop, index) {
                if (index > 0) {
                    backdrop.remove();
                }
            });
        }
        
        // If modal is shown but body doesn't have modal-open class, add it
        if (modalShown && !document.body.classList.contains('modal-open')) {
            document.body.classList.add('modal-open');
        }
    }, 5000);

    // ============================================
    // HANDLE PAGE UNLOAD (Cleanup)
    // ============================================
    window.addEventListener('beforeunload', function() {
        if (cleanupInterval) {
            clearInterval(cleanupInterval);
            cleanupInterval = null;
        }
        cleanupModal();
    });

    // ============================================
    // INITIAL SETUP
    // ============================================

    // Initialize Bootstrap modal
    initModal();

    // Initial cleanup
    cleanupModal();

    // ============================================
    // EXPOSE PUBLIC API (Optional)
    // ============================================
    window.ConfirmModal = {
        /**
         * Show a confirmation dialog programmatically
         * @param {string} message - The confirmation message
         * @param {Function} onConfirm - Callback when user confirms
         * @param {Function} onCancel - Callback when user cancels
         */
        show: function(message, onConfirm, onCancel) {
            // Store the callbacks
            const confirmHandler = function(e) {
                confirmYes.removeEventListener('click', confirmHandler);
                if (typeof onConfirm === 'function') {
                    onConfirm();
                }
                handleConfirmYes(e);
            };
            
            const cancelHandler = function(e) {
                modalEl.querySelectorAll('[data-bs-dismiss="modal"], .btn-close, .btn-outline-grad, .btn-cancel, .btn-secondary, .btn-confirm-cancel, .btn-modal-close, .btn-no')
                    .forEach(function(btn) {
                        btn.removeEventListener('click', cancelHandler);
                    });
                confirmYes.removeEventListener('click', confirmHandler);
                if (typeof onCancel === 'function') {
                    onCancel();
                }
                handleCancel(e);
            };
            
            // Bind the handlers
            confirmYes.addEventListener('click', confirmHandler);
            modalEl.querySelectorAll('[data-bs-dismiss="modal"], .btn-close, .btn-outline-grad, .btn-cancel, .btn-secondary, .btn-confirm-cancel, .btn-modal-close, .btn-no')
                .forEach(function(btn) {
                    btn.addEventListener('click', cancelHandler);
                });
            
            // Show the modal
            return showConfirmation(message);
        },
        
        /**
         * Programmatically close the confirmation modal
         */
        close: function() {
            if (bsModal) {
                try {
                    bsModal.hide();
                } catch (e) {
                    // Ignore
                }
            }
            cleanupModal();
        },
        
        /**
         * Check if modal is currently shown
         */
        isShown: function() {
            return modalEl && modalEl.classList.contains('show');
        },
        
        /**
         * Get the current pending form/link
         */
        getPendingAction: function() {
            return pendingForm;
        }
    };

    console.log('✅ Confirmation modal interceptor initialized successfully.');

})();