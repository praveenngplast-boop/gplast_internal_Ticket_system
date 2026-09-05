document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // THEME SYNC FOR THIS PARTIAL
    // ============================================================
    function updateTicketListTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var container = document.querySelector('.uh-ticket-list-container');
        var table = document.querySelector('.uh-ticket-list-table');
        
        if (container) {
            container.style.backgroundColor = isDark ? '#1A1A2E' : '';
        }
        if (table) {
            table.style.backgroundColor = isDark ? '#1A1A2E' : '';
        }
    }

    var themeToggle = document.getElementById('themeToggleFloating');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            setTimeout(updateTicketListTheme, 100);
        });
    }

    var observer = new MutationObserver(function() {
        updateTicketListTheme();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateTicketListTheme, 200);

});