function startCountdown(deadlineISO) {
    var timerEl = document.getElementById('reopen-timer');
    if (!timerEl || !deadlineISO || deadlineISO === '') {
        if (timerEl) timerEl.innerHTML = 'No deadline set';
        return;
    }

    var deadline = new Date(deadlineISO).getTime();
    
    var style = document.createElement('style');
    style.textContent = `
        @keyframes timerPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.02); }
        }
    `;
    document.head.appendChild(style);

    var interval = setInterval(function() {
        var now = new Date().getTime();
        var distance = deadline - now;

        if (distance < 0) {
            clearInterval(interval);
            timerEl.innerHTML = '⏰ Expired';
            timerEl.style.color = '#EF4444';
            timerEl.style.fontSize = '1rem';
            timerEl.style.animation = 'timerPulse 1s ease-in-out infinite';
            
            var reopenBtn = document.querySelector('[data-bs-target="#reopenModal"]');
            if (reopenBtn) {
                reopenBtn.style.display = 'none';
                var parentDiv = reopenBtn.closest('.card-body');
                if (parentDiv) {
                    var timerBox = parentDiv.querySelector('.reopen-timer-box');
                    if (timerBox) {
                        timerBox.innerHTML = `
                            <div class="text-center py-2">
                                <i class="fa-regular fa-clock fa-2x mb-2 d-block opacity-25" style="color: #EF4444;"></i>
                                <p class="mb-0" style="color: #EF4444; font-size: 0.85rem; font-weight: 600;">
                                    ⏰ Reopen window has expired
                                </p>
                                <p style="color: var(--text-muted); font-size: 0.7rem;">This ticket was closed more than 48 hours ago</p>
                            </div>
                        `;
                    }
                }
            }
            return;
        }

        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        var h = String(hours).padStart(2, '0');
        var m = String(minutes).padStart(2, '0');
        var s = String(seconds).padStart(2, '0');
        
        timerEl.innerHTML = h + 'h ' + m + 'm ' + s + 's';
        
        if (hours < 1) {
            timerEl.style.color = '#EF4444';
            timerEl.style.animation = 'timerPulse 1s ease-in-out infinite';
        } else if (hours < 6) {
            timerEl.style.color = '#F59E0B';
            timerEl.style.animation = 'none';
        } else {
            timerEl.style.color = 'var(--brand-orange)';
            timerEl.style.animation = 'none';
        }
        
    }, 1000);
}

document.addEventListener('DOMContentLoaded', function() {
    var deadlineISO = document.querySelector('input[name="reopen_deadline_iso"]')?.value || '';
    if (deadlineISO && deadlineISO !== '') {
        startCountdown(deadlineISO);
    }

    var timelineItems = document.querySelectorAll('.timeline-item');
    timelineItems.forEach(function(item, index) {
        item.style.opacity = '0';
        setTimeout(function() {
            item.style.transition = 'all 0.4s ease';
            item.style.opacity = '1';
        }, 200 + (index * 80));
    });

    function updateTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, textarea');
        
        inputs.forEach(function(input) {
            input.style.display = 'none';
            void input.offsetHeight;
            input.style.display = '';
            
            if (isDark) {
                input.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                input.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                input.style.color = '#E8EDF5';
            } else {
                input.style.backgroundColor = '#F5F8FF';
                input.style.borderColor = '#DCE3F0';
                input.style.color = '#1A2A6C';
            }
        });
    }

    var themeToggleBtn = document.getElementById('themeToggleFloating');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            setTimeout(updateTheme, 100);
        });
    }

    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                updateTheme();
            }
        });
    });
    
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateTheme, 200);

    // ============================================================
    // PREVENT DOUBLE SUBMIT FOR REOPEN FORM
    // ============================================================
    var reopenForm = document.getElementById('reopenForm');
    if (reopenForm) {
        reopenForm.addEventListener('submit', function(e) {
            if (this.dataset.submitted === 'true') {
                e.preventDefault();
                return false;
            }
            this.dataset.submitted = 'true';
            var submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Reopening...';
            }
        });
    }
});