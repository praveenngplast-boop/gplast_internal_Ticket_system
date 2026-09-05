document.addEventListener('DOMContentLoaded', function() {

    // ============================================================
    // TARGET DATE VALIDATION
    // ============================================================
    function initTargetDateValidation() {
        var targetDateInput = document.getElementById('targetDate');
        if (!targetDateInput) return;
        
        // Set minimum date to today
        var today = new Date();
        var todayStr = today.toISOString().split('T')[0];
        targetDateInput.setAttribute('min', todayStr);
        
        // Set default value to 7 days from now
        var futureDate = new Date(today);
        futureDate.setDate(futureDate.getDate() + 7);
        var futureStr = futureDate.toISOString().split('T')[0];
        if (!targetDateInput.value) {
            targetDateInput.value = futureStr;
        }
        
        // Validate on change
        targetDateInput.addEventListener('change', function() {
            var selectedDate = this.value;
            if (!selectedDate) return;
            
            var selected = new Date(selectedDate);
            var today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selected < today) {
                showToast('Target date cannot be in the past. Please select a future date.', 'error');
                this.value = todayStr;
            }
        });
        
        // Validate on form submit
        var assignForm = document.getElementById('assignForm');
        if (assignForm) {
            assignForm.addEventListener('submit', function(e) {
                var targetDate = document.getElementById('targetDate');
                if (targetDate) {
                    var selected = new Date(targetDate.value);
                    var today = new Date();
                    today.setHours(0, 0, 0, 0);
                    
                    if (selected < today) {
                        e.preventDefault();
                        showToast('Target date cannot be in the past. Please select a future date.', 'error');
                        targetDate.focus();
                        return false;
                    }
                    
                    if (!targetDate.value) {
                        e.preventDefault();
                        showToast('Please select a target date.', 'error');
                        targetDate.focus();
                        return false;
                    }
                }
            });
        }
    }

    // ============================================================
    // TOAST NOTIFICATION SYSTEM
    // ============================================================
    function showToast(message, type) {
        type = type || 'success';
        
        var container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container-custom';
            document.body.appendChild(container);
        }
        
        var toast = document.createElement('div');
        toast.className = 'toast-custom ' + type;
        
        var iconMap = {
            'success': 'fa-check-circle',
            'error': 'fa-times-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        var icon = iconMap[type] || 'fa-info-circle';
        
        toast.innerHTML = '<i class="fas ' + icon + ' me-2"></i>' + message;
        container.appendChild(toast);
        
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(30px)';
            toast.style.transition = 'all 0.4s ease';
            setTimeout(function() {
                if (toast.parentNode) toast.remove();
            }, 400);
        }, 4000);
    }

    // ============================================================
    // REOPEN COUNTDOWN TIMER
    // ============================================================
    function startCountdown(deadlineISO) {
        var timerBadge = document.getElementById('reopen-timer-badge');
        var timerText = document.getElementById('reopen-timer-text');
        
        if (!deadlineISO || deadlineISO === '') return;

        var deadline = new Date(deadlineISO).getTime();
        var interval = setInterval(function() {
            var now = new Date().getTime();
            var distance = deadline - now;

            if (distance < 0) {
                clearInterval(interval);
                if (timerBadge) {
                    timerBadge.innerHTML = 'Expired';
                    timerBadge.style.background = 'rgba(239, 68, 68, 0.3)';
                }
                if (timerText) {
                    timerText.textContent = 'Reopen window closed';
                    timerText.style.color = '#EF4444';
                }
                var reopenBtn = document.querySelector('.action-btn-reopen');
                if (reopenBtn) {
                    var parent = reopenBtn.closest('.action-buttons');
                    if (parent) {
                        parent.innerHTML = '<span class="action-status-msg" style="color: var(--text-muted);"><i class="fa-regular fa-clock"></i> Cannot reopen (48+ hours elapsed)</span>';
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

            if (timerBadge) {
                timerBadge.innerHTML = h + ':' + m + ':' + s;
            }
            if (timerText) {
                timerText.textContent = 'Time left to reopen';
            }

            if (timerBadge) {
                if (hours < 1) {
                    timerBadge.style.background = 'rgba(239, 68, 68, 0.3)';
                } else if (hours < 6) {
                    timerBadge.style.background = 'rgba(245, 158, 11, 0.3)';
                } else {
                    timerBadge.style.background = 'rgba(59, 130, 246, 0.2)';
                }
            }
        }, 1000);
    }

    var deadlineISO = document.querySelector('input[name="reopen_deadline_iso"]')?.value || '';
    if (deadlineISO && deadlineISO !== '') {
        startCountdown(deadlineISO);
    }

    // ============================================================
    // DYNAMIC SUB ERROR TYPES
    // ============================================================
    const subErrorOptions = {
        'Roadmap Error': [
            'Database Error',
            'Logic / Functional Error',
            'Application Error',
            'Calculation Error',
            'Report / Print Error',
            'Workflow / Approval Error',
            'Integration / API Error',
            'Barcode Error',
            'Performance Error',
            'Access / Permission Error',
            'Master Data / Configuration Error',
            'Other ERP Error'
        ],
        'GPL Error': [
            'User / Data Entry Error',
            'Process / Procedure Error',
            'Master Data Error',
            'Other GPL Error'
        ]
    };

    var mainErrorSelect = document.getElementById('mainErrorType');
    var subErrorSelect = document.getElementById('subErrorType');
    var subErrorGroup = document.getElementById('subErrorGroup');

    if (mainErrorSelect && subErrorSelect && subErrorGroup) {
        mainErrorSelect.addEventListener('change', function() {
            var selected = this.value;
            var subOptions = subErrorOptions[selected] || [];

            // Clear existing options
            subErrorSelect.innerHTML = '<option value="">-- Select Sub Error Type --</option>';

            if (subOptions.length > 0) {
                subOptions.forEach(function(option) {
                    var opt = document.createElement('option');
                    opt.value = option;
                    opt.textContent = option;
                    subErrorSelect.appendChild(opt);
                });
                subErrorGroup.classList.add('show');
                subErrorSelect.disabled = false;
                subErrorSelect.required = true;
            } else {
                subErrorGroup.classList.remove('show');
                subErrorSelect.disabled = true;
                subErrorSelect.required = false;
            }
        });

        // Trigger change on load if value is set
        if (mainErrorSelect.value) {
            mainErrorSelect.dispatchEvent(new Event('change'));
        }
    }

    // ============================================================
    // PREVENT DOUBLE SUBMIT
    // ============================================================
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (this.dataset.submitted === 'true') {
                e.preventDefault();
                return false;
            }
            this.dataset.submitted = 'true';
            
            // Show loading state on submit button
            var submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                var originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
                
                // Re-enable after 3 seconds if not redirected
                setTimeout(function() {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    form.dataset.submitted = 'false';
                }, 5000);
            }
            
            setTimeout(function() {
                form.dataset.submitted = 'false';
            }, 3000);
        });
    });

    // ============================================================
    // THEME SYNC
    // ============================================================
    function updateFormTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var inputs = document.querySelectorAll('.form-control, .form-select, textarea');

        inputs.forEach(function(input) {
            if (isDark) {
                input.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                input.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                input.style.color = '#E8EDF5';
                input.style.webkitTextFillColor = '#E8EDF5';
            } else {
                input.style.backgroundColor = '#F8FAFF';
                input.style.borderColor = '#DCE3F0';
                input.style.color = '#1A2A6C';
                input.style.webkitTextFillColor = '#1A2A6C';
            }
        });
    }

    var themeToggleBtn = document.getElementById('themeToggleFloating');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            setTimeout(updateFormTheme, 100);
        });
    }

    var observer = new MutationObserver(function() {
        updateFormTheme();
    });

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });

    setTimeout(updateFormTheme, 200);

    // ============================================================
    // ANIMATE TIMELINE ITEMS
    // ============================================================
    var timelineItems = document.querySelectorAll('.timeline-item');
    timelineItems.forEach(function(item, index) {
        item.style.animationDelay = (index * 0.05) + 's';
    });

    // ============================================================
    // MODAL CLEANUP ON CLOSE
    // ============================================================
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            // Reset form fields if needed
            var form = this.querySelector('form');
            if (form) {
                form.dataset.submitted = 'false';
                var submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    if (submitBtn.dataset.originalText) {
                        submitBtn.innerHTML = submitBtn.dataset.originalText;
                    }
                }
            }
        });
    });

    // ============================================================
    // INITIALIZE TARGET DATE VALIDATION
    // ============================================================
    initTargetDateValidation();

    // ============================================================
    // TOAST STYLES (if not already present)
    // ============================================================
    var style = document.createElement('style');
    style.textContent = `
        .toast-container-custom {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-width: 400px;
        }
        .toast-custom {
            padding: 12px 20px;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: slideInRight 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .toast-custom.success { background: linear-gradient(135deg, #16a34a, #22c55e); }
        .toast-custom.error { background: linear-gradient(135deg, #dc2626, #ef4444); }
        .toast-custom.warning { background: linear-gradient(135deg, #d97706, #f59e0b); }
        .toast-custom.info { background: linear-gradient(135deg, #2563eb, #3b82f6); }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
    `;
    document.head.appendChild(style);

    console.log('✅ Admin Ticket Detail JS loaded successfully');
    console.log('📌 Target date validation initialized');
});