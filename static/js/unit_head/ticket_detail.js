/* ============================================================
   UNIT HEAD TICKET DETAIL JAVASCRIPT
   ============================================================ */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {

        // ============================================================
        // THEME SYNC FOR FORM CONTROLS
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

        // ============================================================
        // PRIORITY CHANGE FORM - VALIDATION & CONFIRMATION
        // ============================================================
        var priorityForm = document.getElementById('priorityChangeForm');
        var changeBtn = document.getElementById('changePriorityBtn');

        if (priorityForm && changeBtn) {
            priorityForm.addEventListener('submit', function(e) {
                var prioritySelect = document.getElementById('new_priority');
                var reasonText = document.getElementById('priority_reason');

                // Validate selection
                if (!prioritySelect || !prioritySelect.value) {
                    e.preventDefault();
                    showToast('Please select a priority level.', 'warning');
                    prioritySelect.focus();
                    return false;
                }

                // Validate reason
                if (!reasonText || !reasonText.value.trim()) {
                    e.preventDefault();
                    showToast('Please provide a reason for changing the priority.', 'warning');
                    reasonText.focus();
                    return false;
                }

                // Show confirmation dialog
                var currentPriority = '{{ ticket.priority }}';
                var newPriority = prioritySelect.value;

                if (currentPriority === newPriority) {
                    e.preventDefault();
                    showToast('The selected priority is the same as the current priority.', 'info');
                    return false;
                }

                var confirmMsg = 'Are you sure you want to change the priority from "' + 
                                currentPriority + '" to "' + newPriority + '"?';
                
                if (!confirm(confirmMsg)) {
                    e.preventDefault();
                    return false;
                }

                // Disable button to prevent double submission
                changeBtn.disabled = true;
                changeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating...';

                // Re-enable after 5 seconds if form doesn't submit (fallback)
                setTimeout(function() {
                    changeBtn.disabled = false;
                    changeBtn.innerHTML = '<i class="fa-solid fa-save"></i> Change Priority';
                }, 5000);

                return true;
            });
        }

        // ============================================================
        // TOAST NOTIFICATION HELPER
        // ============================================================
        function showToast(message, type) {
            // Check if Bootstrap Toast is available
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                // Try to find an existing toast container
                var toastContainer = document.querySelector('.toast-container');
                if (!toastContainer) {
                    toastContainer = document.createElement('div');
                    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                    toastContainer.style.zIndex = '9999';
                    document.body.appendChild(toastContainer);
                }

                var toastId = 'toast-' + Date.now();
                var bgClass = type === 'warning' ? 'bg-warning' : 
                              type === 'error' ? 'bg-danger' : 
                              type === 'success' ? 'bg-success' : 'bg-info';
                
                var toastHtml = `
                    <div id="${toastId}" class="toast align-items-center text-white border-0 ${bgClass}" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="d-flex">
                            <div class="toast-body">
                                <i class="fa-solid fa-${type === 'warning' ? 'triangle-exclamation' : type === 'error' ? 'circle-xmark' : type === 'success' ? 'circle-check' : 'circle-info'} me-2"></i>
                                ${message}
                            </div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                    </div>
                `;

                toastContainer.insertAdjacentHTML('beforeend', toastHtml);

                var toastElement = document.getElementById(toastId);
                var toast = new bootstrap.Toast(toastElement, {
                    delay: 4000,
                    autohide: true
                });
                toast.show();

                // Remove from DOM after hidden
                toastElement.addEventListener('hidden.bs.toast', function() {
                    toastElement.remove();
                });
            } else {
                // Fallback: console log + alert
                console.log('[' + (type || 'info') + '] ' + message);
                if (type === 'error' || type === 'warning') {
                    alert(message);
                }
            }
        }

        // ============================================================
        // AUTO-SELECT CURRENT PRIORITY (Optional)
        // ============================================================
        var prioritySelect = document.getElementById('new_priority');
        if (prioritySelect) {
            // Get current priority from the badge in the header
            var currentPriorityElement = document.querySelector('.badge-priority');
            if (currentPriorityElement) {
                var currentPriority = currentPriorityElement.textContent.trim();
                // Optionally, you can auto-select the current priority
                // so the user knows what it currently is
                // for (var i = 0; i < prioritySelect.options.length; i++) {
                //     if (prioritySelect.options[i].value === currentPriority) {
                //         prioritySelect.options[i].selected = true;
                //     }
                // }
            }
        }

        // ============================================================
        // KEYBOARD SHORTCUTS
        // ============================================================
        document.addEventListener('keydown', function(e) {
            // Ctrl + B - Go Back
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                var backBtn = document.querySelector('.btn-back');
                if (backBtn) {
                    window.location.href = backBtn.href;
                }
            }

            // Ctrl + D - Download
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                var downloadBtn = document.querySelector('.btn-download');
                if (downloadBtn) {
                    window.location.href = downloadBtn.href;
                }
            }
        });

        // ============================================================
        // LOGGING
        // ============================================================
        console.log('✅ Unit Head Ticket Detail loaded');
        console.log('📋 Ticket #' + '{{ ticket.ticket_number }}' + ' - Status: {{ ticket.status }}');

    });

})();