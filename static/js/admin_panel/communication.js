document.addEventListener('DOMContentLoaded', function() {

    function updateTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, .form-select');
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

    var ccList = document.getElementById('communicationAdditionalEmails');
    var addCcButton = document.getElementById('addCommunicationCc');
    if (ccList && addCcButton) {
        addCcButton.addEventListener('click', function() {
            var row = document.createElement('div');
            row.className = 'schedule-cc-row';
            row.innerHTML = '<input class="form-control" type="email" name="additional_emails" placeholder="email@company.com"><button type="button" class="schedule-remove-cc" title="Remove email"><i class="fa-solid fa-xmark"></i></button>';
            ccList.appendChild(row);
            row.querySelector('input').focus();
        });
        ccList.addEventListener('click', function(event) {
            var remove = event.target.closest('.schedule-remove-cc');
            if (remove) remove.closest('.schedule-cc-row').remove();
        });
    }
});