// ============================================
// CONFIRMATION INTERCEPTOR - BACKDROP FIX
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    let currentFormToSubmit = null;
    let isProcessing = false;

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
    // FIX 1: Force cleanup function (CRITICAL)
    // ============================================
    function forceCleanupBackdrops() {
        // Remove ALL modal backdrops
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        
        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
        
        // Remove any inline styles that might be causing blur
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Reset modal display
        if (modalEl) {
            modalEl.style.display = 'none';
            modalEl.classList.remove('show');
            modalEl.removeAttribute('aria-modal');
            modalEl.removeAttribute('style');
        }
        
        console.log('Backdrops cleaned up');
    }

    // ============================================
    // FIX 2: Proper Bootstrap Modal Initialization
    // ============================================
    let bsConfirmModal = null;
    
    function initModal() {
        if (window.bootstrap && window.bootstrap.Modal) {
            // If modal already exists, dispose it first
            if (bsConfirmModal) {
                try {
                    bsConfirmModal.dispose();
                } catch(e) {}
                bsConfirmModal = null;
            }
            
            bsConfirmModal = new bootstrap.Modal(modalEl, {
                backdrop: 'static',
                keyboard: true
            });
            
            console.log('Bootstrap modal initialized');
            return true;
        }
        return false;
    }

    // Try to initialize
    if (!initModal()) {
        const checkBootstrap = setInterval(function() {
            if (initModal()) {
                clearInterval(checkBootstrap);
            }
        }, 100);
        
        setTimeout(function() {
            clearInterval(checkBootstrap);
        }, 5000);
    }

    // ============================================
    // FIX 3: Handle Form Submissions
    // ============================================
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        if (form.classList.contains('confirmed')) {
            setTimeout(() => {
                form.classList.remove('confirmed');
            }, 100);
            return;
        }

        let confirmMsg = form.getAttribute('data-confirm');

        if (confirmMsg) {
            e.preventDefault();
            
            currentFormToSubmit = form;
            confirmModalBody.textContent = confirmMsg;
            
            // Force clean before showing
            forceCleanupBackdrops();
            
            if (bsConfirmModal) {
                bsConfirmModal.show();
            } else {
                if (initModal()) {
                    bsConfirmModal.show();
                } else if (typeof $ !== 'undefined') {
                    $(modalEl).modal('show');
                }
            }
        }
    });

    // ============================================
    // FIX 4: Handle Yes Button - WITH BACKDROP CLEANUP
    // ============================================
    confirmModalYesBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (isProcessing || !currentFormToSubmit) {
            return;
        }
        
        isProcessing = true;
        const target = currentFormToSubmit;
        currentFormToSubmit = null;

        // CRITICAL: Hide modal and clean up BEFORE submitting
        if (bsConfirmModal) {
            bsConfirmModal.hide();
        } else if (typeof $ !== 'undefined') {
            $(modalEl).modal('hide');
        }

        // IMMEDIATE cleanup - this removes the blur
        setTimeout(function() {
            forceCleanupBackdrops();
        }, 50);

        // Submit the form after cleanup
        setTimeout(function() {
            if (target && target.tagName === 'FORM') {
                target.classList.add('confirmed');
                
                // Use native submit
                const submitEvent = new Event('submit', {
                    bubbles: true,
                    cancelable: true
                });
                
                if (target.dispatchEvent(submitEvent)) {
                    target.submit();
                }
            } else if (target && target.tagName === 'A') {
                window.location.href = target.href;
            }
            
            isProcessing = false;
            forceCleanupBackdrops(); // One more time for safety
        }, 100);
    });

    // ============================================
    // FIX 5: Handle No Button
    // ============================================
    document.querySelectorAll('#confirmModal .btn-no, #confirmModal [data-bs-dismiss="modal"]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            currentFormToSubmit = null;
            isProcessing = false;
            
            if (bsConfirmModal) {
                bsConfirmModal.hide();
            } else if (typeof $ !== 'undefined') {
                $(modalEl).modal('hide');
            }
            
            // Clean up immediately
            setTimeout(forceCleanupBackdrops, 50);
        });
    });

    // ============================================
    // FIX 6: Handle Close Button
    // ============================================
    const closeBtn = modalEl.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            currentFormToSubmit = null;
            isProcessing = false;
            
            if (bsConfirmModal) {
                bsConfirmModal.hide();
            } else if (typeof $ !== 'undefined') {
                $(modalEl).modal('hide');
            }
            
            setTimeout(forceCleanupBackdrops, 50);
        });
    }

    // ============================================
    // FIX 7: Modal Hidden Event - Clean up
    // ============================================
    modalEl.addEventListener('hidden.bs.modal', function() {
        forceCleanupBackdrops();
        currentFormToSubmit = null;
        isProcessing = false;
        
        document.querySelectorAll('form.confirmed').forEach(function(form) {
            form.classList.remove('confirmed');
        });
    });

    // ============================================
    // FIX 8: Click Outside
    // ============================================
    modalEl.addEventListener('click', function(e) {
        if (e.target === modalEl) {
            currentFormToSubmit = null;
            isProcessing = false;
            
            if (bsConfirmModal) {
                bsConfirmModal.hide();
            } else if (typeof $ !== 'undefined') {
                $(modalEl).modal('hide');
            }
            
            setTimeout(forceCleanupBackdrops, 50);
        }
    });

    // ============================================
    // FIX 9: Handle Inline Links
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
                
                forceCleanupBackdrops();
                
                if (bsConfirmModal) {
                    bsConfirmModal.show();
                }
            }
        }
    });

    // ============================================
    // FIX 10: Mutation Observer for rogue backdrops
    // ============================================
    const observer = new MutationObserver(function() {
        // Check for any leftover backdrops and remove them
        const backdrops = document.querySelectorAll('.modal-backdrop');
        if (backdrops.length > 1) {
            backdrops.forEach(function(backdrop, index) {
                if (index > 0) {
                    backdrop.remove();
                }
            });
        }
        
        // If modal is not showing but body has modal-open class, fix it
        if (!modalEl.classList.contains('show') && document.body.classList.contains('modal-open')) {
            document.body.classList.remove('modal-open');
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class']
    });

    // ============================================
    // FIX 11: Handle Escape Key properly
    // ============================================
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // If modal is showing and we press Escape, clean up
            if (modalEl.classList.contains('show')) {
                currentFormToSubmit = null;
                isProcessing = false;
                
                setTimeout(forceCleanupBackdrops, 100);
            }
        }
    });

    console.log('Confirmation interceptor initialized with backdrop fix.');
});