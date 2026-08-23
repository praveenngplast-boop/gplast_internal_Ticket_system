# tickets/views/utils.py

"""
Utility functions used across multiple views
"""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from tickets.models import Ticket, TicketHistory, Unit, DepartmentCredential, EmployeeMaster, AdminContact
import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    """Check if user is admin (staff)"""
    return user.is_authenticated and user.is_staff


def format_timedelta_display(td):
    """Format timedelta for human readable display"""
    if not td:
        return ""
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} min{'s' if minutes > 1 else ''}")
    if not parts:
        return "< 1 minute"
    return ", ".join(parts)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def reopen_ticket_logic(ticket, performed_by, remarks, attachments=None):
    """Reopen a closed ticket with audit trail"""
    with transaction.atomic():
        ticket.status = 'Open'
        ticket.closed_by = None
        ticket.closed_at = None
        ticket.closing_remarks = None
        # ✅ Clear error type fields when reopening
        ticket.main_error_type = None
        ticket.sub_error_type = None
        ticket.save()
        TicketHistory.objects.create(
            ticket=ticket,
            action="Ticket Reopened",
            remarks=remarks,
            performed_by=performed_by
        )
    # Import here to avoid circular import
    from tickets.utils import send_ticket_email
    from tickets.models import ReopenAttachment
    reopen_attachments = []
    for uploaded_file in attachments or []:
        reopen_attachment = ReopenAttachment.objects.create(
            ticket=ticket,
            file=uploaded_file,
            uploaded_by=performed_by,
        )
        reopen_attachments.append(reopen_attachment.file)
    send_ticket_email(ticket, 'Reopened', remarks=remarks, attachments=reopen_attachments)


def generate_ticket_list_html(tickets, status):
    """Generate HTML for ticket list (Employee view)"""
    if not tickets:
        return """
        <div class="empty-state text-center py-5">
            <i class="fa-solid fa-receipt fa-3x mb-3 d-block opacity-25" style="color: var(--accent);"></i>
            <h6 style="color: var(--text-secondary); font-weight: 600;">No Tickets Found</h6>
            <p style="color: var(--text-muted); font-size: 0.85rem;">
                No tickets found.
            </p>
            <a href="javascript:void(0)" onclick="window.location.href='/create-ticket/'" class="btn btn-primary-custom btn-sm mt-2">
                <i class="fa-solid fa-circle-plus me-1"></i>Create New Ticket
            </a>
        </div>
        """
    
    html = """
    <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
            <thead>
                <tr>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Ticket</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Created</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Subject</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Status</th>
                    <th class="text-center" style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Action</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for ticket in tickets:
        status_class = ticket.status.lower()
        badge_class = {
            'open': 'badge-status-open',
            'assigned': 'badge-status-assigned',
            'hold': 'badge-status-hold',
            'escalated': 'badge-status-escalated',
            'closed': 'badge-status-closed',
        }.get(status_class, 'badge-status-open')
        
        html += f"""
                <tr>
                    <td class="fw-bold" style="color: var(--accent-light); font-size: 0.7rem;">
                        {ticket.ticket_number}
                    </td>
                    <td style="font-size: 0.65rem; color: var(--text-secondary);">
                        {ticket.created_at.strftime('%d-%m-%Y') if ticket.created_at else '-'}
                        <span class="d-block" style="font-size: 0.55rem; color: var(--text-muted);">{ticket.created_at.strftime('%I:%M %p') if ticket.created_at else ''}</span>
                    </td>
                    <td class="text-truncate" style="max-width: 120px; font-size: 0.7rem;" title="{ticket.subject}">
                        {ticket.subject}
                    </td>
                    <td>
                        <span class="badge-custom {badge_class}" style="font-size: 0.5rem; padding: 0.15rem 0.5rem;">
                            {ticket.status}
                        </span>
                    </td>
                    <td class="text-center">
                        <a href="/ticket/{ticket.id}/" class="btn-view" style="font-size: 0.6rem; padding: 0.15rem 0.6rem;">
                            <i class="fa-solid fa-eye"></i> View
                        </a>
                    </td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


def generate_admin_ticket_list_html(tickets, status):
    """Generate HTML for ticket list (Admin view) with error type display"""
    if not tickets:
        return """
        <div class="empty-state text-center py-5">
            <i class="fa-solid fa-receipt fa-3x mb-3 d-block opacity-25" style="color: var(--accent);"></i>
            <h6 style="color: var(--text-secondary); font-weight: 600;">No Tickets Found</h6>
            <p style="color: var(--text-muted); font-size: 0.85rem;">
                No tickets found.
            </p>
        </div>
        """
    
    html = """
    <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
            <thead>
                <tr>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Ticket</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Created</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Unit</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Subject</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Status</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Priority</th>
                    <th style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Error Type</th>
                    <th class="text-center" style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-secondary);">Action</th>
                </tr>
            </thead>
            <tbody>
    """
    
    badge_class_map = {
        'open': 'badge-status-open',
        'assigned': 'badge-status-assigned',
        'hold': 'badge-status-hold',
        'escalated': 'badge-status-escalated',
        'closed': 'badge-status-closed',
    }
    
    priority_class_map = {
        'critical': 'badge-priority-critical',
        'high': 'badge-priority-high',
        'medium': 'badge-priority-medium',
        'low': 'badge-priority-low',
    }
    
    for ticket in tickets:
        status_class = ticket.status.lower()
        badge_class = badge_class_map.get(status_class, 'badge-status-open')
        priority_class = priority_class_map.get(ticket.priority.lower(), 'badge-priority-low')
        
        # ✅ Get error type display - show main_error_type if available, else error_type
        if ticket.main_error_type and ticket.sub_error_type:
            error_display = f"{ticket.main_error_type}<br><small style='font-size:0.5rem;color:var(--text-muted);'>{ticket.sub_error_type}</small>"
        elif ticket.error_type:
            error_display = ticket.error_type
        else:
            error_display = '-'
        
        html += f"""
                <tr>
                    <td class="fw-bold" style="color: var(--accent-light); font-size: 0.7rem;">
                        {ticket.ticket_number}
                    </td>
                    <td style="font-size: 0.65rem; color: var(--text-secondary);">
                        {ticket.created_at.strftime('%d-%m-%Y') if ticket.created_at else '-'}
                        <span class="d-block" style="font-size: 0.55rem; color: var(--text-muted);">{ticket.created_at.strftime('%I:%M %p') if ticket.created_at else ''}</span>
                    </td>
                    <td style="font-size: 0.65rem; color: var(--text-secondary);">
                        <span class="unit-badge" style="background: rgba(233,69,96,0.1); color: var(--accent); border: 1px solid rgba(233,69,96,0.15); padding: 0.15rem 0.5rem; border-radius: 50px; font-size: 0.6rem; font-weight: 600;">{ticket.unit.code if ticket.unit else '-'}</span>
                    </td>
                    <td class="text-truncate" style="max-width: 100px; font-size: 0.7rem;" title="{ticket.subject}">
                        {ticket.subject}
                    </td>
                    <td>
                        <span class="badge-custom {badge_class}" style="font-size: 0.5rem; padding: 0.15rem 0.5rem;">
                            {ticket.status}
                        </span>
                    </td>
                    <td>
                        <span class="badge-priority {priority_class}" style="font-size: 0.5rem; padding: 0.15rem 0.5rem;">
                            <i class="fa-solid fa-flag" style="font-size: 0.3rem;"></i>
                            {ticket.priority}
                        </span>
                    </td>
                    <td style="font-size: 0.6rem;">
                        {error_display}
                    </td>
                    <td class="text-center">
                        <a href="/admin/ticket/{ticket.id}/" class="btn-view" style="font-size: 0.6rem; padding: 0.15rem 0.6rem; background: var(--accent-gradient); color: white; border-radius: 50px; text-decoration: none; display: inline-block;">
                            <i class="fa-solid fa-eye"></i> View
                        </a>
                    </td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


def get_contact_data():
    """Get or create admin contact data"""
    contact_obj, created = AdminContact.objects.get_or_create(
        id=1,
        defaults={
            'admin_name': "IT ADMIN",
            'admin_phone': "9999999999",
            'admin_email': "admin@gplast.com",
        }
    )
    return contact_obj


# ✅ Alias for backward compatibility
_get_contact_data = get_contact_data


def get_employee_directory_data(request):
    """Get employee directory data with search"""
    emp_search = request.GET.get('emp_search', '').strip()
    employees_qs = EmployeeMaster.objects.select_related('unit', 'department').all().order_by('employee_id')
    if emp_search:
        employees_qs = employees_qs.filter(
            Q(employee_id__icontains=emp_search) |
            Q(employee_name__icontains=emp_search) |
            Q(mobile__icontains=emp_search) |
            Q(email__icontains=emp_search) |
            Q(unit__code__icontains=emp_search) |
            Q(unit__full_name__icontains=emp_search) |
            Q(department__name__icontains=emp_search)
        )
    return employees_qs, emp_search


# ✅ Alias for backward compatibility
_get_employee_directory_data = get_employee_directory_data


def get_credentials_data():
    """Get department credentials grouped by unit"""
    all_credentials = DepartmentCredential.objects.select_related('unit', 'department').order_by('unit__code', 'department__name')
    credentials_by_unit = []
    
    for unit in Unit.objects.filter(is_active=True).order_by('code'):
        unit_creds = all_credentials.filter(unit=unit)
        if unit_creds.exists():
            credentials_by_unit.append({
                'unit': unit, 
                'credentials': unit_creds
            })
    
    for unit in Unit.objects.filter(is_active=False).order_by('code'):
        unit_creds = all_credentials.filter(unit=unit)
        if unit_creds.exists():
            credentials_by_unit.append({
                'unit': unit, 
                'credentials': unit_creds
            })
    
    return all_credentials, credentials_by_unit


# ✅ Alias for backward compatibility
_get_credentials_data = get_credentials_data


def is_ajax(request):
    """Check if request is AJAX"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax', False)


def get_paginated_queryset(queryset, page_number, per_page=20):
    """
    Get paginated queryset with proper error handling
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(queryset, per_page)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj


def get_ticket_status_color(status):
    """Get color class for ticket status"""
    color_map = {
        'Open': 'success',
        'Assigned': 'info',
        'Hold': 'warning',
        'Escalated': 'danger',
        'Closed': 'secondary',
    }
    return color_map.get(status, 'secondary')


def get_ticket_priority_color(priority):
    """Get color class for ticket priority"""
    color_map = {
        'Critical': 'danger',
        'High': 'warning',
        'Medium': 'info',
        'Low': 'secondary',
    }
    return color_map.get(priority, 'secondary')


# ============================================================
# ✅ NEW UTILITY FUNCTIONS FOR ERROR TYPES
# ============================================================

def get_error_type_display(ticket):
    """
    Get formatted error type display for a ticket
    Returns HTML string with main and sub error types
    """
    if ticket.main_error_type and ticket.sub_error_type:
        return f"{ticket.main_error_type} → {ticket.sub_error_type}"
    elif ticket.main_error_type:
        return ticket.main_error_type
    elif ticket.error_type:
        return ticket.error_type
    return "Not Set"


def get_error_type_badge(ticket):
    """
    Get HTML badge for error type display
    Returns HTML string with styled badge
    """
    if ticket.main_error_type and ticket.sub_error_type:
        color = '#8B5CF6' if ticket.main_error_type == 'Roadmap Error' else '#10B981'
        return f"""
            <span style="display:inline-block;background:{color}15;color:{color};padding:0.1rem 0.5rem;border-radius:50px;font-size:0.5rem;font-weight:600;border:1px solid {color}20;">
                {ticket.main_error_type}
                <span style="font-weight:400;opacity:0.7;">→</span>
                {ticket.sub_error_type}
            </span>
        """
    elif ticket.main_error_type:
        color = '#8B5CF6' if ticket.main_error_type == 'Roadmap Error' else '#10B981'
        return f"""
            <span style="display:inline-block;background:{color}15;color:{color};padding:0.1rem 0.5rem;border-radius:50px;font-size:0.5rem;font-weight:600;border:1px solid {color}20;">
                {ticket.main_error_type}
            </span>
        """
    elif ticket.error_type:
        return f"""
            <span style="display:inline-block;background:#E8EDF5;color:#4A5A7A;padding:0.1rem 0.5rem;border-radius:50px;font-size:0.5rem;font-weight:600;border:1px solid #DCE3F0;">
                {ticket.error_type}
            </span>
        """
    return f"""
        <span style="display:inline-block;color:#8A9AB8;padding:0.1rem 0.5rem;border-radius:50px;font-size:0.5rem;font-weight:400;">
            Not Set
        </span>
    """


def has_closing_error_details(ticket):
    """Check if ticket has closing error details"""
    return bool(ticket.main_error_type and ticket.sub_error_type)


def get_sub_error_choices(main_error_type):
    """
    Get sub-error choices based on main error type
    Returns list of tuples for form choices
    """
    if main_error_type == 'Roadmap Error':
        return [
            ('Database Error', 'Database Error'),
            ('Logic / Functional Error', 'Logic / Functional Error'),
            ('Application Error', 'Application Error'),
            ('Calculation Error', 'Calculation Error'),
            ('Report / Print Error', 'Report / Print Error'),
            ('Workflow / Approval Error', 'Workflow / Approval Error'),
            ('Integration / API Error', 'Integration / API Error'),
            ('Barcode Error', 'Barcode Error'),
            ('Performance Error', 'Performance Error'),
            ('Access / Permission Error', 'Access / Permission Error'),
            ('Master Data / Configuration Error', 'Master Data / Configuration Error'),
            ('Other ERP Error', 'Other ERP Error'),
        ]
    elif main_error_type == 'GPL Error':
        return [
            ('User / Data Entry Error', 'User / Data Entry Error'),
            ('Process / Procedure Error', 'Process / Procedure Error'),
            ('Master Data Error', 'Master Data Error'),
            ('Other GPL Error', 'Other GPL Error'),
        ]
    return []


def get_error_type_stats(tickets_qs):
    """
    Get error type statistics from a queryset
    Returns dictionary with main_error_type and sub_error_type counts
    """
    main_error_stats = (
        tickets_qs
        .exclude(main_error_type__isnull=True)
        .exclude(main_error_type__exact='')
        .values('main_error_type')
        .annotate(count=models.Count('id'))
        .order_by('-count')
    )
    
    sub_error_stats = (
        tickets_qs
        .exclude(sub_error_type__isnull=True)
        .exclude(sub_error_type__exact='')
        .values('sub_error_type')
        .annotate(count=models.Count('id'))
        .order_by('-count')
    )
    
    return {
        'main_errors': main_error_stats,
        'sub_errors': sub_error_stats,
    }