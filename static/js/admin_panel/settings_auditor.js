// ============================================================
// SETTINGS · AUDITOR CREDENTIALS
// Page-level behaviour: form toggle, confirmations
// ============================================================

(function () {
    'use strict';

    // --------------------------------------------------------
    // 1. Toggle the Add Auditor form
    // --------------------------------------------------------
    function initToggleButtons() {
        var buttons = document.querySelectorAll('[data-toggle-section]');

        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var targetId = btn.getAttribute('data-toggle-section');
                var target = document.getElementById(targetId);
                if (!target) return;

                var isHidden =
                    target.style.display === 'none' ||
                    target.style.display === '';

                target.style.display = isHidden ? 'block' : 'none';
                btn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');

                // Focus the first input when opening
                if (isHidden) {
                    var firstInput = target.querySelector('input');
                    if (firstInput) {
                        setTimeout(function () {
                            firstInput.focus();
                        }, 100);
                    }
                }
            });
        });
    }


    // --------------------------------------------------------
    // 2. Confirmation dialogs
    // --------------------------------------------------------
    function initConfirmations() {
        // Expose to global scope so inline onsubmit="" can call them
        window.confirmReset = function (username) {
            return confirm(
                'Reset the password for auditor "' + username + '"?\n\n' +
                'They will need the new password to sign in.'
            );
        };

        window.confirmDelete = function (username) {
            return confirm(
                'Remove auditor "' + username + '" from the Auditor group?\n\n' +
                'They will immediately lose oversight access.'
            );
        };
    }


    // --------------------------------------------------------
    // 3. Password strength hint (optional)
    // --------------------------------------------------------
    function initPasswordHints() {
        var inputs = document.querySelectorAll('input[type="password"][maxlength="14"]');

        inputs.forEach(function (input) {
            var hint = input.parentNode.querySelector('.cred-form-hint');
            if (!hint) return;

            var defaultText = hint.textContent;

            input.addEventListener('input', function () {
                var len = input.value.length;

                if (len === 0) {
                    hint.textContent = defaultText;
                    hint.style.color = '';
                } else if (len < 4) {
                    hint.textContent = 'Too short — ' + (4 - len) + ' more character' + (4 - len === 1 ? '' : 's') + ' needed.';
                    hint.style.color = '#EF4444';
                } else if (len > 14) {
                    hint.textContent = 'Too long — max is 14 characters.';
                    hint.style.color = '#EF4444';
                } else {
                    hint.textContent = '✓ ' + len + ' characters';
                    hint.style.color = '#22C55E';
                }
            });
        });
    }


    // --------------------------------------------------------
    // 4. Boot
    // --------------------------------------------------------
    function boot() {
        initToggleButtons();
        initConfirmations();
        initPasswordHints();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();