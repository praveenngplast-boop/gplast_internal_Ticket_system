# tickets/views/settings_action/settings_audit.py

"""
Settings Audit Log - Helper function for logging settings changes.
"""

import logging

from tickets.models import SettingsAuditLog
from ..utils import get_client_ip

logger = logging.getLogger(__name__)


def log_settings_change(request, action_type, setting_type, setting_name,
                        old_value=None, new_value=None, change_summary=None,
                        remarks=None, ip_address=None, **kwargs):
    """
    Log a settings change to the SettingsAuditLog table.

    Called by every settings module to record CREATE / UPDATE / DELETE /
    TOGGLE / LOGIN / LOGOUT actions performed by admins.

    Parameters:
    - request: Django request object
    - action_type: CREATE | UPDATE | DELETE | TOGGLE | LOGIN | LOGOUT
    - setting_type: UNIT | DEPARTMENT | EMPLOYEE | CREDENTIAL | CONTACT |
                    EMAIL | PASSWORD | SCREEN | ERROR_TYPE | ERP_MAPPING |
                    GENERAL
    - setting_name: Name of the setting being changed
    - old_value: Previous value (optional)
    - new_value: New value (optional)
    - change_summary: Short summary of the change (optional)
    - remarks: Additional remarks (optional)
    - ip_address: Optional explicit IP. Falls back to request IP.
    - **kwargs: Absorb extra keyword arguments so callers don't crash.
    """
    try:
        resolved_ip = ip_address or get_client_ip(request)

        SettingsAuditLog.objects.create(
            performed_by=request.user if request.user.is_authenticated else None,
            performed_by_name=request.user.username if request.user.is_authenticated else 'System',
            action_type=action_type,
            setting_type=setting_type,
            setting_name=setting_name,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            change_summary=change_summary or '',
            ip_address=resolved_ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            remarks=remarks or '',
        )
    except Exception as e:
        logger.error(f"Failed to log settings change: {str(e)}")