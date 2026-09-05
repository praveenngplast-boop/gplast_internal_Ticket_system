document.addEventListener('DOMContentLoaded', function() {
    const auditForm = document.getElementById('auditFilterForm');
    const dateFrom = auditForm.querySelector('[name="date_from"]');
    const dateTo = auditForm.querySelector('[name="date_to"]');
    const dateRangeError = document.getElementById('dateRangeError');

    function validateDateRange() {
        dateTo.min = dateFrom.value || '';
        const hasInvalidRange = dateFrom.value && dateTo.value && dateTo.value < dateFrom.value;
        const message = hasInvalidRange ? 'Date To cannot be earlier than Date From.' : '';
        dateTo.setCustomValidity(message);
        dateRangeError.textContent = message;
        return !hasInvalidRange;
    }

    dateFrom.addEventListener('change', validateDateRange);
    dateTo.addEventListener('change', validateDateRange);
    auditForm.addEventListener('submit', function(event) {
        if (!validateDateRange()) {
            event.preventDefault();
            dateTo.reportValidity();
        }
    });
    validateDateRange();

    function syncAuditTheme() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        // CSS custom properties handle everything automatically
    }
    
    syncAuditTheme();
    
    const themeObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                syncAuditTheme();
            }
        });
    });
    
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
    
    window.addEventListener('storage', function(e) {
        if (e.key === 'theme') {
            const newTheme = e.newValue || 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            syncAuditTheme();
        }
    });
});