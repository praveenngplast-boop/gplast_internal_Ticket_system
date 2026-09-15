// ============================================================
// GPLAST SHELL CONTROLLER — Icon Rail + Labels Edition
// Theme · Tooltips · Rail · Rail Collapse · Rail Tooltip ·
// Profile Menu · Notifications · Toasts · Confirmation Modal ·
// Navbar · Shortcuts · Time-Aware Greeting
// ============================================================

(function () {
    'use strict';

    // ==========================================================
    // 0. THEME
    // ==========================================================
    const ThemeController = (() => {
        const KEY = 'theme';

        function read() {
            try { return localStorage.getItem(KEY) || 'light'; }
            catch (e) { return 'light'; }
        }

        function applyRaw(theme) {
            if (theme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
        }

        function persist(theme) {
            try { localStorage.setItem(KEY, theme); } catch (e) {}
        }

        const initial = read();
        applyRaw(initial);

        function apply(theme) {
            applyRaw(theme);
            persist(theme);
        }

        function toggle() {
            const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            apply(current === 'dark' ? 'light' : 'dark');
        }

        return { apply, toggle, initial };
    })();

    window.shellApplyTheme = ThemeController.apply;
    window.shellToggleTheme = ThemeController.toggle;


    // ==========================================================
    // 1. TOOLTIP ENGINE
    //    Generic tooltips — used for toggle, bell, avatar, etc.
    //    Skips rail buttons (RailTooltipController handles them).
    // ==========================================================
    const TooltipEngine = (() => {
        let tipEl = null;
        let currentTarget = null;
        let showTimer = null;
        const SHOW_DELAY = 120;
        const HIDE_DELAY = 60;

        function ensureEl() {
            if (tipEl) return tipEl;
            tipEl = document.createElement('div');
            tipEl.className = 'shell-tip';
            tipEl.setAttribute('role', 'tooltip');
            document.body.appendChild(tipEl);
            return tipEl;
        }

        function position(target) {
            const el = ensureEl();
            const rect = target.getBoundingClientRect();
            const placement = target.getAttribute('data-tip-placement') || 'top';
            el.setAttribute('data-placement', placement);

            el.classList.add('show');
            const tipRect = el.getBoundingClientRect();

            let top, left;
            switch (placement) {
                case 'right':
                    top = rect.top + rect.height / 2 - tipRect.height / 2;
                    left = rect.right + 10;
                    break;
                case 'left':
                    top = rect.top + rect.height / 2 - tipRect.height / 2;
                    left = rect.left - tipRect.width - 10;
                    break;
                case 'bottom':
                    top = rect.bottom + 10;
                    left = rect.left + rect.width / 2 - tipRect.width / 2;
                    break;
                case 'top':
                default:
                    top = rect.top - tipRect.height - 10;
                    left = rect.left + rect.width / 2 - tipRect.width / 2;
                    break;
            }

            const pad = 8;
            left = Math.max(pad, Math.min(left, window.innerWidth - tipRect.width - pad));
            top = Math.max(pad, Math.min(top, window.innerHeight - tipRect.height - pad));

            el.style.top = top + 'px';
            el.style.left = left + 'px';
        }

        function show(target) {
            if (!target) return;

            // Skip rail buttons entirely — RailTooltipController handles them
            if (target.closest && target.closest('.shell-rail-wrap')) {
                return;
            }

            const text = target.getAttribute('data-tip');
            if (!text) return;
            currentTarget = target;
            const el = ensureEl();
            el.textContent = text;
            requestAnimationFrame(() => position(target));
        }

        function hide() {
            currentTarget = null;
            if (tipEl) tipEl.classList.remove('show');
        }

        function bind() {
            document.querySelectorAll('[data-tip]').forEach((el) => {
                if (el._tipBound) return;
                el._tipBound = true;

                el.addEventListener('mouseenter', () => {
                    clearTimeout(showTimer);
                    showTimer = setTimeout(() => show(el), SHOW_DELAY);
                });
                el.addEventListener('mouseleave', () => {
                    clearTimeout(showTimer);
                    showTimer = setTimeout(hide, HIDE_DELAY);
                });
                el.addEventListener('focus', () => show(el));
                el.addEventListener('blur', hide);
                el.addEventListener('click', hide);
            });
        }

        function refresh() { bind(); }

        window.addEventListener('scroll', () => {
            if (currentTarget) position(currentTarget);
        }, true);
        window.addEventListener('resize', () => {
            if (currentTarget) position(currentTarget);
        });

        return { bind, refresh, hide };
    })();


    // ==========================================================
    // 2. RAIL CONTROLLER (mobile drawer)
    // ==========================================================
    const RailController = (() => {
        const rail = document.getElementById('shellRail');
        const backdrop = document.getElementById('shellRailBackdrop');
        const hamburger = document.getElementById('shellHamburger');

        if (!rail) {
            return { init() {}, open() {}, close() {}, toggle() {}, isOpen: () => false };
        }

        const isMobile = () => window.matchMedia('(max-width: 991px)').matches;
        let isOpen = false;

        function open() {
            if (!isMobile()) return;
            isOpen = true;
            TooltipEngine.hide();
            rail.classList.add('open');
            if (backdrop) backdrop.classList.add('open');
            document.body.style.overflow = 'hidden';
        }

        function close() {
            if (!isOpen) return;
            isOpen = false;
            rail.classList.remove('open');
            if (backdrop) backdrop.classList.remove('open');
            document.body.style.overflow = '';
        }

        function toggle() { isOpen ? close() : open(); }

        if (hamburger) {
            hamburger.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                toggle();
            });
        }

        if (backdrop) backdrop.addEventListener('click', close);

        rail.querySelectorAll('.shell-rail-btn').forEach((link) => {
            link.addEventListener('click', () => {
                if (isMobile()) close();
            });
        });

        window.addEventListener('resize', () => {
            if (!isMobile()) close();
        });

        return { init() {}, open, close, toggle, isOpen: () => isOpen };
    })();


    // ==========================================================
    // 3. RAIL COLLAPSE CONTROLLER
    //    Expanded (220px, icon + label) ↔ Collapsed (64px, icon only)
    // ==========================================================
    const RailCollapseController = (() => {
        const rail = document.getElementById('shellRail');
        const toggleBtn = document.getElementById('shellRailToggle');
        const content = document.querySelector('.shell-content');
        const footer = document.querySelector('.shell-footer');

        if (!rail || !toggleBtn) {
            return { init() {}, collapse() {}, expand() {}, toggle() {}, isCollapsed: () => false };
        }

        const isMobile = () => window.matchMedia('(max-width: 991px)').matches;
        const KEY = 'shellRailCollapsed';

        let collapsed = false;

        function apply(collapsedState, animate = true) {
            collapsed = collapsedState;

            if (animate) {
                rail.style.transition = '';
            } else {
                rail.style.transition = 'none';
            }

            rail.classList.toggle('collapsed', collapsed);
            if (content) content.classList.toggle('rail-collapsed', collapsed);
            if (footer) footer.classList.toggle('rail-collapsed', collapsed);

            // Update document root flag
            if (collapsed) {
                document.documentElement.setAttribute('data-rail-collapsed', '1');
            } else {
                document.documentElement.removeAttribute('data-rail-collapsed');
            }

            // Update toggle button ARIA + tooltip
            toggleBtn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
            toggleBtn.setAttribute('aria-label', collapsed ? 'Expand navigation' : 'Collapse navigation');
            toggleBtn.setAttribute('data-tip', collapsed ? 'Expand (press [)' : 'Collapse (press [)');

            // Persist state
            try { localStorage.setItem(KEY, collapsed ? '1' : '0'); } catch (e) {}

            if (!animate) {
                requestAnimationFrame(() => {
                    rail.style.transition = '';
                });
            }
        }

        function collapse() { apply(true); }
        function expand()   { apply(false); }
        function toggle()   { apply(!collapsed); }

        // Restore persisted state on load (no animation, no flash)
        try {
            const stored = localStorage.getItem(KEY) === '1';
            if (stored && !isMobile()) {
                apply(true, false);
            } else {
                apply(false, false);
            }
        } catch (e) {
            apply(false, false);
        }

        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            TooltipEngine.hide();

            // On mobile: open the drawer. On desktop: toggle collapse.
            if (isMobile()) {
                RailController.toggle();
            } else {
                toggle();
            }
        });

        // Auto-expand on mobile (rail is drawer there, never collapsed)
        window.addEventListener('resize', () => {
            if (isMobile() && collapsed) {
                apply(false, false);
            }
        });

        return {
            init() {},
            collapse,
            expand,
            toggle,
            isCollapsed: () => collapsed,
        };
    })();


    // ==========================================================
    // 3b. RAIL TOOLTIP — floating label on collapsed rail icons
    // ==========================================================
    const RailTooltipController = (() => {
        const rail = document.getElementById('shellRail');
        if (!rail) return { init() {}, hide() {} };

        const isMobile = () => window.matchMedia('(max-width: 991px)').matches;
        const isCollapsed = () => rail.classList.contains('collapsed') && !isMobile();

        let tip = null;
        let showTimer = null;
        let hideTimer = null;
        const SHOW_DELAY = 100;
        const HIDE_DELAY = 80;

        function ensureTip() {
            if (tip) return tip;
            tip = document.createElement('div');
            tip.className = 'shell-rail-tooltip';
            tip.setAttribute('role', 'tooltip');
            document.body.appendChild(tip);
            return tip;
        }

        function position(target) {
            const el = ensureTip();
            const rect = target.getBoundingClientRect();
            const tipRect = el.getBoundingClientRect();

            const top = rect.top + rect.height / 2 - tipRect.height / 2;
            const left = rect.right + 14;

            const pad = 8;
            el.style.top = Math.max(pad, Math.min(top, window.innerHeight - tipRect.height - pad)) + 'px';
            el.style.left = Math.max(pad, Math.min(left, window.innerWidth - tipRect.width - pad)) + 'px';
        }

        function show(target) {
            if (!isCollapsed()) return;
            const text = target.getAttribute('data-tip');
            if (!text) return;

            const el = ensureTip();
            el.textContent = text;
            el.classList.add('show');
            requestAnimationFrame(() => position(target));
        }

        function hide() {
            if (tip) tip.classList.remove('show');
        }

        // Bind only to rail buttons
        rail.querySelectorAll('.shell-rail-btn').forEach((btn) => {
            btn.addEventListener('mouseenter', () => {
                if (!isCollapsed()) return;
                clearTimeout(showTimer);
                clearTimeout(hideTimer);
                showTimer = setTimeout(() => show(btn), SHOW_DELAY);
            });

            btn.addEventListener('mouseleave', () => {
                clearTimeout(showTimer);
                clearTimeout(hideTimer);
                hideTimer = setTimeout(hide, HIDE_DELAY);
            });

            btn.addEventListener('click', () => hide());
        });

        window.addEventListener('scroll', hide, { passive: true });
        window.addEventListener('resize', hide);

        return { init() {}, hide };
    })();


    // ==========================================================
    // 4. PROFILE MENU CONTROLLER (rail avatar only)
    // ==========================================================
    const ProfileMenuController = (() => {
        const menu = document.getElementById('shellProfileMenu');
        const railBtn = document.getElementById('shellRailProfileBtn');

        if (!menu || !railBtn) {
            return { init() {}, open() {}, close() {}, toggle() {} };
        }

        let isOpen = false;

        function positionMenu() {
            const rect = railBtn.getBoundingClientRect();
            const pad = 12;

            menu.classList.remove('from-navbar');
            menu.classList.add('from-rail');

            const left = rect.right + pad;
            const menuH = menu.offsetHeight || 420;
            let top = rect.bottom - menuH;
            top = Math.max(pad, Math.min(top, window.innerHeight - menuH - pad));

            menu.style.left = left + 'px';
            menu.style.top = top + 'px';
            menu.style.right = 'auto';
            menu.style.bottom = 'auto';
        }

        function open() {
            if (isOpen) return;
            isOpen = true;
            TooltipEngine.hide();
            RailTooltipController.hide();

            menu.style.visibility = 'hidden';
            menu.classList.add('open');
            menu.setAttribute('aria-hidden', 'false');
            railBtn.setAttribute('aria-expanded', 'true');

            requestAnimationFrame(() => {
                positionMenu();
                menu.style.visibility = '';
            });
        }

        function close() {
            if (!isOpen) return;
            isOpen = false;
            menu.classList.remove('open');
            menu.setAttribute('aria-hidden', 'true');
            railBtn.setAttribute('aria-expanded', 'false');
            TooltipEngine.hide();
        }

        function toggle() { isOpen ? close() : open(); }

        railBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggle();
        });

        document.addEventListener('click', (e) => {
            if (!isOpen) return;
            if (menu.contains(e.target)) return;
            if (railBtn.contains(e.target)) return;
            close();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                close();
                railBtn.focus();
            }
        });

        menu.querySelectorAll('a.shell-menu-item').forEach((link) => {
            link.addEventListener('click', () => close());
        });

        window.addEventListener('resize', () => {
            if (isOpen) positionMenu();
        });

        return { init() {}, open, close, toggle };
    })();


    // ==========================================================
    // 5. NAVBAR CONTROLLER
    // ==========================================================
    const NavbarController = (() => {
        const navbar = document.getElementById('shellNavbar');
        if (!navbar) return { init() {} };

        let ticking = false;
        function onScroll() {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => {
                navbar.classList.toggle('scrolled', window.scrollY > 8);
                ticking = false;
            });
        }
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
        return { init() {} };
    })();


    // ==========================================================
    // 5b. GREETING CONTROLLER (time-aware)
    // ==========================================================
    const GreetingController = (() => {
        const el = document.getElementById('shellGreetingLine');
        if (!el) return { init() {} };

        function greet() {
            const h = new Date().getHours();
            if (h < 12) return 'Good morning';
            if (h < 17) return 'Good afternoon';
            if (h < 21) return 'Good evening';
            return 'Good night';
        }

        function update() {
            el.textContent = greet();
        }

        let intervalId = null;

        function init() {
            update();
            intervalId = setInterval(update, 60000);
        }

        return { init };
    })();


    // ==========================================================
    // 6. KEYBOARD SHORTCUTS
    // ==========================================================
    (function Shortcuts() {
        function isTyping(el) {
            if (!el) return false;
            const tag = el.tagName;
            return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                ProfileMenuController.close && ProfileMenuController.close();
                RailController.close && RailController.close();
                TooltipEngine.hide();
                RailTooltipController.hide();
                return;
            }

            // '[' — toggle rail collapse (desktop only)
            if (e.key === '[' &&
                !isTyping(document.activeElement) &&
                !e.metaKey && !e.ctrlKey && !e.altKey) {
                if (!window.matchMedia('(max-width: 991px)').matches) {
                    e.preventDefault();
                    RailCollapseController.toggle && RailCollapseController.toggle();
                    TooltipEngine.hide();
                    RailTooltipController.hide();
                }
            }
        });
    })();


    // ==========================================================
    // 7. NOTIFICATIONS
    // ==========================================================
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

        fetch('/custom-admin/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok: ' + response.status);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (badge) {
                    badge.classList.add('hidden');
                    badge.textContent = '0';
                    badge.classList.remove('pulse');
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

    window.confirmMarkAllRead = function () {
        const badge = document.getElementById('notificationBadge');
        if (badge && (badge.textContent === '0' || badge.textContent === '')) return;

        if (window.showConfirmation) {
            window.showConfirmation(
                'Are you sure you want to mark all notifications as read? This action cannot be undone.',
                function () { performMarkAllRead(); }
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

        fetch('/custom-admin/notifications/get/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok: ' + response.status);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (badge) {
                    if (data.count > 0) {
                        badge.classList.remove('hidden');
                        badge.textContent = data.count;
                    } else {
                        badge.classList.add('hidden');
                        badge.textContent = '0';
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


    // ==========================================================
    // 8. TOASTS
    // ==========================================================
    const ToastController = (() => {
        const container = document.getElementById('toastContainer');

        function remove(toast) {
            if (!toast || toast.classList.contains('removing')) return;
            if (toast._timeout) clearTimeout(toast._timeout);
            toast.classList.add('removing');
            setTimeout(function () {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 400);
        }

        function show(message, type = 'info', title = null) {
            if (!container) return;
            const types = {
                success: { icon: 'fa-circle-check', title: 'Success' },
                error:   { icon: 'fa-circle-xmark', title: 'Error' },
                warning: { icon: 'fa-triangle-exclamation', title: 'Warning' },
                info:    { icon: 'fa-circle-info', title: 'Info' }
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
            toast.querySelector('.toast-close-btn').addEventListener('click', function (e) {
                e.stopPropagation();
                remove(toast);
            });
            toast._timeout = setTimeout(function () { remove(toast); }, 5000);
            container.appendChild(toast);
        }

        return { show, remove };
    })();

    window.showToast = ToastController.show;


    // ==========================================================
    // 9. CONFIRMATION MODAL
    // ==========================================================
    const ConfirmationController = (() => {
        let modalInstance = null;

        function show(message, onConfirm) {
            const confirmModal = document.getElementById('confirmModal');
            const confirmBody = document.getElementById('confirmModalBody');
            const confirmYesBtn = document.getElementById('confirmModalYesBtn');
            if (!confirmModal || !confirmBody || !confirmYesBtn) return;

            confirmBody.textContent = message;

            if (!modalInstance) {
                modalInstance = new bootstrap.Modal(confirmModal);
            }
            modalInstance.show();

            const newYesBtn = confirmYesBtn.cloneNode(true);
            confirmYesBtn.parentNode.replaceChild(newYesBtn, confirmYesBtn);
            newYesBtn.addEventListener('click', function () {
                modalInstance.hide();
                if (typeof onConfirm === 'function') onConfirm();
            });
        }

        return { show };
    })();

    window.showConfirmation = ConfirmationController.show;


    // ==========================================================
    // 10. BOOT
    // ==========================================================
    function boot() {
        TooltipEngine.bind();
        RailController.init();
        RailCollapseController.init();
        RailTooltipController.init();
        ProfileMenuController.init();
        NavbarController.init();
        GreetingController.init();

        const djangoMessagesContainer = document.getElementById('djangoMessages');
        if (djangoMessagesContainer) {
            djangoMessagesContainer.querySelectorAll('.django-message').forEach(function (el) {
                const message = el.getAttribute('data-message');
                const type = el.getAttribute('data-type');
                if (message) window.showToast(message, type);
            });
            djangoMessagesContainer.remove();
        }

        let tooltipRefreshTimer = null;
        const observer = new MutationObserver(() => {
            clearTimeout(tooltipRefreshTimer);
            tooltipRefreshTimer = setTimeout(() => TooltipEngine.refresh(), 150);
        });
        observer.observe(document.body, { childList: true, subtree: true });

        const menuTheme = document.getElementById('shellThemeToggleInMenu');
        if (menuTheme) {
            menuTheme.addEventListener('click', () => {
                TooltipEngine.hide();
                ThemeController.toggle();
            });
        }

        const isAdmin = document.getElementById('notificationDropdown') !== null;
        if (isAdmin) {
            setTimeout(refreshNotifications, 2000);
            setInterval(refreshNotifications, 30000);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }


    // ==========================================================
    // 11. PUBLIC API
    // ==========================================================
    window.GPLASTShell = {
        tooltips: TooltipEngine,
        rail: RailController,
        railCollapse: RailCollapseController,
        railTooltip: RailTooltipController,
        profileMenu: ProfileMenuController,
        theme: ThemeController,
        toasts: ToastController,
        confirm: ConfirmationController,
        greeting: GreetingController,
        refreshNotifications,
    };
})();