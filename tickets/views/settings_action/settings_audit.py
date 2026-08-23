# tickets/views/settings_actions/settings_audit.py

"""
Settings Audit Log - Helper function for logging settings changes
"""
import logging

from tickets.models import SettingsAuditLog
from ..utils import get_client_ip

logger = logging.getLogger(__name__)


def log_settings_change(request, action_type, setting_type, setting_name, 
                        old_value=None, new_value=None, change_summary=None, remarks=None):
    """
    Helper function to log settings changes
    
    Parameters:
    - request: Django request object
    - action_type: CREATE, UPDATE, DELETE, TOGGLE, LOGIN, LOGOUT
    - setting_type: UNIT, DEPARTMENT, EMPLOYEE, CREDENTIAL, CONTACT, EMAIL, PASSWORD, SCREEN, GENERAL
    - setting_name: Name of the setting being changed
    - old_value: Previous value (optional)
    - new_value: New value (optional)
    - change_summary: Summary of changes (optional)
    - remarks: Additional remarks (optional)
    """
    try:
        SettingsAuditLog.objects.create(
            performed_by=request.user if request.user.is_authenticated else None,
            performed_by_name=request.user.username if request.user.is_authenticated else 'System',
            action_type=action_type,
            setting_type=setting_type,
            setting_name=setting_name,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            change_summary=change_summary or '',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            remarks=remarks or '',
        )
    except Exception as e:
        logger.error(f"Failed to log settings change: {str(e)}")