# tickets/views/utils.py

"""
Utility functions for views
- Admin check
- Format timedelta display
- Reopen ticket logic
- Generate admin ticket list HTML
- Get contact data
- Get employee directory data
- Get credentials data
- Unit Head helper functions
"""

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.template.loader import render_to_string
from datetime import timedelta
import logging

from tickets.models import (
    Ticket, TicketHistory, ReopenAttachment, 
    AdminContact, EmployeeMaster, DepartmentCredential,
    UnitHead
)

logger = logging.getLogger(__name__)


# ============================================================
# ADMIN CHECK
# ============================================================
def is_admin(user):
    """Check if user is a staff/admin user"""
    return user.is_authenticated and user.is_staff


# ============================================================
# UNIT HEAD CHECK FUNCTIONS
# ============================================================
def is_unit_head(user):
    """
    Check if a user is a Unit Head.
    Returns True if the user has an active UnitHead record.
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        return UnitHead.objects.filter(user=user, is_active=True).exists()
    except Exception:
        return False


def get_unit_head_unit(user):
    """
    Get the Unit object for a Unit Head user.
    Returns None if user is not a Unit Head.
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        unit_head = UnitHead.objects.filter(user=user, is_active=True).select_related('unit').first()
        return unit_head.unit if unit_head else None
    except Exception:
        return None


def get_unit_head_object(user):
    """
    Get the UnitHead object for a user.
    Returns None if user is not a Unit Head.
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        return UnitHead.objects.filter(user=user, is_active=True).first()
    except Exception:
        return None


def get_unit_head_emails(unit_id=None):
    """
    Get all active Unit Head email addresses.
    If unit_id is provided, only return the Unit Head for that unit.
    """
    try:
        queryset = UnitHead.objects.filter(is_active=True)
        
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        
        return list(queryset.values_list('email', flat=True))
    except Exception:
        return []


# ============================================================
# ROLE BASED REDIRECT
# ============================================================
def get_user_dashboard_url(user):
    """
    Get the appropriate dashboard URL based on user role.
    Priority: Admin > Unit Head > Employee
    """
    if not user or not user.is_authenticated:
        return '/login/'
    
    if user.is_staff:
        return '/custom-admin/dashboard/'
    
    if is_unit_head(user):
        return '/unit-head/dashboard/'
    
    return '/dashboard/'


# ============================================================
# FORMAT TIMEDELTA DISPLAY
# ============================================================
def format_timedelta_display(td):
    """
    Convert timedelta to human readable string
    Example: 2d 5h 30m
    """
    if not td:
        return ''
    
    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return ' '.join(parts) if parts else '0m'


# ============================================================
# REOPEN TICKET LOGIC
# ============================================================
def reopen_ticket_logic(ticket, performed_by, remarks, uploaded_files=None):
    """
    Reopen a closed ticket with attachments
    """
    with transaction.atomic():
        # Reset ticket status
        ticket.status = 'Open'
        ticket.closed_at = None
        ticket.closed_by = None
        ticket.closing_remarks = ''
        ticket.save()
        
        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            action="Ticket Reopened",
            remarks=remarks,
            performed_by=performed_by
        )
        
        # Save attachments
        if uploaded_files:
            for file in uploaded_files:
                ReopenAttachment.objects.create(
                    ticket=ticket,
                    file=file,
                    uploaded_by=performed_by
                )
        
        logger.info(f"Ticket {ticket.ticket_number} reopened by {performed_by}")
        return True


# ============================================================
# GENERATE ADMIN TICKET LIST HTML
# ============================================================
def generate_admin_ticket_list_html(tickets, filter_value):
    """
    Generate HTML for admin ticket list (fallback when template fails)
    """
    if not tickets:
        return '<p class="text-muted">No tickets found.</p>'
    
    html = '<div class="table-responsive"><table class="table table-sm">'
    html += """
    <thead>
        <tr>
            <th>Ticket #</th>
            <th>Subject</th>
            <th>Unit</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Created</th>
        </tr>
    </thead>
    <tbody>
    """
    
    for ticket in tickets:
        status_color = {
            'Open': 'success',
            'Assigned': 'primary',
            'Hold': 'warning',
            'Escalated': 'danger',
            'Closed': 'secondary'
        }.get(ticket.status, 'secondary')
        
        html += f"""
        <tr>
            <td><a href="/custom-admin/ticket/{ticket.id}/">{ticket.ticket_number}</a></td>
            <td>{ticket.subject}</td>
            <td>{ticket.unit.code if ticket.unit else '-'}</td>
            <td><span class="badge bg-{status_color}">{ticket.status}</span></td>
            <td><span class="badge bg-{ticket.priority.lower()}">{ticket.priority}</span></td>
            <td>{ticket.created_at.strftime('%d-%b-%Y %H:%M') if ticket.created_at else '-'}</td>
        </tr>
        """
    
    html += '</tbody></table></div>'
    return html


# ============================================================
# GET CONTACT DATA
# ============================================================
def _get_contact_data():
    """
    Get or create AdminContact record
    """
    contact, created = AdminContact.objects.get_or_create(
        id=1,
        defaults={
            'admin_name': 'GPLAST Support',
            'admin_phone': '+91-1234567890',
            'admin_email': 'erpimd@gplast.com'
        }
    )
    return contact


# ============================================================
# GET EMPLOYEE DIRECTORY DATA
# ============================================================
def _get_employee_directory_data(request):
    """
    Get employee list with search filtering
    Returns: (queryset, search_term)
    """
    emp_search = request.GET.get('emp_search', '').strip()
    
    if emp_search:
        employees = EmployeeMaster.objects.filter(
            Q(employee_id__icontains=emp_search) |
            Q(employee_name__icontains=emp_search) |
            Q(mobile__icontains=emp_search) |
            Q(email__icontains=emp_search)
        ).order_by('employee_id')
    else:
        employees = EmployeeMaster.objects.all().order_by('employee_id')
    
    return employees, emp_search


# ============================================================
# GET CREDENTIALS DATA
# ============================================================
def _get_credentials_data():
    """
    Get all department credentials grouped by unit
    Returns: (all_credentials, credentials_by_unit)
    """
    all_credentials = DepartmentCredential.objects.all().select_related('unit', 'department')
    
    credentials_by_unit = {}
    for cred in all_credentials:
        unit_code = cred.unit.code if cred.unit else 'Unknown'
        if unit_code not in credentials_by_unit:
            credentials_by_unit[unit_code] = []
        credentials_by_unit[unit_code].append(cred)
    
    return all_credentials, credentials_by_unit


# ============================================================
# CLIENT IP ADDRESS
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
# GET USER DISPLAY NAME
# ============================================================
def get_user_display_name(user):
    """
    Get formatted display name for a user
    """
    if not user:
        return 'Unknown'
    
    if user.get_full_name():
        return user.get_full_name()
    
    return user.username


# ============================================================
# CHECK TICKET OWNERSHIP
# ============================================================
def user_can_view_ticket(user, ticket):
    """
    Check if a user can view a ticket based on their role
    """
    if not user or not user.is_authenticated:
        return False
    
    # Admin can view all tickets
    if user.is_staff:
        return True
    
    # Unit Head can view tickets from their unit
    if is_unit_head(user):
        unit = get_unit_head_unit(user)
        if unit and ticket.unit == unit:
            return True
        return False
    
    # Employee can view tickets they created or are assigned to
    if ticket.created_by_user == user:
        return True
    
    if ticket.assigned_person and ticket.assigned_person.lower() in user.username.lower():
        return True
    
    return False


# ============================================================
# CHECK TICKET UPDATE PERMISSION
# ============================================================
def user_can_update_ticket(user, ticket):
    """
    Check if a user can update a ticket based on their role
    """
    if not user or not user.is_authenticated:
        return False
    
    # Admin can update all tickets
    if user.is_staff:
        return True
    
    # Unit Head can update tickets from their unit
    if is_unit_head(user):
        unit = get_unit_head_unit(user)
        if unit and ticket.unit == unit:
            return True
        return False
    
    # Employee can only update tickets they created
    if ticket.created_by_user == user:
        return True
    
    return False


# ============================================================
# FILTER TICKETS BY USER ROLE
# ============================================================
def filter_tickets_by_role(user, queryset):
    """
    Filter a ticket queryset based on user role
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    # Admin sees all tickets
    if user.is_staff:
        return queryset
    
    # Unit Head sees only their unit's tickets
    if is_unit_head(user):
        unit = get_unit_head_unit(user)
        if unit:
            return queryset.filter(unit=unit)
        return queryset.none()
    
    # Employee sees their own tickets and assigned tickets
    return queryset.filter(
        Q(created_by_user=user) |
        Q(assigned_person__icontains=user.username)
    ).distinct()