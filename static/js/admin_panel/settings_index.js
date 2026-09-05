document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // THEME SYNC - Keep settings page in sync with base theme
    // ============================================================
    function updateThemeStyles() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var cards = document.querySelectorAll('.settings-card');

        cards.forEach(function(card) {
            if (isDark) {
                card.style.backgroundColor = '#12121F';
                card.style.borderColor = 'rgba(255,255,255,0.1)';
                card.style.color = '#E8EDF5';
            } else {
                card.style.backgroundColor = '';
                card.style.borderColor = '';
                card.style.color = '';
            }
        });

        // Update hero text colors
        var heroH1 = document.querySelector('.settings-hero h1');
        var heroP = document.querySelector('.settings-hero p');
        if (heroH1) {
            heroH1.style.color = isDark ? '#E8EDF5' : '';
        }
        if (heroP) {
            heroP.style.color = isDark ? '#A8B8D8' : '';
        }

        // Update section headings
        var headings = document.querySelectorAll('.settings-section-heading h2');
        headings.forEach(function(h2) {
            h2.style.color = isDark ? '#E8EDF5' : '';
        });

        // Update card headings
        var cardHeadings = document.querySelectorAll('.settings-card h3');
        cardHeadings.forEach(function(h3) {
            h3.style.color = isDark ? '#E8EDF5' : '';
        });

        // Update card paragraphs
        var cardPs = document.querySelectorAll('.settings-card p');
        cardPs.forEach(function(p) {
            p.style.color = isDark ? '#A8B8D8' : '';
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

    // ============================================================
    // CARD CLICK ANIMATION
    // ============================================================
    var cards = document.querySelectorAll('.settings-card:not(.settings-card--backup)');
    cards.forEach(function(card) {
        card.addEventListener('mousedown', function(e) {
            // Don't trigger on action button click
            if (e.target.closest('.settings-card-action')) {
                return;
            }
            this.style.transform = 'scale(0.97)';
            setTimeout(function() {
                card.style.transform = '';
            }, 150);
        });
    });

    // ============================================================
    // BACKUP CARD ANIMATION
    // ============================================================
    var backupCard = document.querySelector('.settings-card--backup');
    if (backupCard) {
        backupCard.addEventListener('click', function(e) {
            // Don't trigger on action button click
            if (e.target.closest('.settings-card-action')) {
                return;
            }
            var actionBtn = this.querySelector('.settings-card-action');
            if (actionBtn && actionBtn.href) {
                window.location.href = actionBtn.href;
            }
        });
    }
});