from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from tickets.models import (
    Ticket, 
    Unit, 
    Department, 
    AdminContact,           
    AdminNotificationEmail, 
    EmployeeMaster,         
    TicketHistory           
)
from tickets.forms import TicketForm
from tickets.utils import send_ticket_email  # ✅ IMPORT THIS
import logging

logger = logging.getLogger(__name__)


@login_required
def employee_dashboard(request):
    """Employee dashboard view"""
    contact = AdminContact.objects.first()
    
    if request.user.is_staff:
        tickets = Ticket.objects.all()
    else:
        tickets = Ticket.objects.filter(
            Q(created_by_user=request.user) | 
            Q(assigned_person__icontains=request.user.username)
        ).distinct()
    
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
        'dept_priority': dict(tickets.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
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
    except:
        pass
    
    context = {
        'kpis': kpis,
        'charts_data': charts_data,
        'latest_tickets': latest_tickets,
        'contact': contact,
        'show_department_tickets': show_department_tickets,
        'department_name': department_name,
        'unit_name': unit_name,
    }
    return render(request, 'employee/dashboard.html', context)


@login_required
def create_ticket(request):
    """Create a new ticket"""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by_user = request.user
            ticket.created_by_role = 'Employee'
            ticket.save()
            
            TicketHistory.objects.create(
                ticket=ticket,
                action='Created Ticket',
                remarks='Ticket created by employee',
                performed_by=request.user.username
            )
            
            # ✅ SEND EMAIL NOTIFICATION
            try:
                send_ticket_email(ticket, 'Created')
                logger.info(f"Email sent for ticket {ticket.ticket_number}")
            except Exception as e:
                logger.error(f"Failed to send email for ticket {ticket.ticket_number}: {e}")
            
            messages.success(request, f'Ticket #{ticket.ticket_number} created successfully!')
            return redirect('ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketForm()
    
    units = Unit.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'units': units,
        'departments': departments,
    }
    return render(request, 'employee/create_ticket.html', context)


@login_required
def all_tickets(request):
    """View all tickets"""
    tickets = Ticket.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(employee_name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    is_ajax = request.GET.get('ajax', False)
    if is_ajax:
        tickets = tickets[:50]
        html = render_to_string('employee/_ticket_list_modal.html', {
            'tickets': tickets,
        }, request=request)
        return JsonResponse({
            'html': html,
            'success': True,
            'count': tickets.count()
        })
    
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }
    return render(request, 'employee/all_tickets.html', context)


@login_required
def my_tickets(request):
    """View tickets created by the logged-in user"""
    tickets = Ticket.objects.filter(created_by_user=request.user).order_by('-created_at')
    
    total = tickets.count()
    open_tickets = tickets.filter(status='Open').count()
    assigned_tickets = tickets.filter(status='Assigned').count()
    hold_tickets = tickets.filter(status='Hold').count()
    escalated_tickets = tickets.filter(status='Escalated').count()
    closed_tickets = tickets.filter(status='Closed').count()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(employee_name__icontains=search_query)
        )
    
    is_ajax = request.GET.get('ajax', False)
    if is_ajax:
        tickets = tickets[:50]
        html = render_to_string('employee/_ticket_list_modal.html', {
            'tickets': tickets,
        }, request=request)
        return JsonResponse({
            'html': html,
            'success': True,
            'count': tickets.count()
        })
    
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total': total,
        'open_tickets': open_tickets,
        'assigned_tickets': assigned_tickets,
        'hold_tickets': hold_tickets,
        'escalated_tickets': escalated_tickets,
        'closed_tickets': closed_tickets,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    }
    return render(request, 'employee/my_tickets.html', context)


@login_required
def employee_ticket_detail(request, ticket_id):
    """View ticket details"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    history = TicketHistory.objects.filter(ticket=ticket).order_by('timestamp')
    
    can_reopen = False
    reopen_deadline_iso = ''
    if ticket.status == 'Closed' and ticket.closed_at:
        time_diff = timezone.now() - ticket.closed_at
        if time_diff.total_seconds() <= 48 * 3600:
            can_reopen = True
            reopen_deadline = ticket.closed_at + timezone.timedelta(hours=48)
            reopen_deadline_iso = reopen_deadline.isoformat()
    
    time_to_close = 'N/A'
    if ticket.closed_at and ticket.created_at:
        time_diff = ticket.closed_at - ticket.created_at
        hours = time_diff.total_seconds() / 3600
        if hours < 1:
            minutes = int(time_diff.total_seconds() / 60)
            time_to_close = f'{minutes} minutes'
        else:
            time_to_close = f'{hours:.1f} hours'
    
    employees = EmployeeMaster.objects.filter(is_active=True)
    
    context = {
        'ticket': ticket,
        'history': history,
        'can_reopen': can_reopen,
        'reopen_deadline_iso': reopen_deadline_iso,
        'time_to_close': time_to_close,
        'employees': employees,
    }
    return render(request, 'employee/ticket_detail.html', context)


@login_required
def ticket_detail(request, ticket_id):
    """Alias for employee_ticket_detail"""
    return employee_ticket_detail(request, ticket_id)


@login_required
def download_ticket_excel(request, ticket_id):
    """Download ticket details as Excel file"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ticket Details"
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="FF6B00", end_color="FF6B00", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    headers = ['Field', 'Value']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    data = [
        ['Ticket Number', ticket.ticket_number],
        ['Subject', ticket.subject],
        ['Employee Name', ticket.employee_name],
        ['Employee ID', ticket.employee_id],
        ['Email', ticket.email],
        ['Mobile', ticket.mobile],
        ['Unit', ticket.unit.full_name if ticket.unit else ''],
        ['Department', ticket.department.name if ticket.department else ''],
        ['Screen/Module', ticket.screen_number],
        ['Priority', ticket.priority],
        ['Status', ticket.status],
        ['Error Type', ticket.error_type],
        ['Description', ticket.description],
        ['Assigned To', ticket.assigned_person or 'Not Assigned'],
        ['Created At', ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')],
        ['Updated At', ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    if ticket.closed_at:
        data.append(['Closed At', ticket.closed_at.strftime('%Y-%m-%d %H:%M:%S')])
        data.append(['Closed By', ticket.closed_by or ''])
        data.append(['Closing Remarks', ticket.closing_remarks or ''])
    
    if ticket.vendor_ticket_number:
        data.append(['Vendor Ticket', ticket.vendor_ticket_number])
    
    for row_idx, (field, value) in enumerate(data, 2):
        ws.cell(row=row_idx, column=1, value=field)
        ws.cell(row=row_idx, column=2, value=value)
    
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 50
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=ticket_{ticket.ticket_number}.xlsx'
    wb.save(response)
    
    return response


@login_required
def update_ticket_status(request, ticket_id):
    """Update ticket status (Assign, Hold, Escalate, Close, Reopen)"""
    if request.method != 'POST':
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    action_type = request.POST.get('action_type')
    
    if action_type == 'Assign':
        assigned_person = request.POST.get('assigned_person')
        remarks = request.POST.get('remarks', '')
        
        if assigned_person:
            ticket.assigned_person = assigned_person
            ticket.status = 'Assigned'
            ticket.save()
            
            TicketHistory.objects.create(
                ticket=ticket,
                action=f'Assigned to {assigned_person}',
                remarks=remarks,
                performed_by=request.user.username
            )
            messages.success(request, f'Ticket assigned to {assigned_person}')
        else:
            messages.error(request, 'Please select an employee to assign')
    
    elif action_type == 'Hold':
        hold_reason = request.POST.get('hold_reason')
        if hold_reason:
            ticket.hold_reason = hold_reason
            ticket.status = 'Hold'
            ticket.save()
            
            TicketHistory.objects.create(
                ticket=ticket,
                action='Put on Hold',
                remarks=hold_reason,
                performed_by=request.user.username
            )
            messages.success(request, 'Ticket put on hold')
        else:
            messages.error(request, 'Please provide a reason for holding')
    
    elif action_type == 'Escalate':
        vendor_ticket = request.POST.get('vendor_ticket_number', '')
        remarks = request.POST.get('remarks', '')
        
        if vendor_ticket:
            ticket.vendor_ticket_number = vendor_ticket
        ticket.status = 'Escalated'
        ticket.escalated_at = timezone.now()
        ticket.save()
        
        TicketHistory.objects.create(
            ticket=ticket,
            action='Escalated to Vendor',
            remarks=f'Vendor Ticket: {vendor_ticket or "N/A"} - {remarks}',
            performed_by=request.user.username
        )
        messages.success(request, 'Ticket escalated successfully')
    
    elif action_type == 'Close':
        error_type = request.POST.get('error_type')
        closing_remarks = request.POST.get('closing_remarks')
        
        if error_type and closing_remarks:
            ticket.error_type = error_type
            ticket.closing_remarks = closing_remarks
            ticket.status = 'Closed'
            ticket.closed_by = request.user.username
            ticket.closed_at = timezone.now()
            ticket.save()
            
            TicketHistory.objects.create(
                ticket=ticket,
                action='Closed Ticket',
                remarks=f'Error Type: {error_type}\nClosing Remarks: {closing_remarks}',
                performed_by=request.user.username
            )
            
            # ✅ SEND EMAIL FOR CLOSING
            try:
                send_ticket_email(ticket, 'Closed', remarks=closing_remarks)
            except Exception as e:
                logger.error(f"Failed to send closing email: {e}")
            
            messages.success(request, 'Ticket closed successfully')
        else:
            messages.error(request, 'Please provide both error type and closing remarks')
    
    elif action_type == 'Reopen':
        remarks = request.POST.get('remarks', '')
        
        if remarks:
            if ticket.closed_at and (timezone.now() - ticket.closed_at).total_seconds() <= 48 * 3600:
                ticket.status = 'Open'
                ticket.closed_at = None
                ticket.closed_by = None
                ticket.closing_remarks = ''
                ticket.save()
                
                TicketHistory.objects.create(
                    ticket=ticket,
                    action='Reopened Ticket',
                    remarks=remarks,
                    performed_by=request.user.username
                )
                
                # ✅ SEND EMAIL FOR REOPEN
                try:
                    send_ticket_email(ticket, 'Reopened', remarks=remarks)
                except Exception as e:
                    logger.error(f"Failed to send reopen email: {e}")
                
                messages.success(request, 'Ticket reopened successfully')
            else:
                messages.error(request, 'Cannot reopen ticket after 48 hours')
        else:
            messages.error(request, 'Please provide a reason for reopening')
    
    return redirect('ticket_detail', ticket_id=ticket_id)