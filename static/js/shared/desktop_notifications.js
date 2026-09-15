/*
 * GPLAST Desktop Notification Engine
 * ----------------------------------
 * Polls /notifications/poll/ and turns new rows into native
 * Windows toasts (Chrome / Edge / Firefox).
 *
 * Click a toast -> focuses browser and opens the ticket.
 */

(function () {
    'use strict';

    var POLL_VISIBLE_MS = 30000;   // 30s when tab is visible
    var POLL_HIDDEN_MS  = 120000;  // 120s when tab is hidden
    var POLL_URL        = '/notifications/poll/';
    var ICON_URL        = '/static/images/logo.png';

    var lastId   = 0;
    var timer    = null;
    var inFlight = false;
    var started  = false;

    // ---------------------------------------------------------
    // Permission
    // ---------------------------------------------------------
    function hasPermission() {
        return ('Notification' in window) && Notification.permission === 'granted';
    }

    function requestPermission() {
        if (!('Notification' in window)) {
            console.info('[GPLAST] Notifications API not supported in this browser.');
            return;
        }
        if (Notification.permission === 'granted') {
            start();
            return;
        }
        if (Notification.permission === 'denied') {
            console.info('[GPLAST] Notification permission previously denied.');
            return;
        }
        Notification.requestPermission().then(function (perm) {
            if (perm === 'granted') {
                console.info('[GPLAST] Notification permission granted.');
                start();
            } else {
                console.info('[GPLAST] Notification permission not granted.');
            }
        });
    }

    // ---------------------------------------------------------
    // Show one toast
    // ---------------------------------------------------------
    function showToast(item) {
        if (!hasPermission()) return;

        try {
            var n = new Notification(item.title || 'GPLAST Ticket', {
                body: item.body || '',
                tag: 'gplast-notif-' + item.id,
                icon: ICON_URL,
                silent: false
            });

            n.onclick = function () {
                try {
                    window.focus();
                } catch (e) {}
                if (item.url) {
                    window.location.href = item.url;
                }
                n.close();
            };

            // Auto-close after 10s so Windows Action Center doesn't fill up
            setTimeout(function () {
                try { n.close(); } catch (e) {}
            }, 10000);

        } catch (e) {
            console.warn('[GPLAST] Toast failed:', e);
        }
    }

    // ---------------------------------------------------------
    // Poll
    // ---------------------------------------------------------
    function poll() {
        if (inFlight) return;
        if (!hasPermission()) return;

        inFlight = true;
        var url = POLL_URL + '?since=' + encodeURIComponent(lastId);

        fetch(url, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data && Array.isArray(data.notifications)) {
                    data.notifications.forEach(showToast);
                }
                if (data && typeof data.last_id === 'number' && data.last_id > lastId) {
                    lastId = data.last_id;
                }
            })
            .catch(function (e) {
                if (window.console && console.debug) {
                    console.debug('[GPLAST] Poll failed:', e);
                }
            })
            .finally(function () {
                inFlight = false;
            });
    }

    // ---------------------------------------------------------
    // Scheduling
    // ---------------------------------------------------------
    function schedule() {
        if (timer) clearTimeout(timer);
        var delay = document.hidden ? POLL_HIDDEN_MS : POLL_VISIBLE_MS;
        timer = setTimeout(function () {
            poll();
            schedule();
        }, delay);
    }

    function start() {
        if (started) return;
        started = true;
        poll();
        schedule();
    }

    // ---------------------------------------------------------
    // React to tab visibility changes
    // ---------------------------------------------------------
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden && hasPermission()) {
            poll();
            schedule();
        }
    });

    // ---------------------------------------------------------
    // Boot
    // ---------------------------------------------------------
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', requestPermission);
    } else {
        requestPermission();
    }
})();