// ============================================================
// CHANGE PASSWORD — live validation
// GPLAST policy: 4–14 characters, new ≠ current
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const form = document.getElementById('pcForm');
    if (!form) return;

    const oldPw  = document.getElementById('id_old_password');
    const newPw  = document.getElementById('id_new_password1');
    const confPw = document.getElementById('id_new_password2');

    const counter   = document.getElementById('pcCounter');
    const countEl   = document.getElementById('pcCount');
    const matchEl   = document.getElementById('pcMatch');
    const ruleLen   = document.getElementById('rule-length');
    const ruleDiff  = document.getElementById('rule-different');
    const submitBtn = document.getElementById('pcSubmit');

    const MIN = 4;
    const MAX = 14;

    /* ------------------------------------------------------------
       Show / hide password toggles
       ------------------------------------------------------------ */
    document.querySelectorAll('.pcx-toggle').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('data-target');
            const target = document.getElementById(targetId);
            if (!target) return;

            const isPwd = target.type === 'password';
            target.type = isPwd ? 'text' : 'password';

            this.innerHTML = isPwd
                ? '<i class="fa-regular fa-eye-slash"></i>'
                : '<i class="fa-regular fa-eye"></i>';
        });
    });

    /* ------------------------------------------------------------
       Set the visual state of a rule row
       ------------------------------------------------------------ */
    function setRule(el, ok) {
        if (!el) return;

        el.classList.toggle('rule-ok', ok === true);
        el.classList.toggle('rule-fail', ok === false);

        const icon = el.querySelector('i');
        if (!icon) return;

        if (ok === true) {
            icon.className = 'fa-solid fa-circle-check';
        } else if (ok === false) {
            icon.className = 'fa-solid fa-circle-xmark';
        } else {
            icon.className = 'fa-regular fa-circle';
        }
    }

    /* ------------------------------------------------------------
       Main validation routine
       ------------------------------------------------------------ */
    function validate() {
        const oldVal  = oldPw ? oldPw.value : '';
        const newVal  = newPw ? newPw.value : '';
        const confVal = confPw ? confPw.value : '';

        // --- Length counter ---
        const len = newVal.length;
        if (countEl) countEl.textContent = len;
        if (counter) {
            counter.classList.remove('valid', 'invalid');
            if (len === 0) {
                // neutral
            } else if (len < MIN || len > MAX) {
                counter.classList.add('invalid');
            } else {
                counter.classList.add('valid');
            }
        }

        // --- Rule: length 4–14 ---
        const lengthOk = len >= MIN && len <= MAX;
        setRule(ruleLen, newVal.length ? lengthOk : null);

        // --- Rule: new ≠ old ---
        let differentOk = null;
        if (newVal.length > 0 && oldVal.length > 0) {
            differentOk = newVal !== oldVal;
        }
        setRule(ruleDiff, differentOk);

        // --- Match indicator ---
        if (matchEl) {
            if (confVal.length === 0) {
                matchEl.textContent = '';
                matchEl.className = 'pcx-match';
            } else if (newVal === confVal) {
                matchEl.innerHTML = '<i class="fa-solid fa-circle-check"></i> Passwords match';
                matchEl.className = 'pcx-match match';
            } else {
                matchEl.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> Passwords do not match';
                matchEl.className = 'pcx-match mismatch';
            }
        }

        // --- Submit availability ---
        const allOk =
            oldVal.length > 0 &&
            lengthOk &&
            newVal !== oldVal &&
            newVal === confVal;

        if (submitBtn) {
            submitBtn.disabled = !allOk;
        }

        return allOk;
    }

    /* ------------------------------------------------------------
       Wire up input events
       ------------------------------------------------------------ */
    [oldPw, newPw, confPw].forEach(function (el) {
        if (!el) return;
        el.addEventListener('input', validate);
        el.addEventListener('blur', validate);
    });

    /* ------------------------------------------------------------
       Submit guard
       ------------------------------------------------------------ */
    form.addEventListener('submit', function (e) {
        if (!validate()) {
            e.preventDefault();

            if (oldPw && oldPw.value.length === 0) {
                oldPw.focus();
                return;
            }
            if (newPw && (newPw.value.length < MIN || newPw.value.length > MAX)) {
                newPw.focus();
                return;
            }
            if (newPw && oldPw && newPw.value === oldPw.value) {
                newPw.focus();
                return;
            }
            if (confPw && newPw && confPw.value !== newPw.value) {
                confPw.focus();
            }
        }
    });

    /* ------------------------------------------------------------
       Auto-focus + initial run
       ------------------------------------------------------------ */
    if (oldPw) {
        setTimeout(function () { oldPw.focus(); }, 100);
    }

    validate();
});