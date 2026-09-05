/* Shared ticket UI helpers used by Employee, Admin, and Unit Head pages. */
(function(window) {
    'use strict';

    function escapeHtml(value) {
        var text = value === null || value === undefined ? '' : String(value);
        var element = document.createElement('div');
        element.textContent = text;
        return element.innerHTML;
    }

    function requestJson(response) {
        if (response.redirected || response.url.indexOf('/login/') !== -1) {
            throw new Error('Your session has expired. Please login again.');
        }
        if (!response.ok) {
            throw new Error('Server returned ' + response.status);
        }
        var contentType = response.headers.get('content-type') || '';
        if (contentType.indexOf('application/json') === -1) {
            throw new Error('The ticket service returned an invalid response. Please refresh and try again.');
        }
        return response.json();
    }

    function formatDate(value) {
        if (!value) return '';
        var date = new Date(value);
        if (Number.isNaN(date.getTime())) return '';
        return date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }

    function aging(value) {
        if (!value) return { label: 'N/A', className: 'aging-unknown' };
        var createdAt = new Date(value);
        if (Number.isNaN(createdAt.getTime())) return { label: 'N/A', className: 'aging-unknown' };

        var seconds = Math.max(0, (Date.now() - createdAt.getTime()) / 1000);
        if (seconds < 60) return { label: 'Just now', className: 'aging-fresh' };
        if (seconds < 3600) return { label: Math.floor(seconds / 60) + 'm', className: 'aging-fresh' };
        if (seconds < 86400) {
            var hours = Math.floor(seconds / 3600);
            var minutes = Math.floor((seconds % 3600) / 60);
            return { label: hours + 'h' + (minutes ? ' ' + minutes + 'm' : ''), className: 'aging-medium' };
        }
        if (seconds < 2592000) {
            var days = Math.floor(seconds / 86400);
            var remainingHours = Math.floor((seconds % 86400) / 3600);
            return { label: days + 'd' + (remainingHours ? ' ' + remainingHours + 'h' : ''), className: 'aging-old' };
        }

        var months = Math.floor(seconds / 2592000);
        var remainingDays = Math.floor((seconds % 2592000) / 86400);
        return { label: months + 'mo' + (remainingDays ? ' ' + remainingDays + 'd' : ''), className: 'aging-very-old' };
    }

    function cleanupModal() {
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    function setModalState(element, state, message) {
        var icons = {
            loading: 'fa-spinner fa-spin',
            empty: 'fa-receipt',
            error: 'fa-circle-exclamation'
        };
        var text = escapeHtml(message || (state === 'loading' ? 'Loading tickets...' : 'No tickets found.'));
        element.innerHTML = '<div class="ticket-modal-state ticket-modal-state-' + state + '">' +
            '<i class="fa-solid ' + (icons[state] || icons.empty) + '"></i>' +
            '<p>' + text + '</p>' +
            '</div>';
    }

    window.TicketUI = {
        escapeHtml: escapeHtml,
        requestJson: requestJson,
        formatDate: formatDate,
        aging: aging,
        cleanupModal: cleanupModal,
        setModalState: setModalState
    };
}(window));
