/* ============================================================
   UNIT HEAD TICKET DETAIL JAVASCRIPT
   File: static/js/unit_head/ticket_detail.js
   ============================================================ */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        // ============================================================
        // PRIORITY CHANGE FORM — validation + confirmation
        // ============================================================
        var priorityForm = document.getElementById('priorityChangeForm');
        if (priorityForm) {
            priorityForm.addEventListener('submit', function (e) {
                var select = document.getElementById('new_priority');
                var reason = document.getElementById('priority_reason');

                // Validate priority selection
                if (!select || !select.value) {
                    e.preventDefault();
                    alert('Please select a priority level.');
                    if (select) select.focus();
                    return false;
                }

                // Validate reason
                if (!reason || !reason.value.trim()) {
                    e.preventDefault();
                    alert('Please provide a reason for changing the priority.');
                    if (reason) reason.focus();
                    return false;
                }

                // Confirmation
                if (!confirm('Change priority to "' + select.value + '"?')) {
                    e.preventDefault();
                    return false;
                }

                // Disable button to prevent double submission
                var btn = priorityForm.querySelector('button[type="submit"]');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Saving...';

                    // Re-enable after 8 seconds as a fallback
                    setTimeout(function () {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fa-solid fa-save" aria-hidden="true"></i> Save';
                    }, 8000);
                }
                return true;
            });
        }

        // ============================================================
        // TARGET DATE FORM — validation
        // ============================================================
        var targetForm = document.getElementById('targetDateForm');
        if (targetForm) {
            targetForm.addEventListener('submit', function (e) {
                var input = document.getElementById('targetDate');

                if (!input || !input.value) {
                    e.preventDefault();
                    alert('Please select a target date.');
                    if (input) input.focus();
                    return false;
                }

                var picked = new Date(input.value);
                var today = new Date();
                today.setHours(0, 0, 0, 0);

                if (picked < today) {
                    e.preventDefault();
                    alert('Target date cannot be in the past.');
                    input.focus();
                    return false;
                }

                // Disable button to prevent double submission
                var btn = targetForm.querySelector('button[type="submit"]');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Updating...';

                    setTimeout(function () {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fa-regular fa-calendar-check" aria-hidden="true"></i> Update';
                    }, 8000);
                }
                return true;
            });
        }

    });
})();