# tickets/views/admin_views.py

"""
Admin Views - Dashboard, Create Ticket, All Tickets, Ticket Detail, Reports, Download Excel
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q, DateField
from django.db.models.functions import TruncMonth, Cast
from django.db import transaction
from django.contrib import messages
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import logging

from tickets.models import (
    Unit, Department, Ticket, TicketHistory, EmployeeMaster,
    AdminContact, AdminNotificationEmail, SettingsAuditLog
)
from tickets.forms import AdminTicketForm
from tickets.utils import send_ticket_email

from .utils import (
    is_admin,
    format_timedelta_display,
    reopen_ticket_logic,
    generate_admin_ticket_list_html,
)

logger = logging.getLogger(__name__)


# ============================================================
# ADMIN DASHBOARD
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def admin_dashboard(request):
    """
    Admin dashboard showing:
    - KPIs for all tickets
    - Charts: Status, Unit, Priority, Error Type, Monthly
    - Notification badge count
    """
    all_tickets = Ticket.objects.all()
    
    unviewed_count = Ticket.objects.filter(is_viewed=False).count()
    unviewed_tickets = Ticket.objects.filter(is_viewed=False).order_by('-created_at')[:10]
    
    kpis = {
        'total': all_tickets.count(), 
        'open': all_tickets.filter(status='Open').count(),
        'assigned': all_tickets.filter(status='Assigned').count(), 
        'hold': all_tickets.filter(status='Hold').count(),
        'escalated': all_tickets.filter(status='Escalated').count(), 
        'closed': all_tickets.filter(status='Closed').count(),
        'critical': all_tickets.filter(priority='Critical').count(),
        'unviewed': unviewed_count,
    }
    
    status_counts = list(all_tickets.values('status').annotate(count=Count('id')))
    chart_status = {item['status']: item['count'] for item in status_counts}
    
    unit_counts = list(all_tickets.filter(unit__isnull=False).values('unit_id', 'unit__code').annotate(count=Count('id')).order_by('unit__code'))
    chart_units = [{'id': item['unit_id'], 'label': item['unit__code'], 'value': item['count']} for item in unit_counts]
    
    prio_counts = list(all_tickets.values('priority').annotate(count=Count('id')))
    chart_priority = {item['priority']: item['count'] for item in prio_counts}
    
    closed_tickets = Ticket.objects.filter(status='Closed')
    error_type_counts = (
        closed_tickets
        .exclude(error_type__isnull=True)
        .exclude(error_type__exact='')
        .values('error_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    chart_error_type = {item['error_type']: item['count'] for item in error_type_counts}
    
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_counts_qs = Ticket.objects.filter(created_at__gte=twelve_months_ago).annotate(
        month=TruncMonth(Cast('created_at', output_field=DateField()))
    ).values('month').annotate(count=Count('id')).order_by('month')
    chart_monthly = [{'label': item['month'].strftime('%b %Y'), 'value': item['count']} for item in monthly_counts_qs]
    
    charts_data = {
        'status': chart_status,
        'units': chart_units,
        'priority': chart_priority,
        'errorType': chart_error_type,
        'monthly': chart_monthly,
    }
    
    context = {
        'kpis': kpis,
        'charts_data': charts_data,
        'unviewed_count': unviewed_count,
        'unviewed_tickets': unviewed_tickets,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ============================================================
# CREATE TICKET - ADMIN
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def create_ticket_admin(request):
    """
    Admin ticket creation with:
    - Employee assignment options
    - Admin creation reason
    - Admin or Employee role selection
    - 3 attachment fields
    """
    employees = EmployeeMaster.objects.filter(is_active=True, can_assign_ticket=True).order_by('employee_name')
    
    if request.method == 'POST':
        form = AdminTicketForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                ticket = form.save(commit=False)
                
                if ticket.created_by_role == 'Admin':
                    hist_remark = f"Ticket created by Admin on behalf of employee (Reason: {ticket.admin_creation_reason})"
                    hist_perf = f"Admin {request.user.username}"
                    ticket.created_by_user = request.user
                else:
                    hist_remark = "Ticket Created by Employee (logged by Admin)"
                    hist_perf = "Employee"
                    employee_user, _ = User.objects.get_or_create(
                        username='GPLERPUSERS', 
                        defaults={'is_staff': False, 'password': 'pbkdf2_sha256$720000$j5xL6pS0LpGvLq3sRjVbWk$V/Hq7aYt2x531enqYm5d9f2uZdtsJ7MLd2y221C+L9s='}
                    )
                    ticket.created_by_user = employee_user
                
                ticket.save()
                
                TicketHistory.objects.create(
                    ticket=ticket, 
                    action="Ticket Created", 
                    remarks=hist_remark, 
                    performed_by=hist_perf
                )
            
            send_ticket_email(ticket, 'Created')
            messages.success(request, f'Ticket {ticket.ticket_number} created successfully by Admin!')
            return redirect('admin_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminTicketForm()
    
    return render(request, 'admin_panel/create_ticket.html', {
        'form': form,
        'employees': employees,
    })


# ============================================================
# ALL TICKETS - ADMIN
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def all_tickets(request):
    """
    Admin ticket listing with filters, AJAX support, and pagination
    """
    is_ajax = request.GET.get('ajax', False)
    
    if isinstance(is_ajax, str):
        is_ajax = is_ajax.lower() in ['true', '1', 'yes']
    
    tickets_qs = Ticket.objects.all().order_by('-created_at')
    units = Unit.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    category = request.GET.get('category', 'all')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    unit_id = request.GET.get('unit')
    dept_id = request.GET.get('department')
    assigned_person = request.GET.get('assigned_person', '').strip()
    created_by_role = request.GET.get('created_by_role')
    ticket_number = request.GET.get('ticket_number', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search = request.GET.get('search', '').strip()
    
    is_viewed = request.GET.get('is_viewed', '')
    if is_viewed == 'false':
        tickets_qs = tickets_qs.filter(is_viewed=False)
    elif is_viewed == 'true':
        tickets_qs = tickets_qs.filter(is_viewed=True)
    
    employees = EmployeeMaster.objects.filter(is_active=True, can_assign_ticket=True).order_by('employee_name')
    
    if category == 'open': 
        tickets_qs = tickets_qs.filter(status='Open')
    elif category == 'assigned': 
        tickets_qs = tickets_qs.filter(status='Assigned')
    elif category == 'hold': 
        tickets_qs = tickets_qs.filter(status='Hold')
    elif category == 'escalated': 
        tickets_qs = tickets_qs.filter(status='Escalated')
    elif category == 'closed': 
        tickets_qs = tickets_qs.filter(status='Closed')
    elif category == 'critical': 
        tickets_qs = tickets_qs.filter(priority='Critical')
    
    if unit_id: 
        tickets_qs = tickets_qs.filter(unit_id=unit_id)
    if dept_id: 
        tickets_qs = tickets_qs.filter(department_id=dept_id)
    if status: 
        tickets_qs = tickets_qs.filter(status=status)
    if priority: 
        tickets_qs = tickets_qs.filter(priority=priority)
    if assigned_person: 
        tickets_qs = tickets_qs.filter(assigned_person__icontains=assigned_person)
    if created_by_role: 
        tickets_qs = tickets_qs.filter(created_by_role=created_by_role)
    if ticket_number: 
        tickets_qs = tickets_qs.filter(ticket_number__icontains=ticket_number)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            from_datetime = timezone.make_aware(
                datetime.combine(date_from_obj, datetime.min.time())
            )
            tickets_qs = tickets_qs.filter(created_at__gte=from_datetime)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            to_datetime = timezone.make_aware(
                datetime.combine(date_to_obj, datetime.max.time())
            )
            tickets_qs = tickets_qs.filter(created_at__lte=to_datetime)
        except ValueError:
            pass
    
    if search: 
        tickets_qs = tickets_qs.filter(
            Q(ticket_number__icontains=search) | 
            Q(subject__icontains=search) | 
            Q(unit__code__icontains=search) | 
            Q(department__name__icontains=search)
        )
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    closed_count_30_days = Ticket.objects.filter(
        status='Closed',
        closed_at__gte=thirty_days_ago
    ).count()
    
    if is_ajax:
        filter_value = 'All'
        filter_type = 'status'
        
        if status:
            filter_value = status
            filter_type = 'status'
        elif priority:
            filter_value = priority
            filter_type = 'priority'
        elif unit_id:
            unit = Unit.objects.filter(pk=unit_id).first()
            filter_value = unit.code if unit else 'Unit'
            filter_type = 'unit'
        elif category and category != 'all':
            filter_value = category.capitalize()
            filter_type = 'status'

        try:
            try:
                html = render_to_string('admin_panel/_ticket_list_modal.html', {
                    'tickets': tickets_qs[:50],
                    'status_label': filter_value,
                    'filter_type': filter_type,
                    'filter_value': filter_value,
                }, request=request)
                return JsonResponse({'html': html, 'success': True, 'count': tickets_qs.count()})
            except TemplateDoesNotExist:
                html = generate_admin_ticket_list_html(tickets_qs[:50], filter_value)
                return JsonResponse({'html': html, 'success': True, 'count': tickets_qs.count()})
            except Exception as e:
                logger.error(f"AJAX error in all_tickets (template): {str(e)}")
                html = generate_admin_ticket_list_html(tickets_qs[:50], filter_value)
                return JsonResponse({'html': html, 'success': True, 'count': tickets_qs.count()})
        except Exception as e:
            logger.error(f"AJAX error in all_tickets: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e),
                'message': 'Error loading tickets. Please try again.'
            }, status=500)
    
    paginator = Paginator(tickets_qs, 20)
    page_number = request.GET.get('page')
    try: 
        tickets_page = paginator.page(page_number)
    except PageNotAnInteger: 
        tickets_page = paginator.page(1)
    except EmptyPage: 
        tickets_page = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': tickets_page,
        'units': units, 
        'departments': departments,
        'employees': employees,
        'status_choices': Ticket.STATUS_CHOICES, 
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'created_by_choices': Ticket.CREATED_BY_CHOICES, 
        'selected_status': status,
        'selected_priority': priority, 
        'selected_unit': unit_id, 
        'selected_department': dept_id,
        'selected_assigned_person': assigned_person, 
        'selected_created_by_role': created_by_role,
        'selected_ticket_number': ticket_number, 
        'date_from': date_from, 
        'date_to': date_to,
        'search_query': search, 
        'category': category,
        'is_viewed': is_viewed,
        'closed_count_30_days': closed_count_30_days,
    }
    return render(request, 'admin_panel/all_tickets.html', context)


# ============================================================
# TICKET DETAIL - ADMIN
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def ticket_detail_admin(request, pk):
    """
    Admin ticket detail view with full ticket management
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if not ticket.is_viewed:
        ticket.is_viewed = True
        ticket.viewed_at = timezone.now()
        ticket.save()
        logger.info(f"Ticket {ticket.ticket_number} marked as viewed by {request.user.username}")
    
    history = ticket.history.all().order_by('timestamp')
    can_reopen = False
    reopen_time_left = None
    reopen_deadline = None
    
    if ticket.status == 'Closed' and ticket.closed_at:
        reopen_deadline = ticket.closed_at + timedelta(hours=48)
        if timezone.now() < reopen_deadline: 
            can_reopen = True
            reopen_time_left = reopen_deadline - timezone.now()
    
    time_to_close_str = ""
    if ticket.status == 'Closed' and ticket.created_at and ticket.closed_at:
        time_to_close = ticket.closed_at - ticket.created_at
        time_to_close_str = format_timedelta_display(time_to_close)
    
    employees = EmployeeMaster.objects.filter(is_active=True, can_assign_ticket=True).order_by('employee_name')
    
    attachments = []
    if ticket.attachment_1:
        attachments.append({'file': ticket.attachment_1, 'name': 'Attachment 1'})
    if ticket.attachment_2:
        attachments.append({'file': ticket.attachment_2, 'name': 'Attachment 2'})
    if ticket.attachment_3:
        attachments.append({'file': ticket.attachment_3, 'name': 'Attachment 3'})
    
    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        remarks = request.POST.get('remarks', '')
        
        with transaction.atomic():
            if action_type == 'Assign':
                assigned_person = request.POST.get('assigned_person', '').strip()
                if not assigned_person: 
                    messages.error(request, "Assigned Person Name is mandatory.")
                    return redirect('admin_ticket_detail', pk=pk)
                ticket.status = 'Assigned'
                ticket.assigned_person = assigned_person
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, 
                    action=f"Assigned to {assigned_person}", 
                    remarks=remarks, 
                    performed_by=f"Admin {request.user.username}"
                )
                messages.success(request, f'Ticket assigned to {assigned_person}.')
                
            elif action_type == 'Hold':
                hold_reason = request.POST.get('hold_reason', '').strip()
                if not hold_reason: 
                    messages.error(request, "Hold Reason is mandatory.")
                    return redirect('admin_ticket_detail', pk=pk)
                ticket.status = 'Hold'
                ticket.hold_reason = hold_reason
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, 
                    action="Status changed to Hold", 
                    remarks=f"Reason: {hold_reason}", 
                    performed_by=f"Admin {request.user.username}"
                )
                messages.success(request, 'Ticket placed on Hold.')
                
            elif action_type == 'Escalate':
                vendor_ticket = request.POST.get('vendor_ticket_number', '').strip()
                ticket.status = 'Escalated'
                if vendor_ticket: 
                    ticket.vendor_ticket_number = vendor_ticket
                ticket.escalated_at = timezone.now()
                ticket.save()
                remark_str = f"Vendor Ticket: {vendor_ticket}" if vendor_ticket else "Escalated without vendor ticket number"
                TicketHistory.objects.create(
                    ticket=ticket, 
                    action="Escalated to ERP Vendor", 
                    remarks=remark_str, 
                    performed_by=f"Admin {request.user.username}"
                )
                messages.success(request, 'Ticket escalated to ERP vendor.')
                
            elif action_type == 'Close':
                closing_remarks = request.POST.get('closing_remarks', '').strip()
                error_type = request.POST.get('error_type', '').strip()
                if not closing_remarks: 
                    messages.error(request, "Closing Remarks are mandatory.")
                    return redirect('admin_ticket_detail', pk=pk)
                if not error_type: 
                    messages.error(request, "Error Classification is mandatory.")
                    return redirect('admin_ticket_detail', pk=pk)
                ticket.status = 'Closed'
                ticket.closing_remarks = closing_remarks
                ticket.error_type = error_type
                ticket.closed_by = request.user.username
                ticket.closed_at = timezone.now()
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, 
                    action=f"Closed by {request.user.username}", 
                    remarks=f"Error Type: {error_type} | {closing_remarks}", 
                    performed_by=f"Admin {request.user.username}"
                )
                send_ticket_email(ticket, 'Closed', remarks=closing_remarks)
                messages.success(request, 'Ticket closed successfully.')
                
            elif action_type == 'Reopen':
                if not can_reopen: 
                    messages.error(request, "Cannot reopen - 48 hours elapsed.")
                    return redirect('admin_ticket_detail', pk=pk)
                remarks = request.POST.get('remarks', '').strip()
                if not remarks: 
                    messages.error(request, "Reason for reopening is mandatory.")
                    return redirect('admin_ticket_detail', pk=pk)
                reopen_ticket_logic(ticket, f"Admin {request.user.username}", remarks)
                messages.success(request, 'Ticket reopened successfully.')
                
        return redirect('admin_ticket_detail', pk=pk)
    
    context = {
        'ticket': ticket,
        'history': history,
        'employees': employees,
        'attachments': attachments,
        'can_reopen': can_reopen,
        'time_to_close': time_to_close_str,
        'reopen_time_left': reopen_time_left,
        'reopen_deadline_iso': reopen_deadline.isoformat() if reopen_deadline else None,
    }
    return render(request, 'admin_panel/ticket_detail.html', context)


# ============================================================
# DOWNLOAD TICKET EXCEL
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def download_ticket_excel(request, pk):
    """
    Export single ticket details to Excel
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Ticket_{ticket.ticket_number}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Ticket {ticket.ticket_number}"
    
    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    section_font = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
    label_font = Font(name='Calibri', size=11, bold=True, color='1A2A6C')
    data_font = Font(name='Calibri', size=11, color='333333')
    history_header_font = Font(name='Calibri', size=10, bold=True, color='FFFFFF')
    history_data_font = Font(name='Calibri', size=10, color='333333')
    
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    section_fill = PatternFill(start_color='FF6B00', end_color='FF6B00', fill_type='solid')
    label_fill = PatternFill(start_color='E8EDF5', end_color='E8EDF5', fill_type='solid')
    history_header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )
    
    ws.merge_cells('A1:F1')
    ws['A1'] = f"GPLAST TICKET DETAILS - {ticket.ticket_number}"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 40
    
    row = 3
    ws.merge_cells(f'A{row}:F{row}')
    ws[f'A{row}'] = "BASIC INFORMATION"
    ws[f'A{row}'].font = section_font
    ws[f'A{row}'].fill = section_fill
    ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[row].height = 30
    row += 1
    
    basic_info = [
        ('Ticket Number', ticket.ticket_number),
        ('Subject', ticket.subject),
        ('Description', ticket.description or ''),
        ('Priority', ticket.priority),
        ('Status', ticket.status),
        ('Error Type', ticket.error_type or 'Not Set'),
        ('Created Date', ticket.created_at.strftime('%d-%b-%Y %I:%M %p') if ticket.created_at else ''),
        ('Updated Date', ticket.updated_at.strftime('%d-%b-%Y %I:%M %p') if ticket.updated_at else ''),
    ]
    
    for label, value in basic_info:
        ws.cell(row=row, column=1, value=label).font = label_font
        ws.cell(row=row, column=1).fill = label_fill
        ws.cell(row=row, column=1).border = thin_border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
        
        ws.cell(row=row, column=2, value=value).font = data_font
        ws.cell(row=row, column=2).border = thin_border
        ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        row += 1
    
    row += 1
    
    ws.merge_cells(f'A{row}:F{row}')
    ws[f'A{row}'] = "EMPLOYEE DETAILS"
    ws[f'A{row}'].font = section_font
    ws[f'A{row}'].fill = section_fill
    ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[row].height = 30
    row += 1
    
    emp_info = [
        ('Employee Name', ticket.employee_name),
        ('Employee ID', ticket.employee_id),
        ('Mobile', ticket.mobile),
        ('Email', ticket.email),
        ('Unit', ticket.unit.full_name if ticket.unit else ''),
        ('Department', ticket.department.name if ticket.department else ''),
        ('Screen/Module', ticket.screen_number),
    ]
    
    for label, value in emp_info:
        ws.cell(row=row, column=1, value=label).font = label_font
        ws.cell(row=row, column=1).fill = label_fill
        ws.cell(row=row, column=1).border = thin_border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
        
        ws.cell(row=row, column=2, value=value).font = data_font
        ws.cell(row=row, column=2).border = thin_border
        ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        row += 1
    
    row += 1
    
    ws.merge_cells(f'A{row}:F{row}')
    ws[f'A{row}'] = "ATTACHMENTS"
    ws[f'A{row}'].font = section_font
    ws[f'A{row}'].fill = PatternFill(start_color='8B5CF6', end_color='8B5CF6', fill_type='solid')
    ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[row].height = 30
    row += 1
    
    attachments = []
    if ticket.attachment_1:
        attachments.append({'file': ticket.attachment_1, 'name': 'Attachment 1'})
    if ticket.attachment_2:
        attachments.append({'file': ticket.attachment_2, 'name': 'Attachment 2'})
    if ticket.attachment_3:
        attachments.append({'file': ticket.attachment_3, 'name': 'Attachment 3'})
    
    if attachments:
        for idx, att in enumerate(attachments, 1):
            att_label = f"Attachment {idx}"
            att_value = att['file'].name if att['file'] else 'No file'
            ws.cell(row=row, column=1, value=att_label).font = label_font
            ws.cell(row=row, column=1).fill = label_fill
            ws.cell(row=row, column=1).border = thin_border
            ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
            
            ws.cell(row=row, column=2, value=att_value).font = data_font
            ws.cell(row=row, column=2).border = thin_border
            ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
            row += 1
    else:
        ws.cell(row=row, column=1, value="No Attachments").font = data_font
        ws.cell(row=row, column=1).border = thin_border
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        row += 1
    
    row += 1
    
    ws.merge_cells(f'A{row}:F{row}')
    ws[f'A{row}'] = "ASSIGNMENT & STATUS"
    ws[f'A{row}'].font = section_font
    ws[f'A{row}'].fill = section_fill
    ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[row].height = 30
    row += 1
    
    assign_info = [
        ('Created By Role', ticket.created_by_role),
        ('Assigned To', ticket.assigned_person or 'Not Assigned'),
        ('Hold Reason', ticket.hold_reason or ''),
        ('Vendor Ticket', ticket.vendor_ticket_number or ''),
        ('Admin Creation Reason', ticket.admin_creation_reason or ''),
    ]
    
    for label, value in assign_info:
        ws.cell(row=row, column=1, value=label).font = label_font
        ws.cell(row=row, column=1).fill = label_fill
        ws.cell(row=row, column=1).border = thin_border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
        
        ws.cell(row=row, column=2, value=value).font = data_font
        ws.cell(row=row, column=2).border = thin_border
        ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        row += 1
    
    row += 1
    
    if ticket.status == 'Closed':
        ws.merge_cells(f'A{row}:F{row}')
        ws[f'A{row}'] = "CLOSING DETAILS"
        ws[f'A{row}'].font = section_font
        ws[f'A{row}'].fill = section_fill
        ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.row_dimensions[row].height = 30
        row += 1
        
        closing_info = [
            ('Closed By', ticket.closed_by or ''),
            ('Closed Date', ticket.closed_at.strftime('%d-%b-%Y %I:%M %p') if ticket.closed_at else ''),
            ('Closing Remarks', ticket.closing_remarks or ''),
            ('Time to Close', format_timedelta_display(ticket.closed_at - ticket.created_at) if ticket.closed_at else ''),
        ]
        
        for label, value in closing_info:
            ws.cell(row=row, column=1, value=label).font = label_font
            ws.cell(row=row, column=1).fill = label_fill
            ws.cell(row=row, column=1).border = thin_border
            ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
            
            ws.cell(row=row, column=2, value=value).font = data_font
            ws.cell(row=row, column=2).border = thin_border
            ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
            row += 1
        
        row += 1
    
    ws.merge_cells(f'A{row}:F{row}')
    ws[f'A{row}'] = "AUDIT HISTORY"
    ws[f'A{row}'].font = section_font
    ws[f'A{row}'].fill = section_fill
    ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[row].height = 30
    row += 1
    
    history_headers = ['Timestamp', 'Action', 'Remarks', 'Performed By']
    for col_idx, header in enumerate(history_headers, 1):
        cell = ws.cell(row=row, column=col_idx)
        cell.value = header
        cell.font = history_header_font
        cell.fill = history_header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[row].height = 25
    row += 1
    
    for history in ticket.history.all().order_by('timestamp'):
        ws.cell(row=row, column=1, value=history.timestamp.strftime('%d-%b-%Y %I:%M %p')).font = history_data_font
        ws.cell(row=row, column=1).border = thin_border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        
        ws.cell(row=row, column=2, value=history.action).font = history_data_font
        ws.cell(row=row, column=2).border = thin_border
        ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        
        ws.cell(row=row, column=3, value=history.remarks or '').font = history_data_font
        ws.cell(row=row, column=3).border = thin_border
        ws.cell(row=row, column=3).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        
        ws.cell(row=row, column=4, value=history.performed_by).font = history_data_font
        ws.cell(row=row, column=4).border = thin_border
        ws.cell(row=row, column=4).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        row += 1
    
    row += 1
    ws.merge_cells(f'A{row}:F{row}')
    ws[f'A{row}'] = f"Report generated on {timezone.now().strftime('%d-%b-%Y %I:%M %p')} | GPLAST Support System"
    ws[f'A{row}'].font = Font(name='Calibri', size=9, italic=True, color='666666')
    ws[f'A{row}'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[row].height = 25
    
    ws.column_dimensions['A'].width = 28
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    
    ws.freeze_panes = 'A1'
    
    wb.save(response)
    return response


# ============================================================
# EXPORT CLOSED TICKETS (LAST 30 DAYS) TO EXCEL
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def export_closed_tickets_30_days(request):
    """
    Export closed tickets from the last 30 days to Excel
    """
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    tickets_qs = Ticket.objects.filter(
        status='Closed',
        closed_at__gte=thirty_days_ago
    ).order_by('-closed_at')
    
    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    now_local = now_utc.astimezone(current_tz)
    report_time = now_local.strftime('%d-%b-%Y %I:%M:%S %p')
    
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
    
    ws.merge_cells('A1:Z1')
    ws['A1'] = f"CLOSED TICKETS - LAST 30 DAYS"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 45
    
    ws.merge_cells('A2:Z2')
    ws['A2'] = f"Generated: {report_time}  |  Total Closed Tickets: {tickets_qs.count()}  |  Period: {thirty_days_ago.strftime('%d-%b-%Y')} to {timezone.now().strftime('%d-%b-%Y')}"
    ws['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 25
    
    headers = [
        'Ticket Number', 'Status', 'Unit Code', 'Unit Name', 'Department',
        'Employee ID', 'Employee Name', 'Mobile', 'Email', 'Screen/Module',
        'Subject', 'Description', 'Priority', 'Error Type', 'Created By Role',
        'Admin Creation Reason', 'Assigned Person', 'Hold Reason',
        'Closing Remarks', 'Closed By', 'Vendor Ticket Number',
        'Created At', 'Closed At', 'Time to Close', 'Escalated At',
        'Attachment 1', 'Attachment 2', 'Attachment 3'
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
        if ticket.created_at:
            if timezone.is_naive(ticket.created_at):
                utc_time = timezone.make_aware(ticket.created_at, timezone.utc)
            else:
                utc_time = ticket.created_at
            created_at_local = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            created_at_local = ''
        
        if ticket.closed_at:
            if timezone.is_naive(ticket.closed_at):
                utc_time = timezone.make_aware(ticket.closed_at, timezone.utc)
            else:
                utc_time = ticket.closed_at
            closed_at_local = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            closed_at_local = ''
        
        if ticket.escalated_at:
            if timezone.is_naive(ticket.escalated_at):
                utc_time = timezone.make_aware(ticket.escalated_at, timezone.utc)
            else:
                utc_time = ticket.escalated_at
            escalated_at_local = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            escalated_at_local = ''
        
        time_to_close = ''
        if ticket.created_at and ticket.closed_at:
            duration = ticket.closed_at - ticket.created_at
            days = duration.days
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if days > 0:
                time_to_close = f"{days}d {hours}h {minutes}m"
            else:
                time_to_close = f"{hours}h {minutes}m"
        
        row_data = [
            ticket.ticket_number,
            ticket.status,
            ticket.unit.code if ticket.unit else '',
            ticket.unit.full_name if ticket.unit else '',
            ticket.department.name if ticket.department else '',
            ticket.employee_id,
            ticket.employee_name,
            ticket.mobile,
            ticket.email,
            ticket.screen_number,
            ticket.subject,
            ticket.description or '',
            ticket.priority,
            ticket.error_type or '',
            ticket.created_by_role,
            ticket.admin_creation_reason or '',
            ticket.assigned_person or '',
            ticket.hold_reason or '',
            ticket.closing_remarks or '',
            ticket.closed_by or '',
            ticket.vendor_ticket_number or '',
            created_at_local,
            closed_at_local,
            time_to_close,
            escalated_at_local,
            ticket.attachment_1.name if ticket.attachment_1 else '',
            ticket.attachment_2.name if ticket.attachment_2 else '',
            ticket.attachment_3.name if ticket.attachment_3 else '',
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
        'P': 25, 'Q': 20, 'R': 20, 'S': 30, 'T': 18,
        'U': 18, 'V': 22, 'W': 22, 'X': 16, 'Y': 22,
        'Z': 30, 'AA': 30, 'AB': 30
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    wb.save(response)
    return response


# ============================================================
# REPORTS VIEW
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def reports(request):
    """
    Reports page with advanced filtering and export
    """
    tickets_qs = Ticket.objects.all().order_by('-created_at')
    units = Unit.objects.all()
    departments = Department.objects.all()
    
    unit_id = request.GET.get('unit', '').strip()
    dept_id = request.GET.get('department', '').strip()
    priority = request.GET.get('priority', '').strip()
    status = request.GET.get('status', '').strip()
    assigned_person = request.GET.get('assigned_person', '').strip()
    created_by_role = request.GET.get('created_by_role', '').strip()
    error_type = request.GET.get('error_type', '').strip()
    vendor_ticket = request.GET.get('vendor_ticket_number', '').strip()
    
    created_start = request.GET.get('created_start', '').strip()
    created_end = request.GET.get('created_end', '').strip()
    closed_start = request.GET.get('closed_start', '').strip()
    closed_end = request.GET.get('closed_end', '').strip()
    escalated_start = request.GET.get('escalated_start', '').strip()
    escalated_end = request.GET.get('escalated_end', '').strip()
    
    category = request.GET.get('category', 'all').strip()
    is_reopened = request.GET.get('is_reopened', '').strip()
    
    employees = EmployeeMaster.objects.filter(is_active=True, can_assign_ticket=True).order_by('employee_name')
    
    if category == 'open': 
        tickets_qs = tickets_qs.filter(status='Open')
    elif category == 'assigned': 
        tickets_qs = tickets_qs.filter(status='Assigned')
    elif category == 'hold': 
        tickets_qs = tickets_qs.filter(status='Hold')
    elif category == 'escalated': 
        tickets_qs = tickets_qs.filter(status='Escalated')
    elif category == 'closed': 
        tickets_qs = tickets_qs.filter(status='Closed')
    elif category == 'escalated_closed': 
        tickets_qs = tickets_qs.filter(status='Closed', escalated_at__isnull=False)
    elif category == 'reopened': 
        tickets_qs = tickets_qs.filter(history__action='Ticket Reopened').distinct()
    
    if unit_id and unit_id != '': 
        tickets_qs = tickets_qs.filter(unit_id=unit_id)
    if dept_id and dept_id != '': 
        tickets_qs = tickets_qs.filter(department_id=dept_id)
    if priority and priority != '': 
        tickets_qs = tickets_qs.filter(priority=priority)
    if status and status != '': 
        tickets_qs = tickets_qs.filter(status=status)
    if assigned_person and assigned_person != '': 
        tickets_qs = tickets_qs.filter(assigned_person__icontains=assigned_person)
    if created_by_role and created_by_role != '': 
        tickets_qs = tickets_qs.filter(created_by_role=created_by_role)
    if error_type and error_type != '': 
        tickets_qs = tickets_qs.filter(error_type=error_type)
    if vendor_ticket and vendor_ticket != '': 
        tickets_qs = tickets_qs.filter(vendor_ticket_number__icontains=vendor_ticket)
    
    current_tz = timezone.get_current_timezone()
    
    if created_start and created_start != '':
        try:
            created_start_date = datetime.strptime(created_start, '%Y-%m-%d').date()
            start_dt = datetime.combine(created_start_date, datetime.min.time())
            from_datetime = timezone.make_aware(start_dt, current_tz)
            tickets_qs = tickets_qs.filter(created_at__gte=from_datetime)
        except ValueError:
            pass
    
    if created_end and created_end != '':
        try:
            created_end_date = datetime.strptime(created_end, '%Y-%m-%d').date()
            end_dt = datetime.combine(created_end_date, datetime.max.time())
            to_datetime = timezone.make_aware(end_dt, current_tz)
            tickets_qs = tickets_qs.filter(created_at__lte=to_datetime)
        except ValueError:
            pass
    
    if closed_start and closed_start != '':
        try:
            closed_start_date = datetime.strptime(closed_start, '%Y-%m-%d').date()
            start_dt = datetime.combine(closed_start_date, datetime.min.time())
            from_datetime = timezone.make_aware(start_dt, current_tz)
            tickets_qs = tickets_qs.filter(closed_at__gte=from_datetime)
        except ValueError:
            pass
    
    if closed_end and closed_end != '':
        try:
            closed_end_date = datetime.strptime(closed_end, '%Y-%m-%d').date()
            end_dt = datetime.combine(closed_end_date, datetime.max.time())
            to_datetime = timezone.make_aware(end_dt, current_tz)
            tickets_qs = tickets_qs.filter(closed_at__lte=to_datetime)
        except ValueError:
            pass
    
    if escalated_start and escalated_start != '':
        try:
            escalated_start_date = datetime.strptime(escalated_start, '%Y-%m-%d').date()
            start_dt = datetime.combine(escalated_start_date, datetime.min.time())
            from_datetime = timezone.make_aware(start_dt, current_tz)
            tickets_qs = tickets_qs.filter(escalated_at__gte=from_datetime)
        except ValueError:
            pass
    
    if escalated_end and escalated_end != '':
        try:
            escalated_end_date = datetime.strptime(escalated_end, '%Y-%m-%d').date()
            end_dt = datetime.combine(escalated_end_date, datetime.max.time())
            to_datetime = timezone.make_aware(end_dt, current_tz)
            tickets_qs = tickets_qs.filter(escalated_at__lte=to_datetime)
        except ValueError:
            pass
    
    if is_reopened == 'yes': 
        tickets_qs = tickets_qs.filter(history__action='Ticket Reopened').distinct()
    elif is_reopened == 'no': 
        tickets_qs = tickets_qs.exclude(history__action='Ticket Reopened')
    
    total_count = tickets_qs.count()
    open_count = tickets_qs.filter(status='Open').count()
    assigned_count = tickets_qs.filter(status='Assigned').count()
    hold_count = tickets_qs.filter(status='Hold').count()
    escalated_count = tickets_qs.filter(status='Escalated').count()
    closed_count = tickets_qs.filter(status='Closed').count()
    
    if 'export' in request.GET:
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=GPLAST_Report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Tickets Report"
        
        title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        data_font = Font(name='Calibri', size=11)
        title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
        header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
        thin_border = Border(
            left=Side(style='thin', color='D0D0D0'),
            right=Side(style='thin', color='D0D0D0'),
            top=Side(style='thin', color='D0D0D0'),
            bottom=Side(style='thin', color='D0D0D0')
        )
        
        now_utc = timezone.now()
        if timezone.is_naive(now_utc):
            now_utc = timezone.make_aware(now_utc, timezone.utc)
        now_local = now_utc.astimezone(current_tz)
        report_time = now_local.strftime('%d-%b-%Y %I:%M:%S %p')
        
        ws.merge_cells('A1:Y1')
        ws['A1'] = f"GPLAST TICKET REPORT - Generated: {report_time}  |  Total Entries: {tickets_qs.count()}"
        ws['A1'].font = title_font
        ws['A1'].fill = title_fill
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 45
        
        headers = ["Ticket Number","Status","Unit Code","Unit Full Name","Department","Employee ID","Employee Name","Mobile","Email","Screen Number","Subject","Description","Priority","Error Type","Created By Role","Time to Close","Admin Reason","Assigned Person","Hold Reason","Closing Remarks","Closed By","Vendor Ticket","Created At","Closed At","Escalated At"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border
        ws.row_dimensions[3].height = 25
        
        row_idx = 4
        for t in tickets_qs:
            if t.created_at:
                if timezone.is_naive(t.created_at):
                    utc_time = timezone.make_aware(t.created_at, timezone.utc)
                else:
                    utc_time = t.created_at
                c_at = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
            else:
                c_at = ""
            
            if t.closed_at:
                if timezone.is_naive(t.closed_at):
                    utc_time = timezone.make_aware(t.closed_at, timezone.utc)
                else:
                    utc_time = t.closed_at
                cl_at = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
            else:
                cl_at = ""
            
            if t.escalated_at:
                if timezone.is_naive(t.escalated_at):
                    utc_time = timezone.make_aware(t.escalated_at, timezone.utc)
                else:
                    utc_time = t.escalated_at
                esc_at = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
            else:
                esc_at = ""
            
            ttc = format_timedelta_display(t.closed_at - t.created_at) if t.status == 'Closed' and t.created_at and t.closed_at else ""
            
            row_data = [
                t.ticket_number,
                t.status,
                t.unit.code if t.unit else '',
                t.unit.full_name if t.unit else '',
                t.department.name if t.department else '',
                t.employee_id,
                t.employee_name,
                t.mobile,
                t.email,
                t.screen_number,
                t.subject,
                t.description,
                t.priority,
                t.error_type,
                t.created_by_role,
                ttc,
                t.admin_creation_reason or '',
                t.assigned_person or '',
                t.hold_reason or '',
                t.closing_remarks or '',
                t.closed_by or '',
                t.vendor_ticket_number or '',
                c_at,
                cl_at,
                esc_at
            ]
            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = val
                cell.font = data_font
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                cell.border = thin_border
            row_idx += 1
        
        column_widths = {
            'A': 18, 'B': 14, 'C': 14, 'D': 25, 'E': 20,
            'F': 14, 'G': 22, 'H': 16, 'I': 25, 'J': 16,
            'K': 30, 'L': 40, 'M': 14, 'N': 20, 'O': 18,
            'P': 16, 'Q': 20, 'R': 20, 'S': 20, 'T': 30,
            'U': 18, 'V': 18, 'W': 22, 'X': 22, 'Y': 22
        }
        
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width
        
        wb.save(response)
        return response
    
    paginator = Paginator(tickets_qs, 15)
    page_number = request.GET.get('page')
    try: 
        tickets_page = paginator.page(page_number)
    except PageNotAnInteger: 
        tickets_page = paginator.page(1)
    except EmptyPage: 
        tickets_page = paginator.page(paginator.num_pages)
    
    error_type_choices = Ticket.objects.filter(
        error_type__isnull=False
    ).exclude(
        error_type__exact=''
    ).values_list('error_type', flat=True).distinct().order_by('error_type')
    
    error_type_choices_list = [(et, et) for et in error_type_choices]
    
    context = {
        'tickets': tickets_page,
        'total_count': total_count,
        'open_count': open_count,
        'assigned_count': assigned_count,
        'hold_count': hold_count,
        'escalated_count': escalated_count,
        'closed_count': closed_count,
        'units': units,
        'departments': departments,
        'employees': employees,
        'category': category,
        'is_reopened': is_reopened,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'created_by_choices': Ticket.CREATED_BY_CHOICES,
        'error_type_choices': error_type_choices_list,
        'selected_unit': unit_id,
        'selected_department': dept_id,
        'selected_status': status,
        'selected_priority': priority,
        'selected_assigned_person': assigned_person,
        'selected_created_by_role': created_by_role,
        'selected_error_type': error_type,
        'selected_vendor_ticket': vendor_ticket,
        'created_start': created_start,
        'created_end': created_end,
        'closed_start': closed_start,
        'closed_end': closed_end,
        'escalated_start': escalated_start,
        'escalated_end': escalated_end,
    }
    return render(request, 'admin_panel/reports.html', context)


# ============================================================
# NOTIFICATION FUNCTIONS
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def get_notifications(request):
    """
    Get unviewed tickets for AJAX dropdown refresh
    """
    unviewed_count = Ticket.objects.filter(is_viewed=False).count()
    unviewed_tickets = Ticket.objects.filter(is_viewed=False).order_by('-created_at')[:10]
    
    html = render_to_string('admin_panel/_notification_items.html', {
        'unviewed_tickets': unviewed_tickets,
        'unviewed_count': unviewed_count,
    }, request=request)
    
    return JsonResponse({
        'success': True,
        'html': html,
        'count': unviewed_count
    })


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def mark_all_notifications_read(request):
    """
    Mark all tickets as viewed
    """
    if request.method == 'POST':
        count = Ticket.objects.filter(is_viewed=False).update(
            is_viewed=True,
            viewed_at=timezone.now()
        )
        return JsonResponse({
            'success': True,
            'message': f'Marked {count} tickets as read',
            'count': 0
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def mark_notification_read(request, ticket_id):
    """
    Mark a single ticket as viewed
    """
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        ticket.is_viewed = True
        ticket.viewed_at = timezone.now()
        ticket.save()
        return JsonResponse({
            'success': True,
            'message': f'Ticket {ticket.ticket_number} marked as read'
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# ============================================================
# TEST NOTIFICATIONS
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def test_notifications(request): 
    return render(request, 'admin_panel/test_notifications.html')


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def test_success_message(request): 
    messages.success(request, 'Test success message.')
    return redirect('test_notifications')


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def test_error_message(request): 
    messages.error(request, 'Test error message.')
    return redirect('test_notifications')


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def test_warning_message(request): 
    messages.warning(request, 'Test warning message.')
    return redirect('test_notifications')


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def test_info_message(request): 
    messages.info(request, 'Test info message.')
    return redirect('test_notifications')


# ============================================================
# DOWNLOAD AUDIT LOG EXCEL
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def download_audit_log_excel(request):
    """
    Export filtered audit logs to Excel
    """
    audit_logs = SettingsAuditLog.objects.all().order_by('-created_at')
    
    action = request.GET.get('action', '')
    setting_type = request.GET.get('setting_type', '')
    performed_by = request.GET.get('performed_by', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    if action:
        audit_logs = audit_logs.filter(action_type=action)
    if setting_type:
        audit_logs = audit_logs.filter(setting_type=setting_type)
    if performed_by:
        audit_logs = audit_logs.filter(performed_by_name__icontains=performed_by)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            from_datetime = timezone.make_aware(
                datetime.combine(date_from_obj, datetime.min.time())
            )
            audit_logs = audit_logs.filter(created_at__gte=from_datetime)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            to_datetime = timezone.make_aware(
                datetime.combine(date_to_obj, datetime.max.time())
            )
            audit_logs = audit_logs.filter(created_at__lte=to_datetime)
        except ValueError:
            pass
    if search:
        audit_logs = audit_logs.filter(
            Q(setting_name__icontains=search) |
            Q(change_summary__icontains=search) |
            Q(performed_by_name__icontains=search)
        )
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Audit_Log_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Audit Log"
    
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
    
    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    now_local = now_utc.astimezone(current_tz)
    report_time = now_local.strftime('%d-%b-%Y %I:%M:%S %p')
    
    ws.merge_cells('A1:K1')
    ws['A1'] = f"GPLAST SETTINGS AUDIT LOG - Generated: {report_time}  |  Total Entries: {audit_logs.count()}"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 45
    
    headers = ['ID', 'Action', 'Setting Type', 'Setting Name', 'Old Value', 'New Value', 
               'Change Summary', 'Performed By', 'IP Address', 'Remarks', 'Created At']
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    ws.row_dimensions[3].height = 30
    
    row_idx = 4
    for log in audit_logs:
        ws.cell(row=row_idx, column=1, value=log.id).font = data_font
        ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal='center', vertical='center')
        ws.cell(row=row_idx, column=1).border = thin_border
        
        ws.cell(row=row_idx, column=2, value=log.get_action_type_display()).font = data_font
        ws.cell(row=row_idx, column=2).alignment = Alignment(horizontal='left', vertical='center')
        ws.cell(row=row_idx, column=2).border = thin_border
        
        ws.cell(row=row_idx, column=3, value=log.get_setting_type_display()).font = data_font
        ws.cell(row=row_idx, column=3).alignment = Alignment(horizontal='left', vertical='center')
        ws.cell(row=row_idx, column=3).border = thin_border
        
        ws.cell(row=row_idx, column=4, value=log.setting_name).font = data_font
        ws.cell(row=row_idx, column=4).alignment = Alignment(horizontal='left', vertical='center')
        ws.cell(row=row_idx, column=4).border = thin_border
        
        ws.cell(row=row_idx, column=5, value=log.old_value or '').font = data_font
        ws.cell(row=row_idx, column=5).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.cell(row=row_idx, column=5).border = thin_border
        
        ws.cell(row=row_idx, column=6, value=log.new_value or '').font = data_font
        ws.cell(row=row_idx, column=6).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.cell(row=row_idx, column=6).border = thin_border
        
        ws.cell(row=row_idx, column=7, value=log.change_summary or '').font = data_font
        ws.cell(row=row_idx, column=7).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.cell(row=row_idx, column=7).border = thin_border
        
        ws.cell(row=row_idx, column=8, value=log.performed_by_name).font = data_font
        ws.cell(row=row_idx, column=8).alignment = Alignment(horizontal='left', vertical='center')
        ws.cell(row=row_idx, column=8).border = thin_border
        
        ws.cell(row=row_idx, column=9, value=log.ip_address or 'N/A').font = data_font
        ws.cell(row=row_idx, column=9).alignment = Alignment(horizontal='left', vertical='center')
        ws.cell(row=row_idx, column=9).border = thin_border
        
        ws.cell(row=row_idx, column=10, value=log.remarks or '').font = data_font
        ws.cell(row=row_idx, column=10).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.cell(row=row_idx, column=10).border = thin_border
        
        if log.created_at:
            if timezone.is_naive(log.created_at):
                utc_time = timezone.make_aware(log.created_at, timezone.utc)
            else:
                utc_time = log.created_at
            local_time = utc_time.astimezone(current_tz)
            formatted_time = local_time.strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            formatted_time = ''
        
        ws.cell(row=row_idx, column=11, value=formatted_time).font = data_font
        ws.cell(row=row_idx, column=11).alignment = Alignment(horizontal='center', vertical='center')
        ws.cell(row=row_idx, column=11).border = thin_border
        
        row_idx += 1
    
    column_widths = {
        'A': 10, 'B': 20, 'C': 20, 'D': 30, 'E': 35,
        'F': 35, 'G': 40, 'H': 22, 'I': 18, 'J': 35, 'K': 25
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    wb.save(response)
    return response