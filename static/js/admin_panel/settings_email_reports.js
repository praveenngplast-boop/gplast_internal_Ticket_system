document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // TOGGLE STATUS
    // ============================================================
    var enabledCheckbox = document.getElementById('enabled');
    var toggleStatus = document.getElementById('toggleStatus');

    if (enabledCheckbox && toggleStatus) {
        enabledCheckbox.addEventListener('change', function() {
            if (this.checked) {
                toggleStatus.className = 'email-toggle-status active';
                toggleStatus.innerHTML = '<i class="fa-regular fa-circle-check"></i> Active';
            } else {
                toggleStatus.className = 'email-toggle-status inactive';
                toggleStatus.innerHTML = '<i class="fa-regular fa-circle-xmark"></i> Inactive';
            }
        });
    }

    // ============================================================
    // FREQUENCY CHECKBOXES
    // ============================================================
    document.querySelectorAll('.email-frequency-item input[type="checkbox"]').forEach(function(input) {
        input.addEventListener('change', function() {
            var parent = this.closest('.email-frequency-item');
            if (parent) {
                parent.classList.toggle('active', this.checked);
            }
        });
    });

    // ============================================================
    // ALL UNITS TOGGLE
    // ============================================================
    var allUnitsCheckbox = document.getElementById('all_units');
    if (allUnitsCheckbox) {
        allUnitsCheckbox.addEventListener('change', function() {
            document.querySelectorAll('.unit-choice').forEach(function(box) {
                box.style.opacity = this.checked ? '0.4' : '1';
                box.style.pointerEvents = this.checked ? 'none' : 'auto';
                if (this.checked) {
                    var cb = box.querySelector('input[type="checkbox"]');
                    if (cb) cb.checked = false;
                }
            }.bind(this));
        });
    }

    // ============================================================
    // ADD ADDITIONAL EMAIL
    // ============================================================
    var additionalEmailList = document.getElementById('additionalEmailList');
    var addEmailBtn = document.getElementById('addAdditionalEmail');

    if (addEmailBtn && additionalEmailList) {
        addEmailBtn.addEventListener('click', function() {
            var row = document.createElement('div');
            row.className = 'email-additional-row';
            row.innerHTML = `
                <input class="email-form-control" type="email" name="additional_emails" placeholder="person@example.com">
                <button class="email-remove-btn" type="button" aria-label="Remove email">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            `;
            additionalEmailList.appendChild(row);
            var input = row.querySelector('input');
            if (input) input.focus();
        });
    }

    // ============================================================
    // REMOVE ADDITIONAL EMAIL
    // ============================================================
    if (additionalEmailList) {
        additionalEmailList.addEventListener('click', function(event) {
            var removeButton = event.target.closest('.email-remove-btn');
            if (!removeButton) return;
            var rows = additionalEmailList.querySelectorAll('.email-additional-row');
            if (rows.length > 1) {
                removeButton.closest('.email-additional-row').remove();
            } else {
                var input = removeButton.closest('.email-additional-row').querySelector('input');
                if (input) input.value = '';
            }
        });
    }

    // ============================================================
    // INITIAL: DISABLE UNIT CHECKBOXES IF ALL UNITS IS CHECKED
    // ============================================================
    (function() {
        var allUnits = document.getElementById('all_units');
        if (allUnits && allUnits.checked) {
            document.querySelectorAll('.unit-choice').forEach(function(box) {
                box.style.opacity = '0.4';
                box.style.pointerEvents = 'none';
                var cb = box.querySelector('input[type="checkbox"]');
                if (cb) cb.checked = false;
            });
        }
    })();

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.email-form-control, .email-form-select');
        inputs.forEach(function(input) {
            if (isDark) {
                input.style.backgroundColor = 'rgba(255,255,255,0.05)';
                input.style.borderColor = 'rgba(255,255,255,0.08)';
                input.style.color = '#E8EDF5';
            } else {
                input.style.backgroundColor = '';
                input.style.borderColor = '';
                input.style.color = '';
            }
        });

        var selects = document.querySelectorAll('.email-form-select');
        selects.forEach(function(select) {
            var options = select.querySelectorAll('option');
            options.forEach(function(option) {
                if (isDark) {
                    option.style.backgroundColor = '#1A1A2E';
                    option.style.color = '#E8EDF5';
                } else {
                    option.style.backgroundColor = '';
                    option.style.color = '';
                }
            });
        });
    }

    var themeToggle = document.getElementById('themeToggleFloating');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            setTimeout(updateThemeStyles, 100);
        });
    }

    var observer = new MutationObserver(function() {
        updateThemeStyles();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateThemeStyles, 200);
});