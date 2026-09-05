// ============================================================
// TOAST NOTIFICATION TEST FUNCTIONS
// ============================================================

function testSuccess() {
    if (window.showToast) {
        window.showToast('Operation completed successfully! All changes have been saved.', 'success', 'Success');
    } else {
        alert('Toast function not available. Make sure base.html is loaded correctly.');
    }
}

function testError() {
    if (window.showToast) {
        window.showToast('An error occurred while processing your request. Please try again later.', 'error', 'Error');
    } else {
        alert('Toast function not available. Make sure base.html is loaded correctly.');
    }
}

function testWarning() {
    if (window.showToast) {
        window.showToast('Please review your input before submitting. Some fields may contain invalid data.', 'warning', 'Warning');
    } else {
        alert('Toast function not available. Make sure base.html is loaded correctly.');
    }
}

function testInfo() {
    if (window.showToast) {
        window.showToast('Your session will expire in 5 minutes. Please save your work.', 'info', 'Session Expiring');
    } else {
        alert('Toast function not available. Make sure base.html is loaded correctly.');
    }
}

function testLongMessage() {
    if (window.showToast) {
        window.showToast(
            'This is a very long notification message to test how the toast handles multiple lines of text. It should wrap properly and not overflow the container.',
            'info',
            'Long Message Test'
        );
    } else {
        alert('Toast function not available. Make sure base.html is loaded correctly.');
    }
}

function testMultiple() {
    if (!window.showToast) {
        alert('Toast function not available. Make sure base.html is loaded correctly.');
        return;
    }

    var messages = [
        { msg: 'Ticket #1001 created successfully!', type: 'success', title: 'Created' },
        { msg: 'Ticket #1001 assigned to John Doe', type: 'info', title: 'Assigned' },
        { msg: 'Ticket #1002 requires attention', type: 'warning', title: 'Attention' },
        { msg: 'Failed to process ticket #1003', type: 'error', title: 'Error' },
        { msg: 'Report generated successfully!', type: 'success', title: 'Report Ready' }
    ];
    
    messages.forEach(function(item, index) {
        setTimeout(function() {
            window.showToast(item.msg, item.type, item.title);
        }, index * 600);
    });
}

function clearAllNotifications() {
    var container = document.getElementById('toastContainer');
    if (!container) return;
    
    var toasts = container.querySelectorAll('.toast-custom');
    toasts.forEach(function(toast) {
        if (toast._timeout) {
            clearTimeout(toast._timeout);
        }
        toast.classList.add('removing');
        setTimeout(function() {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 400);
    });
    
    setTimeout(function() {
        if (window.showToast) {
            window.showToast('All notifications cleared!', 'success', 'Cleared');
        }
    }, 500);
}

// ============================================================
// NOTIFICATION API FUNCTIONS - FIXED URLS
// ============================================================

// ✅ FIXED: Use correct URL with custom-admin prefix
var NOTIFICATION_GET_URL = '/custom-admin/notifications/get/';
var NOTIFICATION_MARK_ALL_READ_URL = '/custom-admin/notifications/mark-all-read/';
var NOTIFICATION_MARK_READ_URL = '/custom-admin/notifications/mark-read/';

function getCSRFToken() {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Refresh notifications from server
 * ✅ FIXED: Uses /custom-admin/notifications/get/
 */
window.refreshNotifications = function() {
    var badge = document.getElementById('notificationBadge');
    if (!badge) return;

    fetch(NOTIFICATION_GET_URL, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }
        return response.json();
    })
    .then(function(data) {
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
            
            var itemsContainer = document.getElementById('notificationItems');
            if (itemsContainer && data.html) {
                itemsContainer.innerHTML = data.html;
            }
        }
    })
    .catch(function(error) {
        console.error('Error refreshing notifications:', error);
    });
};

/**
 * Mark all notifications as read
 * ✅ FIXED: Uses /custom-admin/notifications/mark-all-read/
 */
window.performMarkAllRead = function() {
    var badge = document.getElementById('notificationBadge');
    var itemsContainer = document.getElementById('notificationItems');
    
    fetch(NOTIFICATION_MARK_ALL_READ_URL, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }
        return response.json();
    })
    .then(function(data) {
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
            
            if (window.showToast) {
                window.showToast('All notifications marked as read!', 'success', 'All Read');
            }
        }
    })
    .catch(function(error) {
        console.error('Error marking all as read:', error);
        if (window.showToast) {
            window.showToast('Failed to mark all as read. Please try again.', 'error', 'Error');
        }
    });
};

/**
 * Confirm mark all as read
 */
window.confirmMarkAllRead = function() {
    var badge = document.getElementById('notificationBadge');
    if (badge && (badge.textContent === '0' || badge.textContent === '' || badge.classList.contains('hidden'))) {
        if (window.showToast) {
            window.showToast('No notifications to mark as read.', 'info', 'Info');
        }
        return;
    }
    
    if (window.showConfirmation) {
        window.showConfirmation(
            'Are you sure you want to mark all notifications as read? This action cannot be undone.',
            function() {
                window.performMarkAllRead();
            }
        );
    } else {
        if (confirm('Are you sure you want to mark all notifications as read?')) {
            window.performMarkAllRead();
        }
    }
};

/**
 * Mark individual notification as read
 * ✅ FIXED: Uses /custom-admin/notifications/mark-read/{id}/
 */
window.markNotificationRead = function(notificationId) {
    fetch(NOTIFICATION_MARK_READ_URL + notificationId + '/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.status);
        }
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            window.refreshNotifications();
        }
    })
    .catch(function(error) {
        console.error('Error marking notification as read:', error);
    });
};

console.log('✅ Test Notifications JS loaded with fixed URLs');
console.log('🔔 Notification GET URL:', NOTIFICATION_GET_URL);
console.log('🔔 Mark All Read URL:', NOTIFICATION_MARK_ALL_READ_URL);
console.log('🔔 Mark Read URL:', NOTIFICATION_MARK_READ_URL);