from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.db import transaction
from django.contrib import messages

import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

from tickets.models import Unit, Department, AdminContact, AdminNotificationEmail, Ticket, TicketHistory
from tickets.forms import TicketForm, AdminTicketForm, AdminContactForm, UnitForm, DepartmentForm, AdminNotificationEmailForm, AdminPasswordChangeForm, AdminSetUserPasswordForm, UserSelectionForm
from tickets.utils import generate_ticket_number, send_ticket_email

# Helper: Check if user is Admin
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Custom Login Redirect View
@login_required
def role_redirect(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('employee_dashboard')

# Custom Logout View
def custom_logout(request):
    logout(request)
    return redirect('login')


# =========================================================================
# EMPLOYEE VIEWS
# =========================================================================

@login_required
@user_passes_test(lambda u: not u.is_staff, login_url='role_redirect')
def employee_dashboard(request):
    user_tickets = Ticket.objects.filter(created_by_user=request.user)
    
    # KPI Calculations
    kpis = {
        'total': user_tickets.count(),
        'open': user_tickets.filter(status='Open').count(),
        'assigned': user_tickets.filter(status='Assigned').count(),
        'hold': user_tickets.filter(status='Hold').count(),
        'escalated': user_tickets.filter(status='Escalated').count(),
        'closed': user_tickets.filter(status='Closed').count(),
        'critical': user_tickets.filter(priority='Critical').count(),
    }
    
    # Latest 5 tickets
    latest_tickets = user_tickets.order_by('-created_at')[:5]
    
    # IT Support Contact Card
    contact = AdminContact.objects.first()
    
    context = {
        'kpis': kpis,
        'latest_tickets': latest_tickets,
        'contact': contact,
    }
    return render(request, 'employee/dashboard.html', context)


@login_required
@user_passes_test(lambda u: not u.is_staff, login_url='role_redirect')
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                ticket = form.save(commit=False)
                ticket.ticket_number = generate_ticket_number()
                ticket.created_by_user = request.user
                ticket.created_by_role = 'Employee'
                ticket.status = 'Open'
                ticket.save()
                
                # History log
                TicketHistory.objects.create(
                    ticket=ticket,
                    action="Ticket Created",
                    remarks="Ticket Created by Employee",
                    performed_by="Employee"
                )
            
            # Send Email
            send_ticket_email(ticket, 'Created')
            
            messages.success(request, f"Ticket {ticket.ticket_number} created successfully!")
            return redirect('employee_dashboard')
    else:
        form = TicketForm()
        
    return render(request, 'employee/create_ticket.html', {'form': form})


@login_required
@user_passes_test(lambda u: not u.is_staff, login_url='role_redirect')
def my_tickets(request):
    # Active tickets
    active_tickets = Ticket.objects.filter(
        created_by_user=request.user
    ).exclude(status='Closed').order_by('-created_at')

    # Last 50 closed tickets
    closed_tickets = Ticket.objects.filter(
        created_by_user=request.user,
        status='Closed'
    ).order_by('-closed_at')[:50]

    all_visible = list(active_tickets) + list(closed_tickets)
    
    return render(request, 'employee/my_tickets.html', {'tickets': all_visible})


@login_required
@user_passes_test(lambda u: not u.is_staff, login_url='role_redirect')
def ticket_detail(request, pk):
    # Security: Ensure employee only views their own ticket
    ticket = get_object_or_404(Ticket, pk=pk, created_by_user=request.user)
    history = ticket.history.all().order_by('timestamp')
    
    context = {
        'ticket': ticket,
        'history': history,
    }
    return render(request, 'employee/ticket_detail.html', context)


# =========================================================================
# ADMIN VIEWS
# =========================================================================

@login_required
@user_passes_test(is_admin, login_url='role_redirect')
def admin_dashboard(request):
    all_tickets = Ticket.objects.all()
    
    # KPI Calculations
    kpis = {
        'total': all_tickets.count(),
        'open': all_tickets.filter(status='Open').count(),
        'assigned': all_tickets.filter(status='Assigned').count(),
        'hold': all_tickets.filter(status='Hold').count(),
        'escalated': all_tickets.filter(status='Escalated').count(),
        'closed': all_tickets.filter(status='Closed').count(),
        'critical': all_tickets.filter(priority='Critical').count(),
    }
    
    # Chart 1: Status Distribution
    status_counts = list(all_tickets.values('status').annotate(count=Count('id')))
    chart_status = {item['status']: item['count'] for item in status_counts}
    
    # Chart 2: Unit-wise Tickets
    unit_counts = list(all_tickets.values('unit__code').annotate(count=Count('id')))
    chart_units = {item['unit__code']: item['count'] for item in unit_counts if item['unit__code']}

    # Chart 4: Priority Distribution
    prio_counts = list(all_tickets.values('priority').annotate(count=Count('id')))
    chart_priority = {item['priority']: item['count'] for item in prio_counts}

    charts_data = {
        'status': chart_status,
        'units': chart_units,
        'priority': chart_priority,
    }

    context = {
        'kpis': kpis,
        'charts_data': charts_data,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='role_redirect')
def create_ticket_admin(request):
    if request.method == 'POST':
        form = AdminTicketForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                ticket = form.save(commit=False)
                ticket.ticket_number = generate_ticket_number()
                
                # Custom history text
                if ticket.created_by_role == 'Admin':
                    hist_remark = f"Ticket created by Admin on behalf of employee (Reason: {ticket.admin_creation_reason})"
                    hist_perf = f"Admin {request.user.username}"
                    # The admin is creating it, so the admin is the user who created it.
                    ticket.created_by_user = request.user
                else:
                    hist_remark = "Ticket Created by Employee (logged by Admin)"
                    hist_perf = "Employee"
                    # Find or create the single, shared employee user.
                    # All employee-created tickets will be associated with this user.
                    employee_user, _ = User.objects.get_or_create(
                        username='GPLERPUSERS', 
                        defaults={'is_staff': False, 'password': 'pbkdf2_sha256$720000$j5xL6pS0LpGvLq3sRjVbWk$V/Hq7aYt2x531enqYm5d9f2uZdtsJ7MLd2y221C+L9s='} # GPL123USER
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
            messages.success(request, f"Ticket {ticket.ticket_number} created successfully by Admin!")
            return redirect('admin_dashboard')
    else:
        form = AdminTicketForm()
        
    return render(request, 'admin_panel/create_ticket.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='role_redirect')
def all_tickets(request):
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
    search = request.GET.get('search', '').strip()

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
    if search:
        tickets_qs = tickets_qs.filter(
            Q(ticket_number__icontains=search)
            | Q(subject__icontains=search)
            | Q(unit__code__icontains=search)
            | Q(department__name__icontains=search)
        )

    context = {
        'tickets': tickets_qs,
        'units': units,
        'departments': departments,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'created_by_choices': Ticket.CREATED_BY_CHOICES,
        'selected_status': status,
        'selected_priority': priority,
        'selected_unit': unit_id,
        'selected_department': dept_id,
        'selected_assigned_person': assigned_person,
        'selected_created_by_role': created_by_role,
        'search_query': search,
        'category': category,
    }
    return render(request, 'admin_panel/all_tickets.html', context)


@login_required
@user_passes_test(is_admin, login_url='role_redirect')
def ticket_detail_admin(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    history = ticket.history.all().order_by('timestamp')
    
    # Process actions (Assign, Hold, Escalate, Close)
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
                messages.success(request, f"Ticket assigned to {assigned_person}.")
                
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
                messages.success(request, "Ticket placed on Hold.")
                
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
                messages.success(request, "Ticket escalated to ERP vendor.")
                
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
                
                # Send Closed Notification Email
                send_ticket_email(ticket, 'Closed', remarks=closing_remarks)
                messages.success(request, "Ticket closed successfully.")
        
        return redirect('admin_ticket_detail', pk=pk)
        
    return render(request, 'admin_panel/ticket_detail.html', {'ticket': ticket, 'history': history})


@login_required
@user_passes_test(is_admin, login_url='role_redirect')
def reports(request):
    tickets_qs = Ticket.objects.all().order_by('-created_at')
    
    # Get all filter options
    units = Unit.objects.all()
    departments = Department.objects.all()
    
    # Filter variables
    unit_id = request.GET.get('unit')
    dept_id = request.GET.get('department')
    priority = request.GET.get('priority')
    status = request.GET.get('status')
    assigned_person = request.GET.get('assigned_person')
    created_by_role = request.GET.get('created_by_role')
    error_type = request.GET.get('error_type')
    vendor_ticket = request.GET.get('vendor_ticket_number')
    
    created_start = request.GET.get('created_start')
    created_end = request.GET.get('created_end')
    closed_start = request.GET.get('closed_start')
    closed_end = request.GET.get('closed_end')
    escalated_start = request.GET.get('escalated_start')
    escalated_end = request.GET.get('escalated_end')
    
    category = request.GET.get('category', 'all')

    # Apply category shortcuts
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
        # Tickets that were escalated then closed (must have escalated_at and status=Closed)
        tickets_qs = tickets_qs.filter(status='Closed', escalated_at__isnull=False)

    # Apply general filters
    if unit_id:
        tickets_qs = tickets_qs.filter(unit_id=unit_id)
    if dept_id:
        tickets_qs = tickets_qs.filter(department_id=dept_id)
    if priority:
        tickets_qs = tickets_qs.filter(priority=priority)
    if status and category == 'all':
        tickets_qs = tickets_qs.filter(status=status)
    if assigned_person:
        tickets_qs = tickets_qs.filter(assigned_person__icontains=assigned_person)
    if created_by_role:
        tickets_qs = tickets_qs.filter(created_by_role=created_by_role)
    if error_type:
        tickets_qs = tickets_qs.filter(error_type=error_type)
    if vendor_ticket:
        tickets_qs = tickets_qs.filter(vendor_ticket_number__icontains=vendor_ticket)

    # Date ranges
    if created_start:
        tickets_qs = tickets_qs.filter(created_at__date__gte=created_start)
    if created_end:
        tickets_qs = tickets_qs.filter(created_at__date__lte=created_end)
        
    if closed_start:
        tickets_qs = tickets_qs.filter(closed_at__date__gte=closed_start)
    if closed_end:
        tickets_qs = tickets_qs.filter(closed_at__date__lte=closed_end)
        
    if escalated_start:
        tickets_qs = tickets_qs.filter(escalated_at__date__gte=escalated_start)
    if escalated_end:
        tickets_qs = tickets_qs.filter(escalated_at__date__lte=escalated_end)

    # Handle Export
    if 'export' in request.GET:
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=GPLAST_Ticket_Report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        # Build workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Tickets Report"
        
        # Style Definitions
        title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        data_font = Font(name='Calibri', size=11)
        
        title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid') # Navy
        header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid') # Lighter Navy
        
        # Title block
        ws.merge_cells('A1:U1')
        ws['A1'] = "GPLAST ERP Support Ticket System - Export Report"
        ws['A1'].font = title_font
        ws['A1'].fill = title_fill
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 40
        
        # Headers
        headers = [
            "Ticket Number", "Status", "Unit Code", "Unit Full Name", "Department",
            "Employee ID", "Employee Name", "Mobile Number", "Email ID", "Screen Number",
            "Subject", "Description", "Priority", "Error Type", "Created By Role",
            "Admin Creation Reason", "Assigned Person", "Hold Reason", "Closing Remarks",
            "Closed By", "Vendor Ticket Number", "Created At", "Closed At", "Escalated At"
        ]
        
        ws.row_dimensions[3].height = 25
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
        # Data Rows
        row_idx = 4
        for t in tickets_qs:
            # Format Datetimes safely
            c_at = t.created_at.astimezone(timezone.get_current_timezone()).strftime('%d-%b-%Y %I:%M %p') if t.created_at else ""
            cl_at = t.closed_at.astimezone(timezone.get_current_timezone()).strftime('%d-%b-%Y %I:%M %p') if t.closed_at else ""
            esc_at = t.escalated_at.astimezone(timezone.get_current_timezone()).strftime('%d-%b-%Y %I:%M %p') if t.escalated_at else ""
            
            row_data = [
                t.ticket_number, t.status, t.unit.code, t.unit.full_name, t.department.name,
                t.employee_id, t.employee_name, t.mobile, t.email, t.screen_number,
                t.subject, t.description, t.priority, t.error_type, t.created_by_role,
                t.admin_creation_reason or "", t.assigned_person or "", t.hold_reason or "", t.closing_remarks or "",
                t.closed_by or "", t.vendor_ticket_number or "", c_at, cl_at, esc_at
            ]
            
            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = val
                cell.font = data_font
                # Align left for text, center for codes/dates
                if col_idx in [1, 2, 3, 6, 8, 13, 14, 15, 21, 22, 23, 24]:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                else:
                    cell.alignment = Alignment(horizontal='left', vertical='center')
                    
            ws.row_dimensions[row_idx].height = 20
            row_idx += 1
            
        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            for cell in col:
                if cell.row == 1:
                    continue
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
        wb.save(response)
        return response

    context = {
        'tickets': tickets_qs,
        'units': units,
        'departments': departments,
        'category': category,
    }
    return render(request, 'admin_panel/reports.html', context)


@login_required
@user_passes_test(is_admin, login_url='role_redirect')
def settings_page(request):
    # Retrieve singletons and lists
    contact_obj = AdminContact.objects.first()
    if not contact_obj:
        contact_obj = AdminContact.objects.create(admin_name="IT ADMIN", admin_phone="9999999999", admin_email="admin@gplast.com")
        
    # Ensure the shared employee user exists, create if not.
    employee_user, _ = User.objects.get_or_create(
        username='GPLERPUSERS',
        defaults={'is_staff': False, 'password': 'pbkdf2_sha256$720000$j5xL6pS0LpGvLq3sRjVbWk$V/Hq7aYt2x531enqYm5d9f2uZdtsJ7MLd2y221C+L9s='} # GPL123USER
    )

    units = Unit.objects.all().order_by('code')
    departments = Department.objects.all().order_by('unit__code', 'name')
    emails = AdminNotificationEmail.objects.all().order_by('-created_at')

    # Initialize Forms
    contact_form = AdminContactForm(instance=contact_obj)
    my_password_form = AdminPasswordChangeForm(user=request.user)
    set_user_password_form = AdminSetUserPasswordForm(user=None)
    unit_form = UnitForm()
    dept_form = DepartmentForm()
    email_form = AdminNotificationEmailForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'contact':
            contact_form = AdminContactForm(request.POST, instance=contact_obj)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, "IT Support Contact updated successfully.")
                return redirect('settings_page')
                
        elif form_type == 'unit_add':
            unit_form = UnitForm(request.POST)
            if unit_form.is_valid():
                unit = unit_form.save(commit=False)
                unit.created_by = request.user.username
                unit.save()
                messages.success(request, f"Unit {unit.code} added successfully.")
                return redirect('settings_page')
                
        elif form_type == 'unit_edit':
            unit_id = request.POST.get('unit_id')
            unit = get_object_or_404(Unit, pk=unit_id)
            # Edit code and name
            unit.code = request.POST.get('code', unit.code).strip().upper()
            unit.full_name = request.POST.get('full_name', unit.full_name).strip().upper()
            unit.save()
            messages.success(request, f"Unit {unit.code} updated successfully.")
            return redirect('settings_page')
            
        elif form_type == 'unit_toggle':
            unit_id = request.POST.get('unit_id')
            unit = get_object_or_404(Unit, pk=unit_id)
            # Toggle is_active
            unit.is_active = not unit.is_active
            unit.save()
            status_str = "activated" if unit.is_active else "deactivated"
            messages.success(request, f"Unit {unit.code} has been {status_str}.")
            return redirect('settings_page')
            
        elif form_type == 'dept_add':
            dept_form = DepartmentForm(request.POST)
            if dept_form.is_valid():
                dept = dept_form.save()
                messages.success(request, f"Department {dept.name} added under unit {dept.unit.code}.")
                return redirect('settings_page')
                
        elif form_type == 'dept_edit':
            dept_id = request.POST.get('dept_id')
            dept = get_object_or_404(Department, pk=dept_id)
            dept.name = request.POST.get('name', dept.name).strip().upper()
            dept.save()
            messages.success(request, f"Department {dept.name} updated successfully.")
            return redirect('settings_page')
            
        elif form_type == 'dept_toggle':
            dept_id = request.POST.get('dept_id')
            dept = get_object_or_404(Department, pk=dept_id)
            dept.is_active = not dept.is_active
            dept.save()
            status_str = "activated" if dept.is_active else "deactivated"
            messages.success(request, f"Department {dept.name} has been {status_str}.")
            return redirect('settings_page')
            
        elif form_type == 'email_add':
            email_form = AdminNotificationEmailForm(request.POST)
            if email_form.is_valid():
                email = email_form.save()
                messages.success(request, f"Notification email {email.email} added.")
                return redirect('settings_page')
                
        elif form_type == 'email_delete':
            email_id = request.POST.get('email_id')
            email_obj = get_object_or_404(AdminNotificationEmail, pk=email_id)
            email_str = email_obj.email
            email_obj.delete()
            messages.success(request, f"Notification email {email_str} deleted.")
            return redirect('settings_page')
            
        elif form_type == 'change_my_password':
            my_password_form = AdminPasswordChangeForm(user=request.user, data=request.POST)
            if my_password_form.is_valid():
                user = my_password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password was successfully updated!')
                return redirect('settings_page')
            else:
                messages.error(request, 'Please correct the error below.')

        elif form_type == 'set_user_password':
            user_id = request.POST.get('user')
            selected_user = get_object_or_404(User, pk=user_id, is_staff=False)
            set_user_password_form = AdminSetUserPasswordForm(user=selected_user, data=request.POST)
            
            if set_user_password_form.is_valid():
                set_user_password_form.save()
                messages.success(request, f"Password for user '{selected_user.username}' has been successfully reset.")
                return redirect('settings_page')
            else:
                messages.error(request, f"Failed to reset password for '{selected_user.username}'. Please correct the errors.")
                # Repopulate user selection form to show which user was selected
                user_select_form = UserSelectionForm(initial={'user': user_id})

    context = {
        'contact_form': contact_form,
        'my_password_form': my_password_form,
        'set_user_password_form': set_user_password_form,
        'employee_user': employee_user,
        'unit_form': unit_form,
        'dept_form': dept_form,
        'email_form': email_form,
        'units': units,
        'departments': departments,
        'emails': emails,
    }
    return render(request, 'admin_panel/settings.html', context)


# =========================================================================
# AJAX ENDPOINTS
# =========================================================================

def get_departments_by_unit(request):
    unit_id = request.GET.get('unit_id')
    show_all = request.GET.get('show_all', 'false') == 'true'
    
    if not unit_id:
        return JsonResponse({'departments': []})
        
    depts_qs = Department.objects.filter(unit_id=unit_id)
    if not show_all:
        depts_qs = depts_qs.filter(is_active=True)
        
    depts_qs = depts_qs.order_by('name')
    
    departments = [{'id': d.id, 'name': d.name} for d in depts_qs]
    return JsonResponse({'departments': departments})
