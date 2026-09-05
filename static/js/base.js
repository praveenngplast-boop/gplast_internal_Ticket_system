// ============================================================
// NOTIFICATION FUNCTIONS - GLOBAL SCOPE
// ============================================================

function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

function performMarkAllRead() {
    const badge = document.getElementById('notificationBadge');
    const itemsContainer = document.getElementById('notificationItems');
    const header = document.querySelector('#notificationDropdownMenu .dropdown-header');
    
    // ✅ FIXED: Use correct URL with custom-admin prefix
    fetch('/custom-admin/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (badge) {
                badge.classList.add('hidden');
                badge.textContent = '0';
            }
            
            if (itemsContainer) {
                itemsContainer.innerHTML = `
                    <li style="list-style: none; margin: 0; padding: 0;">
                        <div style="padding: 2rem 1rem; text-align: center; color: var(--text-muted, #7A7A8A);">
                            <i class="fa-regular fa-circle-check" style="font-size: 2.5rem; display: block; margin-bottom: 0.75rem; color: #22C55E;"></i>
                            <div style="font-size: 0.9rem; font-weight: 500; color: var(--text-primary, #0A0A1A);">All caught up!</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted, #7A7A8A); margin-top: 0.15rem;">No unread notifications</div>
                        </div>
                    </li>
                `;
            }
            
            if (header) {
                const markBtn = header.querySelector('.mark-all-btn');
                if (markBtn) markBtn.remove();
            }
            
            if (window.showToast) {
                window.showToast('All notifications marked as read!', 'success', 'All Read');
            }
        }
    })
    .catch(error => console.error('Error marking all as read:', error));
}

window.confirmMarkAllRead = function() {
    const badge = document.getElementById('notificationBadge');
    if (badge && (badge.textContent === '0' || badge.textContent === '')) {
        return;
    }
    
    if (window.showConfirmation) {
        window.showConfirmation(
            'Are you sure you want to mark all notifications as read? This action cannot be undone.',
            function() {
                performMarkAllRead();
            }
        );
    } else {
        if (confirm('Are you sure you want to mark all notifications as read?')) {
            performMarkAllRead();
        }
    }
};

function refreshNotifications() {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;
    
    // ✅ FIXED: Use correct URL with custom-admin prefix
    fetch('/custom-admin/notifications/get/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (badge) {
                if (data.count > 0) {
                    badge.classList.remove('hidden');
                    badge.textContent = data.count;
                    badge.classList.add('pulse');
                } else {
                    badge.classList.add('hidden');
                    badge.textContent = '0';
                    badge.classList.remove('pulse');
                }
            }
            
            const itemsContainer = document.getElementById('notificationItems');
            if (itemsContainer && data.html) {
                itemsContainer.innerHTML = data.html;
            }
        }
    })
    .catch(error => console.error('Error refreshing notifications:', error));
}

// ============================================================
// DOM CONTENT LOADED
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarCollapseToggle = document.getElementById('sidebarCollapseToggle');
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    
    // ===== HAMBURGER MENU TOGGLE (Mobile) =====
    let isSidebarOpen = false;

    function toggleSidebarMobile() {
        isSidebarOpen = !isSidebarOpen;
        sidebar.classList.toggle('open', isSidebarOpen);
        sidebarOverlay.classList.toggle('show', isSidebarOpen);
        document.body.style.overflow = isSidebarOpen ? 'hidden' : '';
        
        // Change hamburger icon
        if (hamburgerBtn) {
            const icon = hamburgerBtn.querySelector('i');
            if (isSidebarOpen) {
                icon.className = 'fa-solid fa-xmark';
            } else {
                icon.className = 'fa-solid fa-bars';
            }
        }
    }

    // Hamburger button click
    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebarMobile();
        });
    }

    // Click on overlay to close
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            if (isSidebarOpen) {
                toggleSidebarMobile();
            }
        });
    }

    // Close sidebar when clicking a link (mobile)
    document.querySelectorAll('.sidebar-link:not(.theme-toggle-link)').forEach(function(link) {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && isSidebarOpen) {
                toggleSidebarMobile();
            }
        });
    });

    // ===== THEME TOGGLE =====
    const sidebarThemeToggle = document.getElementById('sidebarThemeToggle');
    const sidebarThemeIcon = document.getElementById('sidebarThemeIcon');
    const sidebarThemeText = document.getElementById('sidebarThemeText');
    
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            if (sidebarThemeIcon) {
                sidebarThemeIcon.className = 'fas fa-sun';
            }
            if (sidebarThemeText) {
                sidebarThemeText.textContent = 'Light Mode';
            }
        } else {
            document.documentElement.removeAttribute('data-theme');
            if (sidebarThemeIcon) {
                sidebarThemeIcon.className = 'fas fa-moon';
            }
            if (sidebarThemeText) {
                sidebarThemeText.textContent = 'Dark Mode';
            }
        }
        localStorage.setItem('theme', theme);
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const newTheme = current === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    }

    if (sidebarThemeToggle) {
        sidebarThemeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleTheme();
        });
    }

    // ===== SIDEBAR COLLAPSE =====
    const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isSidebarCollapsed && window.innerWidth >= 992) {
        sidebar.classList.add('collapsed');
        if (sidebarCollapseToggle) {
            sidebarCollapseToggle.querySelector('i').className = 'fa-solid fa-chevron-right';
        }
    }

    function toggleSidebarCollapse() {
        if (window.innerWidth >= 992) {
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            
            if (sidebarCollapseToggle) {
                const icon = sidebarCollapseToggle.querySelector('i');
                icon.className = isCollapsed ? 'fa-solid fa-chevron-right' : 'fa-solid fa-chevron-left';
            }
            
            window.dispatchEvent(new Event('resize'));
        }
    }

    if (sidebarCollapseToggle) {
        sidebarCollapseToggle.addEventListener('click', toggleSidebarCollapse);
    }

    // ===== TOAST NOTIFICATIONS =====
    const toastContainer = document.getElementById('toastContainer');

    window.showToast = function(message, type = 'info', title = null) {
        if (!toastContainer) return;
        const types = {
            success: { icon: 'fa-circle-check', title: 'Success' },
            error: { icon: 'fa-circle-xmark', title: 'Error' },
            warning: { icon: 'fa-triangle-exclamation', title: 'Warning' },
            info: { icon: 'fa-circle-info', title: 'Info' }
        };
        const config = types[type] || types.info;
        const toastTitle = title || config.title;
        const toast = document.createElement('div');
        toast.className = 'toast-custom toast-' + type;
        toast.innerHTML = `
            <div class="toast-icon"><i class="fa-solid ${config.icon}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${toastTitle}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close-btn" aria-label="Close toast"><i class="fa-solid fa-xmark"></i></button>
            <div class="toast-progress"></div>
        `;
        toast.querySelector('.toast-close-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            removeToast(toast);
        });
        toast._timeout = setTimeout(function() { removeToast(toast); }, 5000);
        toastContainer.appendChild(toast);
    };

    function removeToast(toast) {
        if (!toast || toast.classList.contains('removing')) return;
        if (toast._timeout) clearTimeout(toast._timeout);
        toast.classList.add('removing');
        setTimeout(function() { 
            if (toast.parentNode) toast.parentNode.removeChild(toast); 
        }, 400);
    }

    const djangoMessagesContainer = document.getElementById('djangoMessages');
    if (djangoMessagesContainer) {
        djangoMessagesContainer.querySelectorAll('.django-message').forEach(function(el) {
            const message = el.getAttribute('data-message');
            const type = el.getAttribute('data-type');
            if (message) window.showToast(message, type);
        });
        djangoMessagesContainer.remove();
    }

    // ===== NAVBAR SCROLL EFFECT =====
    const navbar = document.getElementById('mainNav');
    if (navbar && !navbar.classList.contains('navbar-hidden')) {
        window.addEventListener('scroll', function() {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    // ===== CONFIRMATION MODAL =====
    window.showConfirmation = function(message, onConfirm) {
        const confirmModal = document.getElementById('confirmModal');
        const confirmBody = document.getElementById('confirmModalBody');
        const confirmYesBtn = document.getElementById('confirmModalYesBtn');
        if (!confirmModal || !confirmBody || !confirmYesBtn) return;
        confirmBody.textContent = message;
        const modal = new bootstrap.Modal(confirmModal);
        modal.show();
        const newYesBtn = confirmYesBtn.cloneNode(true);
        confirmYesBtn.parentNode.replaceChild(newYesBtn, confirmYesBtn);
        newYesBtn.addEventListener('click', function() {
            modal.hide();
            if (typeof onConfirm === 'function') onConfirm();
        });
        confirmModal.querySelectorAll('.btn-close, .btn-no').forEach(function(btn) {
            btn.addEventListener('click', function() { modal.hide(); }, { once: true });
        });
    };

    // ===== RESPONSIVE HANDLING =====
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            // Close mobile sidebar if open
            if (isSidebarOpen) {
                isSidebarOpen = false;
                sidebar.classList.remove('open');
                sidebarOverlay.classList.remove('show');
                document.body.style.overflow = '';
                if (hamburgerBtn) {
                    hamburgerBtn.querySelector('i').className = 'fa-solid fa-bars';
                }
            }
            
            // Apply collapse state
            if (localStorage.getItem('sidebarCollapsed') === 'true') {
                sidebar.classList.add('collapsed');
                if (sidebarCollapseToggle) {
                    sidebarCollapseToggle.querySelector('i').className = 'fa-solid fa-chevron-right';
                }
            } else {
                sidebar.classList.remove('collapsed');
                if (sidebarCollapseToggle) {
                    sidebarCollapseToggle.querySelector('i').className = 'fa-solid fa-chevron-left';
                }
            }
        } else {
            // On mobile, remove collapsed state
            sidebar.classList.remove('collapsed');
            if (sidebarCollapseToggle) {
                sidebarCollapseToggle.querySelector('i').className = 'fa-solid fa-chevron-left';
            }
        }
    });

    // ===== START NOTIFICATION REFRESH =====
    const isAdmin = document.querySelector('.role-badge.admin') !== null;
    if (isAdmin) {
        setTimeout(refreshNotifications, 2000);
        setInterval(refreshNotifications, 30000);
    }

    console.log('✅ Base.js loaded with fixed notification URLs');
    console.log('🔔 Notification GET URL: /custom-admin/notifications/get/');
    console.log('🔔 Mark All Read URL: /custom-admin/notifications/mark-all-read/');
});