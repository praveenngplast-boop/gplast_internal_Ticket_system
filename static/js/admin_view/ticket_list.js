/* ============================================================
   Tickets List — dropdowns + cascade + row nav
   File: js/admin_view/ticket_list.js
   ============================================================ */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        var form = document.getElementById('av-filter-form');
        if (!form) return;

        var dropdowns = Array.prototype.slice.call(
            form.querySelectorAll('.av-dd')
        );

        var ddUnit   = form.querySelector('.av-dd[data-dd="unit"]');
        var ddDept   = form.querySelector('.av-dd[data-dd="department"]');
        var ddAssign = form.querySelector('.av-dd[data-dd="assignee"]');

        /* 1. Open / close dropdowns */
        function closeAll(except) {
            dropdowns.forEach(function (dd) {
                if (dd !== except) {
                    dd.classList.remove('is-open');
                    var t = dd.querySelector('.av-dd-trigger');
                    if (t) t.setAttribute('aria-expanded', 'false');
                }
            });
        }

        dropdowns.forEach(function (dd) {
            var trigger = dd.querySelector('.av-dd-trigger');
            if (!trigger) return;

            trigger.setAttribute('type', 'button');
            trigger.setAttribute('aria-expanded', 'false');

            trigger.addEventListener('click', function (e) {
                e.stopPropagation();
                if (dd.classList.contains('is-locked') || trigger.disabled) return;

                var willOpen = !dd.classList.contains('is-open');
                closeAll(dd);
                dd.classList.toggle('is-open', willOpen);
                trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
            });

            var panel = dd.querySelector('.av-dd-panel');
            if (panel) {
                panel.addEventListener('click', function (e) { e.stopPropagation(); });
            }
        });

        document.addEventListener('click', function () { closeAll(null); });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeAll(null);
        });

        /* 2. Trigger label updates */
        function updateTrigger(dd) {
            var checked = dd.querySelectorAll('input[type="checkbox"]:checked');
            var valueEl = dd.querySelector('.av-dd-value');
            if (!valueEl || dd.classList.contains('is-locked')) return;

            if (checked.length === 0) {
                valueEl.textContent = 'Any';
                dd.classList.remove('has-selection');
            } else if (checked.length === 1) {
                var label = checked[0].closest('.av-dd-option').querySelector('span');
                valueEl.textContent = label ? label.textContent.trim() : '1 selected';
                dd.classList.add('has-selection');
            } else {
                valueEl.textContent = checked.length + ' selected';
                dd.classList.add('has-selection');
            }
        }

        /* 3. Cascade locks */
        function refreshLocks() {
            if (!ddUnit || !ddDept || !ddAssign) return;

            var unitsChecked = ddUnit.querySelectorAll('input[type="checkbox"]:checked').length > 0;
            var deptsChecked = ddDept.querySelectorAll('input[type="checkbox"]:checked').length > 0;

            /* Department */
            var deptTrigger = ddDept.querySelector('.av-dd-trigger');
            var deptValueEl = ddDept.querySelector('.av-dd-value');

            if (unitsChecked) {
                ddDept.classList.remove('is-locked');
                if (deptTrigger) { deptTrigger.disabled = false; deptTrigger.removeAttribute('aria-disabled'); }
                if (deptValueEl) updateTrigger(ddDept);
            } else {
                ddDept.classList.add('is-locked');
                ddDept.classList.remove('is-open');
                if (deptTrigger) { deptTrigger.disabled = true; deptTrigger.setAttribute('aria-disabled', 'true'); }
                if (deptValueEl) deptValueEl.textContent = 'Select a unit first';
                ddDept.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
                ddDept.classList.remove('has-selection');
            }

            /* Assigned */
            var asgTrigger = ddAssign.querySelector('.av-dd-trigger');
            var asgValueEl = ddAssign.querySelector('.av-dd-value');

            if (unitsChecked && deptsChecked) {
                ddAssign.classList.remove('is-locked');
                if (asgTrigger) { asgTrigger.disabled = false; asgTrigger.removeAttribute('aria-disabled'); }
                if (asgValueEl) updateTrigger(ddAssign);
            } else {
                ddAssign.classList.add('is-locked');
                ddAssign.classList.remove('is-open');
                if (asgTrigger) { asgTrigger.disabled = true; asgTrigger.setAttribute('aria-disabled', 'true'); }
                if (asgValueEl) {
                    asgValueEl.textContent = !unitsChecked
                        ? 'Select a unit first'
                        : 'Select a department first';
                }
                ddAssign.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
                ddAssign.classList.remove('has-selection');
            }
        }

        dropdowns.forEach(updateTrigger);
        refreshLocks();

        /* 4. Checkbox change handlers */
        if (ddUnit) {
            ddUnit.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
                cb.addEventListener('change', function () {
                    updateTrigger(ddUnit);
                    refreshLocks();
                    setTimeout(function () { form.submit(); }, 120);
                });
            });
        }

        if (ddDept) {
            ddDept.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
                cb.addEventListener('change', function () {
                    updateTrigger(ddDept);
                    refreshLocks();
                });
            });
        }

        form.querySelectorAll('.av-dd input[type="checkbox"]').forEach(function (cb) {
            var dd = cb.closest('.av-dd');
            if (!dd || dd === ddUnit || dd === ddDept) return;

            cb.addEventListener('change', function () {
                updateTrigger(dd);
            });
        });

        /* 5. Debounced auto-submit for search */
        var timer = null;
        form.querySelectorAll('input[name="q"], input[name="ticket_number"]').forEach(function (input) {
            input.addEventListener('input', function () {
                clearTimeout(timer);
                timer = setTimeout(function () { form.submit(); }, 450);
            });
        });

        /* 6. Table row click → navigate */
        document.querySelectorAll('.av-row[data-href]').forEach(function (row) {
            function go() { window.location.href = row.getAttribute('data-href'); }
            row.addEventListener('click', go);
            row.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    go();
                }
            });
        });
    });
})();