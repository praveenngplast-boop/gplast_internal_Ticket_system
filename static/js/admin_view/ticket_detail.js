/* ============================================================
   Ticket Detail — Oversight
   File: js/admin_view/ticket_detail.js
   ============================================================ */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        /* Confirm before priority auto-submit */
        document.querySelectorAll('.av-select--sm').forEach(function (select) {
            var original = select.value;
            select.addEventListener('change', function (e) {
                var label = select.options[select.selectedIndex].text;
                if (!window.confirm('Change priority to "' + label + '"?')) {
                    select.value = original;
                    e.stopImmediatePropagation();
                    e.preventDefault();
                    return false;
                }
            });
        });

        /* Disable comment submit button while posting */
        document.querySelectorAll('.av-comment-form').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                var ta = form.querySelector('.av-textarea');
                if (!ta || !ta.value.trim()) {
                    e.preventDefault();
                    if (ta) ta.focus();
                    return;
                }
                var btn = form.querySelector('button[type="submit"]');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML =
                        '<i class="fa-solid fa-spinner fa-spin"></i> Posting…';
                }
            });
        });

        /* Auto-resize comment textarea */
        document.querySelectorAll('.av-comment-form .av-textarea').forEach(function (ta) {
            function autosize() {
                ta.style.height = 'auto';
                ta.style.height = Math.min(ta.scrollHeight, 260) + 'px';
            }
            ta.addEventListener('input', autosize);
            autosize();
        });

        /* Copy ticket ID on click */
        document.querySelectorAll('.av-ticket-id').forEach(function (el) {
            el.style.cursor = 'pointer';
            el.title = 'Click to copy ticket ID';
            el.addEventListener('click', function () {
                var text = el.textContent.replace('#', '').trim();
                if (navigator.clipboard) navigator.clipboard.writeText(text);
                el.animate(
                    [{ background: 'rgba(255,107,0,.15)' }, { background: '' }],
                    { duration: 400 }
                );
            });
        });
    });
})();