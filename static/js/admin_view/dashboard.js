/* ============================================================
   Dashboard — clickable recent-ticket rows
   File: js/admin_view/dashboard.js

   Makes each <tr data-href="..."> in the Recent Tickets table
   navigate to its ticket detail page when clicked. Also supports
   keyboard activation (Enter / Space) for accessibility.
   ============================================================ */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        var rows = document.querySelectorAll('tr[data-href]');

        rows.forEach(function (row) {

            function navigate() {
                var href = row.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            }

            // Make the row look and behave like a link
            row.style.cursor = 'pointer';
            row.setAttribute('tabindex', '0');
            row.setAttribute('role', 'link');

            // Mouse click
            row.addEventListener('click', navigate);

            // Keyboard: Enter or Space
            row.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    navigate();
                }
            });
        });
    });
})();