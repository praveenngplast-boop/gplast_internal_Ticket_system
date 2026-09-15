# tickets/views/employee_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from datetime import timedelta, datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from tickets.models import (
    Ticket, 
    Unit, 
    Department, 
    AdminContact,           
    AdminNotificationEmail, 
    EmployeeMaster,         
    TicketHistory,
    TicketReply,
    ReopenAttachment,
    SettingsAuditLog,
    DepartmentCredential,
    ScreenMaster,
)
from tickets.forms import TicketForm, TicketReplyForm
from tickets.utils import send_ticket_email, validate_attachment
import logging

logger = logging.getLogger(__name__)


def get_reply_text(reply):
    """Extract reply text from a TicketReply instance."""
    if not reply:
        return ''
    for field in ['reply', 'reply_text', 'message', 'text', 'content', 'comment', 'body', 'description']:
        if hasattr(reply, field):
            value = getattr(reply, field)
            if value:
                return str(value)
    try:
        return str(reply)
    except Exception:
        return ''


# ============================================================
# ROLE REDIRECT
# ============================================================
def role_redirect(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'employee_dashboard')
    return redirect('login')


def _employee_ticket_scope(user):
    """Return the tickets visible to a non-admin employee."""
    credential = DepartmentCredential.objects.filter(
        username=user.username,
        is_active=True,
    ).select_related('department').first()

    if credential and credential.department_id:
        return Ticket.objects.filter(department_id=credential.department_id)

    employee = EmployeeMaster.objects.filter(
        email=user.email,
        is_active=True,
    ).select_related('department').first()

    if employee and employee.department_id:
        return Ticket.objects.filter(department_id=employee.department_id)

    return Ticket.objects.filter(
        Q(created_by_user=user) |
        Q(assigned_person__icontains=user.username)
    ).distinct()


# ============================================================
# SHARED FILTER HELPER
# ============================================================
def _apply_ticket_filters(tickets, request, apply_default_closed_filter=True):
    """
    Apply the standard filter set used by all_tickets and my_tickets.

    Reads from request.GET:
      status, priority, filter, search, date_from, date_to,
      main_error_type, sub_error_type, unit, department,
      ticket_number, assigned_person

    Returns the filtered queryset.
    """
    status_filter   = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    filter_param    = request.GET.get('filter', '').strip()
    search_query    = request.GET.get('search', '').strip()
    date_from       = request.GET.get('date_from', '').strip()
    date_to         = request.GET.get('date_to', '').strip()
    main_error_type = request.GET.get('main_error_type', '').strip()
    sub_error_type  = request.GET.get('sub_error_type', '').strip()
    unit_id         = request.GET.get('unit', '').strip()
    department_id   = request.GET.get('department', '').strip()
    ticket_number   = request.GET.get('ticket_number', '').strip()
    assigned_person = request.GET.get('assigned_person', '').strip()

    # Default: hide Closed tickets older than 30 days
    if apply_default_closed_filter and not status_filter and not filter_param:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        tickets = tickets.filter(
            Q(status='Closed', closed_at__gte=thirty_days_ago) |
            ~Q(status='Closed')
        )

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)

    if filter_param and filter_param != 'all':
        if filter_param == 'Critical':
            tickets = tickets.filter(priority='Critical')
        elif filter_param in ('Open', 'Assigned', 'Hold', 'Escalated', 'Closed'):
            tickets = tickets.filter(status=filter_param)

    if main_error_type:
        tickets = tickets.filter(main_error_type=main_error_type)
    if sub_error_type and sub_error_type != 'All':
        tickets = tickets.filter(sub_error_type=sub_error_type)

    if unit_id:
        tickets = tickets.filter(unit_id=unit_id)
    if department_id:
        tickets = tickets.filter(department_id=department_id)

    if ticket_number:
        tickets = tickets.filter(ticket_number__icontains=ticket_number)

    if assigned_person:
        tickets = tickets.filter(assigned_person__icontains=assigned_person)

    if date_from:
        try:
            d = datetime.strptime(date_from, '%Y-%m-%d').date()
            from_dt = timezone.make_aware(datetime.combine(d, datetime.min.time()))
            tickets = tickets.filter(created_at__gte=from_dt)
        except ValueError:
            pass

    if date_to:
        try:
            d = datetime.strptime(date_to, '%Y-%m-%d').date()
            to_dt = timezone.make_aware(datetime.combine(d, datetime.max.time()))
            tickets = tickets.filter(created_at__lte=to_dt)
        except ValueError:
            pass

    if search_query:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(employee_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(unit__code__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )

    return tickets


# ============================================================
# EMPLOYEE DASHBOARD
# ============================================================
@login_required
def employee_dashboard(request):
    contact = AdminContact.objects.first()

    if request.user.is_staff:
        tickets = Ticket.objects.all()
    else:
        tickets = _employee_ticket_scope(request.user)

    kpis = {
        'total': tickets.count(),
        'open': tickets.filter(status='Open').count(),
        'assigned': tickets.filter(status='Assigned').count(),
        'hold': tickets.filter(status='Hold').count(),
        'escalated': tickets.filter(status='Escalated').count(),
        'closed': tickets.filter(status='Closed').count(),
        'critical': tickets.filter(priority='Critical').count(),
    }

    status_counts = list(tickets.values('status').annotate(count=Count('id')))
    charts_data = {
        'dept_status': {item['status']: item['count'] for item in status_counts},
        'dept_priority': dict(
            tickets.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
        ),
    }

    latest_tickets = tickets.order_by('-created_at')[:10]

    show_department_tickets = False
    department_name = None
    unit_name = None

    try:
        employee = EmployeeMaster.objects.filter(email=request.user.email).first()
        if employee and employee.department:
            show_department_tickets = True
            department_name = employee.department.name
            unit_name = employee.department.unit.full_name if employee.department.unit else None
    except Exception:
        pass

    return render(request, 'employee/dashboard.html', {
        'kpis': kpis,
        'charts_data': charts_data,
        'latest_tickets': latest_tickets,
        'contact': contact,
        'show_department_tickets': show_department_tickets,
        'department_name': department_name,
        'unit_name': unit_name,
    })


# ============================================================
# CREATE TICKET
# ============================================================
@login_required
def create_ticket(request):
    user_credential = None
    try:
        user_credential = DepartmentCredential.objects.filter(
            username=request.user.username,
            is_active=True,
        ).select_related('unit', 'department').first()
    except Exception as e:
        logger.error(f"Error fetching user credential: {e}")

    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)

        employee_id = request.POST.get('employee_id', '').strip().upper()
        employee = EmployeeMaster.objects.filter(employee_id=employee_id, is_active=True).first()

        if employee and user_credential:
            if employee.unit_id != user_credential.unit_id:
                messages.error(request, f'❌ Employee "{employee_id}" belongs to a different Unit.')
                form = TicketForm(initial={
                    'unit': user_credential.unit_id,
                    'department': user_credential.department_id,
                })
                return render(request, 'employee/create_ticket.html', {
                    'form': form,
                    'units': Unit.objects.filter(is_active=True),
                    'departments': Department.objects.filter(is_active=True),
                    'user_credential': user_credential,
                })

            if employee.department_id != user_credential.department_id:
                messages.error(request, f'❌ Employee "{employee_id}" belongs to a different Department.')
                form = TicketForm(initial={
                    'unit': user_credential.unit_id,
                    'department': user_credential.department_id,
                })
                return render(request, 'employee/create_ticket.html', {
                    'form': form,
                    'units': Unit.objects.filter(is_active=True),
                    'departments': Department.objects.filter(is_active=True),
                    'user_credential': user_credential,
                })

        elif not employee and employee_id:
            messages.error(request, f'❌ Employee ID "{employee_id}" not found.')
            form = TicketForm(initial={
                'unit': user_credential.unit_id if user_credential else None,
                'department': user_credential.department_id if user_credential else None,
            })
            return render(request, 'employee/create_ticket.html', {
                'form': form,
                'units': Unit.objects.filter(is_active=True),
                'departments': Department.objects.filter(is_active=True),
                'user_credential': user_credential,
            })

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by_user = request.user
            ticket.created_by_role = 'Employee'
            if user_credential:
                ticket.unit = user_credential.unit
                ticket.department = user_credential.department
            ticket.save()

            TicketHistory.objects.create(
                ticket=ticket,
                action='Created Ticket',
                remarks='Ticket created by employee',
                performed_by=request.user.username,
            )

            try:
                from tickets.services.notify import notify_ticket_created
                notify_ticket_created(ticket, actor=request.user)
            except Exception as _e:
                logger.warning(f"notify_ticket_created failed: {_e}")

            messages.success(request, f'Ticket #{ticket.ticket_number} created successfully!')
            return redirect('ticket_detail', ticket_id=ticket.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        initial_data = {}
        if user_credential:
            initial_data['unit'] = user_credential.unit_id
            initial_data['department'] = user_credential.department_id
        form = TicketForm(initial=initial_data)

    departments = Department.objects.filter(is_active=True)
    if user_credential:
        departments = departments.filter(unit_id=user_credential.unit_id)

    return render(request, 'employee/create_ticket.html', {
        'form': form,
        'units': Unit.objects.filter(is_active=True),
        'departments': departments,
        'user_credential': user_credential,
    })


# ============================================================
# ALL TICKETS - FIXED FILTERS
# ============================================================
@login_required
def all_tickets(request):
    """View all tickets with filters, AJAX, pagination, and Excel export."""
    is_ajax = request.GET.get('ajax', 'false')
    if isinstance(is_ajax, str):
        is_ajax = is_ajax.lower() in ('true', '1', 'yes')

    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'Please login to view tickets.',
                'tickets': [],
                'count': 0,
            }, status=401)
        return redirect('login')

    base_tickets = Ticket.objects.all() if request.user.is_staff else _employee_ticket_scope(request.user)

    tickets = _apply_ticket_filters(base_tickets, request, apply_default_closed_filter=True)
    tickets = tickets.order_by('-created_at').distinct()

    thirty_days_ago = timezone.now() - timedelta(days=30)
    closed_count_30_days = base_tickets.filter(
        status='Closed',
        closed_at__gte=thirty_days_ago,
    ).count()

    if request.GET.get('export') == 'excel':
        return export_filtered_tickets_excel(request, tickets)

    if is_ajax:
        try:
            tickets_list = tickets[:50]
            tickets_data = [{
                'id': t.id,
                'ticket_number': t.ticket_number,
                'subject': t.subject,
                'employee_name': t.employee_name,
                'status': t.status,
                'priority': t.priority,
                'target_date': t.target_date.isoformat() if t.target_date else None,
                'created_at': t.created_at.isoformat(),
                'unit': t.unit.code if t.unit else '',
                'department': t.department.name if t.department else '',
            } for t in tickets_list]

            return JsonResponse({
                'success': True,
                'tickets': tickets_data,
                'count': tickets.count(),
            })
        except Exception as e:
            logger.error(f"AJAX error in all_tickets: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Error loading tickets. Please try again.',
                'tickets': [],
                'count': 0,
            }, status=500)

    paginator = Paginator(tickets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'employee/all_tickets.html', {
        'page_obj': page_obj,
        'status_filter': request.GET.get('status', '').strip(),
        'priority_filter': request.GET.get('priority', '').strip(),
        'search_query': request.GET.get('search', '').strip(),
        'date_from': request.GET.get('date_from', '').strip(),
        'date_to': request.GET.get('date_to', '').strip(),
        'closed_count_30_days': closed_count_30_days,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'units': Unit.objects.filter(is_active=True),
        'departments': Department.objects.filter(is_active=True),
        'selected_main_error_type': request.GET.get('main_error_type', '').strip(),
        'selected_sub_error_type': request.GET.get('sub_error_type', '').strip(),
    })


# ============================================================
# MY TICKETS - FIXED FILTERS
# ============================================================
@login_required
def my_tickets(request):
    """View tickets created by the logged-in user with filters + Excel export."""
    base = Ticket.objects.filter(created_by_user=request.user)

    tickets = _apply_ticket_filters(base, request, apply_default_closed_filter=False)
    tickets = tickets.order_by('-created_at').distinct()

    total             = tickets.count()
    open_tickets      = tickets.filter(status='Open').count()
    assigned_tickets  = tickets.filter(status='Assigned').count()
    hold_tickets      = tickets.filter(status='Hold').count()
    escalated_tickets = tickets.filter(status='Escalated').count()
    closed_tickets    = tickets.filter(status='Closed').count()

    thirty_days_ago = timezone.now() - timedelta(days=30)
    closed_count_30_days = base.filter(
        status='Closed',
        closed_at__gte=thirty_days_ago,
    ).count()

    employees = EmployeeMaster.objects.filter(is_active=True).order_by('employee_name')

    if request.GET.get('export') == 'excel':
        return export_filtered_my_tickets_excel(request, tickets)

    is_ajax = request.GET.get('ajax', 'false')
    if isinstance(is_ajax, str):
        is_ajax = is_ajax.lower() in ('true', '1', 'yes')

    if is_ajax:
        try:
            tickets_list = tickets[:50]
            html = render_to_string('employee/_ticket_list_modal.html', {
                'tickets': tickets_list,
            }, request=request)
            return JsonResponse({'success': True, 'html': html, 'count': tickets.count()})
        except Exception as e:
            logger.error(f"AJAX error in my_tickets: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Error loading tickets. Please try again.',
                'html': '',
                'count': 0,
            }, status=500)

    paginator = Paginator(tickets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'employee/my_tickets.html', {
        'page_obj': page_obj,
        'total': total,
        'open_tickets': open_tickets,
        'assigned_tickets': assigned_tickets,
        'hold_tickets': hold_tickets,
        'escalated_tickets': escalated_tickets,
        'closed_tickets': closed_tickets,
        'closed_count_30_days': closed_count_30_days,
        'search_query': request.GET.get('search', '').strip(),
        'selected_status': request.GET.get('status', '').strip(),
        'selected_priority': request.GET.get('priority', '').strip(),
        'selected_assigned_person': request.GET.get('assigned_person', '').strip(),
        'selected_ticket_number': request.GET.get('ticket_number', '').strip(),
        'date_from': request.GET.get('date_from', '').strip(),
        'date_to': request.GET.get('date_to', '').strip(),
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'employees': employees,
        'selected_main_error_type': request.GET.get('main_error_type', '').strip(),
        'selected_sub_error_type': request.GET.get('sub_error_type', '').strip(),
    })


# ============================================================
# EXCEL EXPORTS
# ============================================================
def export_filtered_tickets_excel(request, tickets_qs):
    """Export filtered all_tickets to Excel."""
    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    report_time = now_utc.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=All_Tickets_Export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Tickets"

    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    data_font = Font(name='Calibri', size=10)
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )

    ws.merge_cells('A1:AB1')
    ws['A1'] = "ALL TICKETS - GPLAST SUPPORT SYSTEM"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 45

    ws.merge_cells('A2:AB2')
    ws['A2'] = f"Generated: {report_time}  |  Total Tickets: {tickets_qs.count()}"
    ws['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 25

    headers = [
        'Ticket Number', 'Status', 'Unit Code', 'Unit Name', 'Department',
        'Employee ID', 'Employee Name', 'Mobile', 'Email', 'Screen/Module',
        'Subject', 'Description', 'Priority', 'Error Type', 'Created By Role',
        'Assigned Person', 'Hold Reason', 'Closing Remarks', 'Closed By',
        'Vendor Ticket', 'Main Error Type', 'Sub Error Type', 'Target Date',
        'Created At', 'Closed At', 'Time to Close', 'Escalated At'
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[4].height = 30

    row_idx = 5
    for ticket in tickets_qs:
        def fmt(dt):
            if not dt:
                return ''
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            return dt.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

        target_date_str = ticket.target_date.strftime('%d-%b-%Y') if ticket.target_date else ''
        time_to_close = ''
        if ticket.created_at and ticket.closed_at:
            d = ticket.closed_at - ticket.created_at
            time_to_close = f"{d.days}d {d.seconds // 3600}h {(d.seconds % 3600) // 60}m"

        row_data = [
            ticket.ticket_number, ticket.status,
            ticket.unit.code if ticket.unit else '',
            ticket.unit.full_name if ticket.unit else '',
            ticket.department.name if ticket.department else '',
            ticket.employee_id, ticket.employee_name,
            ticket.mobile, ticket.email, ticket.screen_number,
            ticket.subject, ticket.description or '', ticket.priority,
            ticket.error_type or '', ticket.created_by_role,
            ticket.assigned_person or '', ticket.hold_reason or '',
            ticket.closing_remarks or '', ticket.closed_by or '',
            ticket.vendor_ticket_number or '',
            ticket.main_error_type or 'N/A', ticket.sub_error_type or 'N/A',
            target_date_str, fmt(ticket.created_at), fmt(ticket.closed_at),
            time_to_close, fmt(ticket.escalated_at),
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = data_font
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = thin_border
        row_idx += 1

    column_widths = {
        'A': 18, 'B': 14, 'C': 12, 'D': 25, 'E': 20,
        'F': 14, 'G': 22, 'H': 16, 'I': 25, 'J': 16,
        'K': 30, 'L': 40, 'M': 14, 'N': 20, 'O': 18,
        'P': 20, 'Q': 20, 'R': 30, 'S': 18, 'T': 18,
        'U': 22, 'V': 22, 'W': 18, 'X': 16, 'Y': 22,
        'Z': 16, 'AA': 22
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    add_replies_sheet(wb, tickets_qs)
    wb.save(response)
    return response


def export_filtered_my_tickets_excel(request, tickets_qs):
    """Export filtered my_tickets to Excel."""
    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    report_time = now_utc.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=My_Tickets_Export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "My Tickets"

    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    data_font = Font(name='Calibri', size=10)
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )

    ws.merge_cells('A1:AB1')
    ws['A1'] = "MY TICKETS - GPLAST SUPPORT SYSTEM"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 45

    ws.merge_cells('A2:AB2')
    ws['A2'] = f"Generated: {report_time}  |  Total Tickets: {tickets_qs.count()}"
    ws['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 25

    headers = [
        'Ticket Number', 'Status', 'Unit Code', 'Unit Name', 'Department',
        'Employee ID', 'Employee Name', 'Mobile', 'Email', 'Screen/Module',
        'Subject', 'Description', 'Priority', 'Error Type', 'Created By Role',
        'Assigned Person', 'Hold Reason', 'Closing Remarks', 'Closed By',
        'Vendor Ticket', 'Main Error Type', 'Sub Error Type', 'Target Date',
        'Created At', 'Closed At', 'Time to Close', 'Escalated At'
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[4].height = 30

    row_idx = 5
    for ticket in tickets_qs:
        def fmt(dt):
            if not dt:
                return ''
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            return dt.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

        target_date_str = ticket.target_date.strftime('%d-%b-%Y') if ticket.target_date else ''
        time_to_close = ''
        if ticket.created_at and ticket.closed_at:
            d = ticket.closed_at - ticket.created_at
            time_to_close = f"{d.days}d {d.seconds // 3600}h {(d.seconds % 3600) // 60}m"

        row_data = [
            ticket.ticket_number, ticket.status,
            ticket.unit.code if ticket.unit else '',
            ticket.unit.full_name if ticket.unit else '',
            ticket.department.name if ticket.department else '',
            ticket.employee_id, ticket.employee_name,
            ticket.mobile, ticket.email, ticket.screen_number,
            ticket.subject, ticket.description or '', ticket.priority,
            ticket.error_type or '', ticket.created_by_role,
            ticket.assigned_person or '', ticket.hold_reason or '',
            ticket.closing_remarks or '', ticket.closed_by or '',
            ticket.vendor_ticket_number or '',
            ticket.main_error_type or 'N/A', ticket.sub_error_type or 'N/A',
            target_date_str, fmt(ticket.created_at), fmt(ticket.closed_at),
            time_to_close, fmt(ticket.escalated_at),
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = data_font
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = thin_border
        row_idx += 1

    column_widths = {
        'A': 18, 'B': 14, 'C': 12, 'D': 25, 'E': 20,
        'F': 14, 'G': 22, 'H': 16, 'I': 25, 'J': 16,
        'K': 30, 'L': 40, 'M': 14, 'N': 20, 'O': 18,
        'P': 20, 'Q': 20, 'R': 30, 'S': 18, 'T': 18,
        'U': 22, 'V': 22, 'W': 18, 'X': 16, 'Y': 22,
        'Z': 16, 'AA': 22
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    add_replies_sheet(wb, tickets_qs)
    wb.save(response)
    return response


def add_replies_sheet(wb, tickets_qs):
    """Add a Replies sheet to a workbook for the given tickets."""
    replies = TicketReply.objects.filter(ticket__in=tickets_qs).select_related('ticket', 'author').order_by('created_at')
    if not replies.exists():
        return

    ws = wb.create_sheet("Replies")
    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    data_font = Font(name='Calibri', size=10)
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )

    ws.merge_cells('A1:F1')
    ws['A1'] = f"TICKET REPLIES - Total: {replies.count()}"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 40

    headers = ['Ticket #', 'Date/Time', 'Author', 'Role', 'Reply', 'Ticket Subject']
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    ws.row_dimensions[3].height = 30

    current_tz = timezone.get_current_timezone()
    row_idx = 4
    for reply in replies:
        if reply.created_at:
            dt = reply.created_at
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            created_at_local = dt.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            created_at_local = ''

        vals = [
            reply.ticket.ticket_number,
            created_at_local,
            reply.author_name or 'Unknown',
            reply.author_role or 'Employee',
            get_reply_text(reply),
            reply.ticket.subject or '',
        ]
        for col, val in enumerate(vals, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        row_idx += 1

    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 50
    ws.column_dimensions['F'].width = 35


# ============================================================
# TICKET DETAIL
# ============================================================
@login_required
def employee_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if not request.user.is_staff and not _employee_ticket_scope(request.user).filter(pk=ticket.pk).exists():
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('employee_all_tickets')

    history = TicketHistory.objects.filter(ticket=ticket).order_by('timestamp')
    replies = ticket.replies.select_related('author').all()
    screen_object = ScreenMaster.objects.filter(screen_code=ticket.screen_number).first()

    attachments = []
    if ticket.attachment_1:
        attachments.append({'file': ticket.attachment_1, 'name': 'Attachment 1'})
    if ticket.attachment_2:
        attachments.append({'file': ticket.attachment_2, 'name': 'Attachment 2'})
    if ticket.attachment_3:
        attachments.append({'file': ticket.attachment_3, 'name': 'Attachment 3'})

    can_reopen = False
    reopen_deadline_iso = ''
    if ticket.status == 'Closed' and ticket.closed_at:
        if (timezone.now() - ticket.closed_at).total_seconds() <= 48 * 3600:
            can_reopen = True
            reopen_deadline_iso = (ticket.closed_at + timedelta(hours=48)).isoformat()

    time_to_close = 'N/A'
    if ticket.closed_at and ticket.created_at:
        diff = ticket.closed_at - ticket.created_at
        hours = diff.total_seconds() / 3600
        time_to_close = f'{int(diff.total_seconds() / 60)} minutes' if hours < 1 else f'{hours:.1f} hours'

    return render(request, 'employee/ticket_detail.html', {
        'ticket': ticket,
        'history': history,
        'replies': replies,
        'reply_form': TicketReplyForm(),
        'can_reply': True,
        'employee_reply_url': reverse('employee_ticket_reply', args=[ticket.id]),
        'attachments': attachments,
        'can_reopen': can_reopen,
        'reopen_deadline_iso': reopen_deadline_iso,
        'time_to_close': time_to_close,
        'employees': EmployeeMaster.objects.filter(is_active=True),
        'screen_object': screen_object,
    })


@login_required
def ticket_detail(request, ticket_id):
    return employee_ticket_detail(request, ticket_id)


# ============================================================
# EMPLOYEE REPLY
# ============================================================
@login_required
def employee_ticket_reply(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if not request.user.is_staff and not _employee_ticket_scope(request.user).filter(pk=ticket.pk).exists():
        messages.error(request, 'You do not have permission to reply to this ticket.')
        return redirect('employee_all_tickets')

    if request.method != 'POST':
        return redirect('ticket_detail', ticket_id=ticket.id)

    form = TicketReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.ticket = ticket
        reply.author = request.user
        reply.author_name = request.user.get_full_name() or request.user.username
        reply.author_role = 'Employee'
        reply.save()

        try:
            from tickets.services.notify import notify_ticket_replied
            notify_ticket_replied(ticket, reply, actor=request.user)
        except Exception as _e:
            logger.warning(f"notify_ticket_replied failed: {_e}")

        messages.success(request, 'Reply added successfully.')
    else:
        messages.error(request, 'Please fix the errors below.')

    return redirect('ticket_detail', ticket_id=ticket.id)


# ============================================================
# INDIVIDUAL TICKET EXCEL
# ============================================================
@login_required
def download_individual_ticket_excel(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if not request.user.is_staff and not _employee_ticket_scope(request.user).filter(pk=ticket.pk).exists():
        messages.error(request, 'You do not have permission to download this ticket.')
        return redirect('employee_all_tickets')

    history = TicketHistory.objects.filter(ticket=ticket).order_by('timestamp')
    replies = ticket.replies.select_related('author').all().order_by('created_at')

    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    report_time = now_utc.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Ticket_{ticket.ticket_number}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Ticket Details"

    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    section_font = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
    label_font = Font(name='Calibri', size=11, bold=True, color='1A2A6C')
    data_font = Font(name='Calibri', size=11, color='333333')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    section_fill = PatternFill(start_color='FF6B00', end_color='FF6B00', fill_type='solid')
    label_fill = PatternFill(start_color='E8EDF5', end_color='E8EDF5', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )

    def write_section(ws, row, title):
        ws.merge_cells(f'A{row}:F{row}')
        ws[f'A{row}'] = title
        ws[f'A{row}'].font = section_font
        ws[f'A{row}'].fill = section_fill
        ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.row_dimensions[row].height = 30
        return row + 1

    def write_kv(ws, row, label, value):
        ws.cell(row=row, column=1, value=label).font = label_font
        ws.cell(row=row, column=1).fill = label_fill
        ws.cell(row=row, column=1).border = thin_border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.cell(row=row, column=2, value=value).font = data_font
        ws.cell(row=row, column=2).border = thin_border
        ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        return row + 1

    ws1.merge_cells('A1:F1')
    ws1['A1'] = f"GPLAST TICKET DETAILS - {ticket.ticket_number}"
    ws1['A1'].font = title_font
    ws1['A1'].fill = title_fill
    ws1['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws1.row_dimensions[1].height = 40

    row = 3
    row = write_section(ws1, row, "BASIC INFORMATION")
    for label, value in [
        ('Ticket Number', ticket.ticket_number),
        ('Subject', ticket.subject),
        ('Description', ticket.description or ''),
        ('Priority', ticket.priority),
        ('Status', ticket.status),
        ('Error Type', ticket.error_type or 'Not Set'),
        ('Target Date', ticket.target_date.strftime('%d-%b-%Y') if ticket.target_date else 'Not Set'),
        ('Created Date', timezone.localtime(ticket.created_at).strftime('%d-%b-%Y %I:%M %p') if ticket.created_at else ''),
        ('Updated Date', ticket.updated_at.strftime('%d-%b-%Y %I:%M %p') if ticket.updated_at else ''),
    ]:
        row = write_kv(ws1, row, label, value)

    row += 1
    row = write_section(ws1, row, "EMPLOYEE DETAILS")
    for label, value in [
        ('Employee Name', ticket.employee_name),
        ('Employee ID', ticket.employee_id),
        ('Mobile', ticket.mobile or ''),
        ('Email', ticket.email or ''),
        ('Unit', ticket.unit.full_name if ticket.unit else ''),
        ('Department', ticket.department.name if ticket.department else ''),
        ('Screen/Module', ticket.screen_number),
    ]:
        row = write_kv(ws1, row, label, value)

    row += 1
    row = write_section(ws1, row, "ASSIGNMENT & STATUS")
    for label, value in [
        ('Created By Role', ticket.created_by_role),
        ('Assigned To', ticket.assigned_person or 'Not Assigned'),
        ('Hold Reason', ticket.hold_reason or ''),
        ('Vendor Ticket', ticket.vendor_ticket_number or ''),
        ('Admin Creation Reason', ticket.admin_creation_reason or ''),
    ]:
        row = write_kv(ws1, row, label, value)

    row += 1
    if ticket.status == 'Closed':
        row = write_section(ws1, row, "CLOSING DETAILS")
        ttc = ''
        if ticket.created_at and ticket.closed_at:
            d = ticket.closed_at - ticket.created_at
            ttc = f"{d.days}d {d.seconds // 3600}h {(d.seconds % 3600) // 60}m"
        for label, value in [
            ('Closed By', ticket.closed_by or ''),
            ('Closed Date', timezone.localtime(ticket.closed_at).strftime('%d-%b-%Y %I:%M %p') if ticket.closed_at else ''),
            ('Main Error Type', ticket.main_error_type or 'N/A'),
            ('Sub Error Type', ticket.sub_error_type or 'N/A'),
            ('Closing Remarks', ticket.closing_remarks or ''),
            ('Time to Close', ttc),
        ]:
            row = write_kv(ws1, row, label, value)
        row += 1

    ws1.merge_cells(f'A{row}:F{row}')
    ws1[f'A{row}'] = f"Report generated on {report_time} | GPLAST Support System"
    ws1[f'A{row}'].font = Font(name='Calibri', size=9, italic=True, color='666666')
    ws1[f'A{row}'].alignment = Alignment(horizontal='center', vertical='center')
    ws1.row_dimensions[row].height = 25

    ws1.column_dimensions['A'].width = 28
    ws1.column_dimensions['B'].width = 35
    for col in ['C', 'D', 'E', 'F']:
        ws1.column_dimensions[col].width = 20

    # Audit History
    ws2 = wb.create_sheet("Audit History")
    ws2.merge_cells('A1:E1')
    ws2['A1'] = f"AUDIT HISTORY - Ticket #{ticket.ticket_number}"
    ws2['A1'].font = title_font
    ws2['A1'].fill = title_fill
    ws2['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws2.row_dimensions[1].height = 40

    for col_idx, header in enumerate(['#', 'Timestamp', 'Action', 'Remarks', 'Performed By'], 1):
        cell = ws2.cell(row=3, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    for idx, log in enumerate(history, start=1):
        ts = ''
        if log.timestamp:
            dt = log.timestamp
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            ts = dt.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        r = idx + 3
        ws2.cell(row=r, column=1, value=idx)
        ws2.cell(row=r, column=2, value=ts)
        ws2.cell(row=r, column=3, value=log.action)
        ws2.cell(row=r, column=4, value=log.remarks or '')
        ws2.cell(row=r, column=5, value=log.get_performed_by_display())
        for c in range(1, 6):
            ws2.cell(row=r, column=c).font = data_font
            ws2.cell(row=r, column=c).border = thin_border
            ws2.cell(row=r, column=c).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    ws2.column_dimensions['A'].width = 8
    ws2.column_dimensions['B'].width = 22
    ws2.column_dimensions['C'].width = 30
    ws2.column_dimensions['D'].width = 50
    ws2.column_dimensions['E'].width = 22

    # Replies
    ws3 = wb.create_sheet("Replies")
    ws3.merge_cells('A1:E1')
    ws3['A1'] = f"REPLIES - Ticket #{ticket.ticket_number}"
    ws3['A1'].font = title_font
    ws3['A1'].fill = title_fill
    ws3['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws3.row_dimensions[1].height = 40

    for col_idx, header in enumerate(['#', 'Date/Time', 'Author', 'Reply', 'Role'], 1):
        cell = ws3.cell(row=3, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    for idx, reply in enumerate(replies, start=1):
        ts = ''
        if reply.created_at:
            dt = reply.created_at
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            ts = dt.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        r = idx + 3
        ws3.cell(row=r, column=1, value=idx)
        ws3.cell(row=r, column=2, value=ts)
        ws3.cell(row=r, column=3, value=reply.author_name or 'Unknown')
        ws3.cell(row=r, column=4, value=get_reply_text(reply))
        ws3.cell(row=r, column=5, value=reply.author_role or 'Employee')
        for c in range(1, 6):
            ws3.cell(row=r, column=c).font = data_font
            ws3.cell(row=r, column=c).border = thin_border
            ws3.cell(row=r, column=c).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    ws3.column_dimensions['A'].width = 8
    ws3.column_dimensions['B'].width = 22
    ws3.column_dimensions['C'].width = 25
    ws3.column_dimensions['D'].width = 50
    ws3.column_dimensions['E'].width = 18

    wb.save(response)
    return response


# ============================================================
# UPDATE TICKET STATUS
# ============================================================
@login_required
def update_ticket_status(request, ticket_id):
    if request.method != 'POST':
        return redirect('ticket_detail', ticket_id=ticket_id)

    ticket = get_object_or_404(Ticket, id=ticket_id)
    action_type = request.POST.get('action_type')

    if not request.user.is_staff:
        if not _employee_ticket_scope(request.user).filter(pk=ticket.pk).exists():
            messages.error(request, 'You do not have permission to update this ticket.')
            return redirect('employee_all_tickets')
        if action_type != 'Reopen':
            messages.error(request, 'Only administrators can perform this ticket action.')
            return redirect('ticket_detail', ticket_id=ticket_id)

    if action_type == 'Assign':
        assigned_person = request.POST.get('assigned_person')
        remarks = request.POST.get('remarks', '')
        target_date_str = request.POST.get('target_date', '').strip()
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid target date format.')
                return redirect('ticket_detail', ticket_id=ticket_id)

        if assigned_person:
            ticket.assigned_person = assigned_person
            ticket.status = 'Assigned'
            if target_date:
                ticket.target_date = target_date
            ticket.save()

            TicketHistory.objects.create(
                ticket=ticket,
                action=f'Assigned to {assigned_person}',
                remarks=remarks + (f' | Target Date: {target_date.strftime("%d-%b-%Y")}' if target_date else ''),
                performed_by=request.user.username,
            )

            try:
                from tickets.services.notify import notify_ticket_assigned, ticket_assignee
                assignee_user = ticket_assignee(ticket)
                notify_ticket_assigned(ticket, assignee_user, actor=request.user)
            except Exception as _e:
                logger.warning(f"notify_ticket_assigned failed: {_e}")

            messages.success(request, f'Ticket assigned to {assigned_person}.')
        else:
            messages.error(request, 'Please select an employee to assign')

    elif action_type == 'Hold':
        hold_reason = request.POST.get('hold_reason')
        if hold_reason:
            old_status = ticket.status
            ticket.hold_reason = hold_reason
            ticket.status = 'Hold'
            ticket.save()
            TicketHistory.objects.create(
                ticket=ticket, action='Put on Hold',
                remarks=hold_reason, performed_by=request.user.username,
            )
            try:
                from tickets.services.notify import notify_status_changed
                notify_status_changed(ticket, old_status, 'Hold', actor=request.user)
            except Exception as _e:
                logger.warning(f"notify_status_changed (Hold) failed: {_e}")
            messages.success(request, 'Ticket put on hold')
        else:
            messages.error(request, 'Please provide a reason for holding')

    elif action_type == 'Escalate':
        vendor_ticket = request.POST.get('vendor_ticket_number', '')
        remarks = request.POST.get('remarks', '')
        old_status = ticket.status
        if vendor_ticket:
            ticket.vendor_ticket_number = vendor_ticket
        ticket.status = 'Escalated'
        ticket.escalated_at = timezone.now()
        ticket.save()
        TicketHistory.objects.create(
            ticket=ticket, action='Escalated to Vendor',
            remarks=f'Vendor Ticket: {vendor_ticket or "N/A"} - {remarks}',
            performed_by=request.user.username,
        )
        try:
            from tickets.services.notify import notify_status_changed
            notify_status_changed(ticket, old_status, 'Escalated', actor=request.user)
        except Exception as _e:
            logger.warning(f"notify_status_changed (Escalate) failed: {_e}")
        messages.success(request, 'Ticket escalated successfully')

    elif action_type == 'Close':
        main_error_type = request.POST.get('main_error_type', '').strip()
        sub_error_type = request.POST.get('sub_error_type', '').strip()
        closing_remarks = request.POST.get('closing_remarks', '').strip()

        if main_error_type and sub_error_type and closing_remarks:
            old_status = ticket.status
            ticket.main_error_type = main_error_type
            ticket.sub_error_type = sub_error_type
            ticket.closing_remarks = closing_remarks
            ticket.status = 'Closed'
            ticket.closed_by = request.user.username
            ticket.closed_at = timezone.now()
            ticket.save()
            TicketHistory.objects.create(
                ticket=ticket, action='Closed Ticket',
                remarks=f'Main Error: {main_error_type}\nSub Error: {sub_error_type}\nClosing Remarks: {closing_remarks}',
                performed_by=request.user.username,
            )
            try:
                from tickets.services.notify import notify_status_changed
                notify_status_changed(ticket, old_status, 'Closed', actor=request.user)
            except Exception as _e:
                logger.warning(f"notify_status_changed (Close) failed: {_e}")
            messages.success(request, 'Ticket closed successfully')
        else:
            messages.error(request, 'Please provide main error type, sub error type, and closing remarks')

    elif action_type == 'Reopen':
        remarks = request.POST.get('remarks', '')
        uploaded_files = request.FILES.getlist('reopen_attachments')

        if remarks:
            if ticket.closed_at and (timezone.now() - ticket.closed_at).total_seconds() <= 48 * 3600:
                try:
                    for f in uploaded_files:
                        validate_attachment(f)
                except ValidationError as error:
                    messages.error(request, str(error))
                    return redirect('ticket_detail', ticket_id=ticket_id)

                old_status = ticket.status
                ticket.status = 'Open'
                ticket.closed_at = None
                ticket.closed_by = None
                ticket.closing_remarks = ''
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, action='Reopened Ticket',
                    remarks=remarks, performed_by=request.user.username,
                )
                for f in uploaded_files:
                    ReopenAttachment.objects.create(
                        ticket=ticket, file=f, uploaded_by=request.user.username,
                    )
                try:
                    from tickets.services.notify import notify_status_changed
                    notify_status_changed(ticket, old_status, 'Open', actor=request.user)
                except Exception as _e:
                    logger.warning(f"notify_status_changed (Reopen) failed: {_e}")
                messages.success(request, 'Ticket reopened successfully')
            else:
                messages.error(request, 'Cannot reopen ticket after 48 hours')
        else:
            messages.error(request, 'Please provide a reason for reopening')

    elif action_type == 'UpdateTargetDate':
        target_date_str = request.POST.get('target_date', '').strip()
        if not target_date_str:
            messages.error(request, 'Target date is required.')
            return redirect('ticket_detail', ticket_id=ticket_id)
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            if target_date < timezone.now().date():
                messages.error(request, 'Target date cannot be in the past.')
                return redirect('ticket_detail', ticket_id=ticket_id)
            old_target_date = ticket.target_date
            ticket.target_date = target_date
            ticket.save()
            TicketHistory.objects.create(
                ticket=ticket, action='Target Date Updated',
                remarks=f'Target date changed from {old_target_date.strftime("%d-%b-%Y") if old_target_date else "Not set"} to {target_date.strftime("%d-%b-%Y")}',
                performed_by=request.user.username,
            )
            messages.success(request, f'Target date updated to {target_date.strftime("%d-%b-%Y")}.')
        except ValueError:
            messages.error(request, 'Invalid date format.')

    return redirect('ticket_detail', ticket_id=ticket_id)


# ============================================================
# EXPORT CLOSED TICKETS (LAST 30 DAYS)
# ============================================================
@login_required
def export_closed_tickets_30_days(request):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    tickets_qs = _employee_ticket_scope(request.user).filter(
        status='Closed', closed_at__gte=thirty_days_ago,
    ).order_by('-closed_at')

    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    report_time = now_utc.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Closed_Tickets_30_Days_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Closed Tickets (30 Days)"

    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    data_font = Font(name='Calibri', size=10)
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )

    ws.merge_cells('A1:AA1')
    ws['A1'] = "CLOSED TICKETS - LAST 30 DAYS"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 45

    ws.merge_cells('A2:AA2')
    ws['A2'] = f"Generated: {report_time}  |  Total Closed Tickets: {tickets_qs.count()}"
    ws['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 25

    headers = [
        'Ticket Number', 'Status', 'Unit Code', 'Unit Name', 'Department',
        'Employee ID', 'Employee Name', 'Mobile', 'Email', 'Screen/Module',
        'Subject', 'Description', 'Priority', 'Error Type', 'Created By Role',
        'Admin Creation Reason', 'Assigned Person', 'Hold Reason',
        'Main Error Type', 'Sub Error Type', 'Target Date', 'Closing Remarks',
        'Closed By', 'Vendor Ticket Number', 'Created At', 'Closed At',
        'Time to Close', 'Escalated At'
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[4].height = 30

    row_idx = 5
    for ticket in tickets_qs:
        def fmt(dt):
            if not dt:
                return ''
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            return dt.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')

        target_date_str = ticket.target_date.strftime('%d-%b-%Y') if ticket.target_date else ''
        ttc = ''
        if ticket.created_at and ticket.closed_at:
            d = ticket.closed_at - ticket.created_at
            ttc = f"{d.days}d {d.seconds // 3600}h {(d.seconds % 3600) // 60}m"

        row_data = [
            ticket.ticket_number, ticket.status,
            ticket.unit.code if ticket.unit else '',
            ticket.unit.full_name if ticket.unit else '',
            ticket.department.name if ticket.department else '',
            ticket.employee_id, ticket.employee_name,
            ticket.mobile, ticket.email, ticket.screen_number,
            ticket.subject, ticket.description or '', ticket.priority,
            ticket.error_type or '', ticket.created_by_role,
            ticket.admin_creation_reason or '', ticket.assigned_person or '',
            ticket.hold_reason or '', ticket.main_error_type or 'N/A',
            ticket.sub_error_type or 'N/A', target_date_str,
            ticket.closing_remarks or '', ticket.closed_by or '',
            ticket.vendor_ticket_number or '', fmt(ticket.created_at),
            fmt(ticket.closed_at), ttc, fmt(ticket.escalated_at),
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = data_font
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = thin_border
        row_idx += 1

    add_replies_sheet(wb, tickets_qs)
    wb.save(response)
    return response


# ============================================================
# GET EMPLOYEE DETAILS (AJAX)
# ============================================================
@login_required
def get_employee_details(request):
    employee_id = request.GET.get('employee_id', '').strip().upper()
    if not employee_id:
        return JsonResponse({'error': 'Employee ID required'}, status=400)
    try:
        employee = EmployeeMaster.objects.filter(
            employee_id=employee_id, is_active=True,
        ).select_related('unit', 'department').first()
        if not employee:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        return JsonResponse({
            'employee_name': employee.employee_name,
            'email': employee.email or '',
            'mobile': employee.mobile or '',
            'unit_id': employee.unit_id,
            'unit_name': employee.unit.full_name if employee.unit else '',
            'department_id': employee.department_id,
            'department_name': employee.department.name if employee.department else '',
        })
    except Exception as e:
        logger.error(f"Error fetching employee details: {e}")
        return JsonResponse({'error': str(e)}, status=500)