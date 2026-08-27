# tickets/utils.py

"""
Utility functions for tickets app
"""
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


# ============================================================
# USER ROLE CHECKS
# ============================================================

def is_admin(user):
    """
    Check if user is a superuser/admin
    """
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff


def is_employee(user):
    """
    Check if user is an employee (not admin, not unit head)
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return False
    # Check if user is a unit head
    from tickets.models import UnitHead
    if UnitHead.objects.filter(user=user, is_active=True).exists():
        return False
    return True


def is_unit_head(user):
    """
    Check if user is a unit head
    """
    if not user.is_authenticated:
        return False
    from tickets.models import UnitHead
    return UnitHead.objects.filter(user=user, is_active=True).exists()


def get_user_role(user):
    """
    Get user's role: 'admin', 'unit_head', or 'employee'
    """
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return 'admin'
    if is_unit_head(user):
        return 'unit_head'
    return 'employee'


# ============================================================
# IP ADDRESS UTILITY
# ============================================================

def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================
# FORMATTING UTILITIES
# ============================================================

def format_timedelta_display(timedelta):
    """
    Format timedelta for display
    """
    if not timedelta:
        return ""
    days = timedelta.days
    hours = timedelta.seconds // 3600
    minutes = (timedelta.seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def truncate_text(text, max_length=100):
    """
    Truncate text to max_length
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


# ============================================================
# EMAIL UTILITIES
# ============================================================

def send_ticket_email(subject, message, recipient_list, html_template=None, context=None):
    """
    Send email with optional HTML template
    """
    try:
        if html_template and context:
            html_message = render_to_string(html_template, context)
            plain_message = strip_tags(html_message)
        else:
            html_message = None
            plain_message = message
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def validate_attachment(file):
    """
    Validate file attachment
    """
    # Max file size: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.png', '.jpg', '.jpeg', '.gif']
    
    if file.size > MAX_FILE_SIZE:
        return False, "File size exceeds 5MB limit"
    
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {ext} not allowed"
    
    return True, "OK"


# ============================================================
# REOPEN TICKET LOGIC
# ============================================================

def reopen_ticket_logic(ticket, user, remarks=None):
    """
    Logic for reopening a ticket
    Returns (success, message)
    """
    from tickets.models import TicketHistory
    from django.utils import timezone
    
    if ticket.status != 'Closed':
        return False, "Ticket is not closed."
    
    if not ticket.can_reopen():
        return False, "Ticket cannot be reopened after 48 hours."
    
    # Reopen the ticket
    ticket.status = 'Open'
    ticket.closed_at = None
    ticket.closed_by = None
    ticket.closing_remarks = None
    ticket.main_error_type = None
    ticket.sub_error_type = None
    ticket.save()
    
    # Add history
    TicketHistory.objects.create(
        ticket=ticket,
        action=f"Reopened by {user.get_full_name() or user.username}",
        remarks=remarks or "Ticket reopened",
        performed_by=str(user.id)
    )
    
    return True, "Ticket reopened successfully."


# ============================================================
# EMPLOYEE DIRECTORY UTILITY
# ============================================================

def _get_employee_directory_data(request):
    """
    Get employee directory data with search
    """
    from tickets.models import EmployeeMaster
    
    search = request.GET.get('search', '').strip()
    
    employees = EmployeeMaster.objects.all().select_related('unit', 'department').order_by('employee_id')
    
    if search:
        employees = employees.filter(
            models.Q(employee_id__icontains=search) |
            models.Q(employee_name__icontains=search) |
            models.Q(mobile__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    return employees, search


def _get_contact_data():
    """
    Get contact data
    """
    from tickets.models import AdminContact
    return AdminContact.objects.first()


def _get_credentials_data():
    """
    Get credentials data
    """
    from tickets.models import DepartmentCredential, Unit
    
    all_credentials = DepartmentCredential.objects.all().select_related('unit', 'department').order_by('unit__code', 'department__name')
    
    credentials_by_unit = []
    for unit in Unit.objects.filter(is_active=True).order_by('code'):
        creds = all_credentials.filter(unit=unit)
        if creds.exists():
            credentials_by_unit.append({
                'unit': unit,
                'credentials': creds
            })
    
    return all_credentials, credentials_by_unit


# ============================================================
# SETTINGS AUDIT UTILITY
# ============================================================

def log_settings_change(request, action_type, setting_type, setting_name, 
                        old_value=None, new_value=None, change_summary=None, remarks=None):
    """
    Log a settings change to the audit log
    """
    from tickets.models import SettingsAuditLog
    
    try:
        performed_by = request.user if request.user.is_authenticated else None
        performed_by_name = request.user.username if request.user.is_authenticated else 'System'
        
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        SettingsAuditLog.objects.create(
            performed_by=performed_by,
            performed_by_name=performed_by_name,
            action_type=action_type,
            setting_type=setting_type,
            setting_name=setting_name[:200],
            old_value=old_value[:500] if old_value else None,
            new_value=new_value[:500] if new_value else None,
            change_summary=change_summary[:500] if change_summary else '',
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=remarks[:500] if remarks else '',
        )
    except Exception as e:
        print(f"Error logging settings change: {e}")