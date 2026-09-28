# tickets/views/admin_views.py

"""
Admin Views - Dashboard, Create Ticket, All Tickets, Ticket Detail
(Reports views moved to reports_views.py)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q, DateField, Value, CharField, OuterRef, Subquery
from django.db.models.functions import TruncMonth, Cast, Coalesce
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import logging
import json

from tickets.models import (
    Unit, Department, Ticket, TicketHistory, EmployeeMaster,
    AdminContact, AdminNotificationEmail, SettingsAuditLog, ScreenMaster,
    ERPHolderMapping, ReopenAttachment, UnitHead, TicketReply,
    ErrorTypeMain, ErrorTypeSub,   # ✅ NEW — Error Type Master
)
from tickets.forms import AdminTicketForm, CloseTicketForm, TicketReplyForm
from tickets.utils import send_ticket_email, validate_attachment

from .utils import (
    is_admin,
    format_timedelta_display,
    reopen_ticket_logic,
    generate_admin_ticket_list_html,
)

# ✅ Import reports views from separate file
from .reports_views import reports, download_ticket_excel, export_closed_tickets_30_days

logger = logging.getLogger(__name__)


# ============================================================
# HELPER — Build the error type map for the close form
# ============================================================
def _build_error_type_map():
    """
    Return a dict: { "Main Name": [ {id, name, order}, ... ], ... }
    used by the Close Ticket sheet JS to populate the sub dropdown.
    Only active mains and active subs are included.
    """
    mains = (
        ErrorTypeMain.objects
        .filter(is_active=True)
        .prefetch_related('sub_types')
        .order_by('display_order', 'name')
    )
    payload = {}
    for main in mains:
        subs = (
            main.sub_types
            .filter(is_active=True)
            .order_by('display_order', 'name')
            .values('id', 'name', 'display_order')
        )
        payload[main.name] = list(subs)
    return payload


# ============================================================
# ADMIN DASHBOARD
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
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

    total_unit_heads = UnitHead.objects.filter(is_active=True).count()

    kpis = {
        'total': all_tickets.count(),
        'open': all_tickets.filter(status='Open').count(),
        'assigned': all_tickets.filter(status='Assigned').count(),
        'hold': all_tickets.filter(status='Hold').count(),
        'escalated': all_tickets.filter(status='Escalated').count(),
        'closed': all_tickets.filter(status='Closed').count(),
        'critical': all_tickets.filter(priority='Critical').count(),
        'unviewed': unviewed_count,
        'unit_heads': total_unit_heads,
    }

    status_counts = list(all_tickets.values('status').annotate(count=Count('id')))
    chart_status = {item['status']: item['count'] for item in status_counts}

    unit_counts = list(all_tickets.filter(unit__isnull=False).values('unit_id', 'unit__code').annotate(count=Count('id')).order_by('unit__code'))
    chart_units = [{'id': item['unit_id'], 'label': item['unit__code'], 'value': item['count']} for item in unit_counts]

    prio_counts = list(all_tickets.values('priority').annotate(count=Count('id')))
    chart_priority = {item['priority']: item['count'] for item in prio_counts}

    closed_tickets = Ticket.objects.filter(status='Closed')

    main_error_counts = (
        closed_tickets
        .exclude(main_error_type__isnull=True)
        .exclude(main_error_type__exact='')
        .values('main_error_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    chart_main_error = {item['main_error_type']: item['count'] for item in main_error_counts}

    sub_error_counts = (
        closed_tickets
        .exclude(sub_error_type__isnull=True)
        .exclude(sub_error_type__exact='')
        .values('sub_error_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    chart_sub_error = {item['sub_error_type']: item['count'] for item in sub_error_counts}

    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_counts_qs = Ticket.objects.filter(created_at__gte=twelve_months_ago).annotate(
        month=TruncMonth(Cast('created_at', output_field=DateField()))
    ).values('month').annotate(count=Count('id')).order_by('month')
    chart_monthly = [{'label': item['month'].strftime('%b %Y'), 'value': item['count']} for item in monthly_counts_qs]

    charts_data = {
        'status': chart_status,
        'units': chart_units,
        'priority': chart_priority,
        'mainErrorType': chart_main_error,
        'subErrorType': chart_sub_error,
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
@user_passes_test(is_admin, login_url='login')
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

            # ✅ Desktop toast: notify admins + unit head
            try:
                from tickets.services.notify import notify_ticket_created
                notify_ticket_created(ticket, actor=request.user)
            except Exception as _e:
                logger.warning(f"notify_ticket_created failed: {_e}")

            messages.success(request, f'Ticket {ticket.ticket_number} created successfully by Admin!')
            return redirect('admin_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminTicketForm()
        form.fields['error_type'].choices = [('', 'Select Error Type'), ('New', 'New'), ('Repeated', 'Repeated')]

    all_screens = ScreenMaster.objects.all().order_by('screen_name')

    units = Unit.objects.filter(is_active=True).order_by('code')
    departments = Department.objects.filter(is_active=True).order_by('unit__code', 'name')

    return render(request, 'admin_panel/create_ticket.html', {
        'form': form,
        'employees': employees,
        'all_screens': all_screens,
        'units': units,
        'departments': departments,
    })


# ============================================================
# ALL TICKETS - ADMIN
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def all_tickets(request):
    """
    Admin ticket listing with filters, AJAX support, and pagination.
    Supports a "show" filter: active (default) / archived / all.
    """
    is_ajax = request.GET.get('ajax', False)

    if isinstance(is_ajax, str):
        is_ajax = is_ajax.lower() in ['true', '1', 'yes']

    erp_subquery = ERPHolderMapping.objects.filter(
        employee__employee_id=OuterRef('employee_id')
    ).values('erp_user_id')[:1]

    # ✅ SHOW filter: active (default), archived, or all
    show = request.GET.get('show', 'active').strip().lower()
    if show not in ('active', 'archived', 'all'):
        show = 'active'

    if show == 'archived':
        base_qs = Ticket.objects.archived_only()
    elif show == 'all':
        base_qs = Ticket.objects.with_archived()
    else:
        base_qs = Ticket.objects.all()   # default manager hides archived

    tickets_qs = base_qs.order_by('-created_at').annotate(
        erp_id=Coalesce(Subquery(erp_subquery, output_field=CharField()), Value('Not Mapped'))
    )

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

    main_error_type = request.GET.get('main_error_type', '').strip()
    sub_error_type = request.GET.get('sub_error_type', '').strip()
    erp_id = request.GET.get('erp_id', '').strip()
    screen_number = request.GET.get('screen_number', '').strip()
    filter_param = request.GET.get('filter', '').strip()

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

    if filter_param and filter_param != 'all':
        if filter_param == 'Open':
            tickets_qs = tickets_qs.filter(status='Open')
        elif filter_param == 'Assigned':
            tickets_qs = tickets_qs.filter(status='Assigned')
        elif filter_param == 'Hold':
            tickets_qs = tickets_qs.filter(status='Hold')
        elif filter_param == 'Escalated':
            tickets_qs = tickets_qs.filter(status='Escalated')
        elif filter_param == 'Closed':
            tickets_qs = tickets_qs.filter(status='Closed')
        elif filter_param == 'Critical':
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

    if main_error_type and main_error_type != '':
        tickets_qs = tickets_qs.filter(main_error_type=main_error_type)

    if sub_error_type and sub_error_type != '' and sub_error_type != 'All':
        tickets_qs = tickets_qs.filter(sub_error_type=sub_error_type)

    if screen_number:
        tickets_qs = tickets_qs.filter(screen_number=screen_number)

    if erp_id and erp_id != '':
        employee_ids_with_erp = ERPHolderMapping.objects.filter(
            erp_user_id__icontains=erp_id
        ).values_list('employee__employee_id', flat=True).distinct()
        tickets_qs = tickets_qs.filter(employee_id__in=employee_ids_with_erp)

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

    # ✅ Excel export — respects the "show" filter
    if request.GET.get('export') == 'excel':
        if show == 'archived':
            return export_archived_tickets_excel(request)
        return export_filtered_tickets_excel(request, tickets_qs, show=show)

    if is_ajax:
        try:
            tickets = tickets_qs[:50]

            tickets_data = []
            for ticket in tickets:
                tickets_data.append({
                    'id': ticket.id,
                    'ticket_number': ticket.ticket_number,
                    'subject': ticket.subject,
                    'employee_name': ticket.employee_name,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'target_date': ticket.target_date.isoformat() if ticket.target_date else None,
                    'created_at': ticket.created_at.isoformat(),
                    'unit': ticket.unit.code if ticket.unit else '',
                    'department': ticket.department.name if ticket.department else '',
                })

            return JsonResponse({
                'success': True,
                'tickets': tickets_data,
                'count': tickets_qs.count()
            })

        except Exception as e:
            logger.error(f"AJAX error in all_tickets: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Error loading tickets. Please try again.',
                'tickets': [],
                'count': 0
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
        'selected_main_error_type': main_error_type,
        'selected_sub_error_type': sub_error_type,
        'selected_erp_id': erp_id,
        'selected_screen_number': screen_number,
        'selected_show': show,
        'all_screens': ScreenMaster.objects.all().order_by('screen_name'),
    }
    return render(request, 'admin_panel/all_tickets.html', context)


# ============================================================
# TICKET DETAIL - ADMIN
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def ticket_detail_admin(request, pk):
    """
    Admin ticket detail view with full ticket management
    Includes: Assign, Hold, Escalate, Close, Reopen, Change Priority, and Target Date
    """
    ticket = get_object_or_404(Ticket.objects.with_archived(), pk=pk)

    if not ticket.is_viewed:
        ticket.is_viewed = True
        ticket.viewed_at = timezone.now()
        ticket.save()
        logger.info(f"Ticket {ticket.ticket_number} marked as viewed by {request.user.username}")

    history = ticket.history.all().order_by('timestamp')
    replies = ticket.replies.select_related('author').all()
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

    close_form = CloseTicketForm()

    # ✅ Error Type Map for the Close Ticket sheet (JS reads it from json_script)
    error_type_map = _build_error_type_map()

    erp_id = 'Not Mapped'
    if ticket.employee_id:
        erp_mapping = ERPHolderMapping.objects.filter(
            employee__employee_id=ticket.employee_id
        ).first()
        if erp_mapping:
            erp_id = erp_mapping.erp_user_id

    screen_object = ScreenMaster.objects.filter(screen_code=ticket.screen_number).first()

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        remarks = request.POST.get('remarks', '')

        with transaction.atomic():
            if action_type == 'Assign':
                assigned_person = request.POST.get('assigned_person', '').strip()
                if not assigned_person:
                    messages.error(request, "Assigned Person Name is mandatory.")
                    return redirect('admin_ticket_detail', pk=ticket.id)

                target_date_str = request.POST.get('target_date', '').strip()
                target_date = None
                if target_date_str:
                    try:
                        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        messages.error(request, "Invalid target date format.")
                        return redirect('admin_ticket_detail', pk=ticket.id)

                old_status = ticket.status
                ticket.status = 'Assigned'
                ticket.assigned_person = assigned_person
                if target_date:
                    ticket.target_date = target_date
                ticket.save()

                TicketHistory.objects.create(
                    ticket=ticket,
                    action=f"Assigned to {assigned_person}",
                    remarks=remarks + (f" | Target Date: {target_date.strftime('%d-%b-%Y')}" if target_date else ""),
                    performed_by=f"Admin {request.user.username}"
                )

                # ✅ Desktop toast: notify the assignee
                try:
                    from tickets.services.notify import notify_ticket_assigned, ticket_assignee
                    _assignee_user = ticket_assignee(ticket)
                    if _assignee_user:
                        notify_ticket_assigned(ticket, _assignee_user, actor=request.user)
                except Exception as _e:
                    logger.warning(f"notify_ticket_assigned failed: {_e}")

                messages.success(request, f'Ticket assigned to {assigned_person}. Target date set to {target_date.strftime("%d-%b-%Y") if target_date else "Not set"}.')
                return redirect('admin_ticket_detail', pk=ticket.id)

            elif action_type == 'Hold':
                hold_reason = request.POST.get('hold_reason', '').strip()
                if not hold_reason:
                    messages.error(request, "Hold Reason is mandatory.")
                    return redirect('admin_ticket_detail', pk=ticket.id)
                old_status = ticket.status
                ticket.status = 'Hold'
                ticket.hold_reason = hold_reason
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket,
                    action="Status changed to Hold",
                    remarks=f"Reason: {hold_reason}",
                    performed_by=f"Admin {request.user.username}"
                )

                # ✅ Desktop toast
                try:
                    from tickets.services.notify import notify_status_changed
                    notify_status_changed(ticket, old_status, 'Hold', actor=request.user)
                except Exception as _e:
                    logger.warning(f"notify_status_changed (Hold) failed: {_e}")

                messages.success(request, 'Ticket placed on Hold.')
                return redirect('admin_ticket_detail', pk=ticket.id)

            elif action_type == 'Escalate':
                vendor_ticket = request.POST.get('vendor_ticket_number', '').strip()
                old_status = ticket.status
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

                # ✅ Desktop toast
                try:
                    from tickets.services.notify import notify_status_changed
                    notify_status_changed(ticket, old_status, 'Escalated', actor=request.user)
                except Exception as _e:
                    logger.warning(f"notify_status_changed (Escalate) failed: {_e}")

                messages.success(request, 'Ticket escalated to ERP vendor.')
                return redirect('admin_ticket_detail', pk=ticket.id)

            elif action_type == 'Close':
                close_form = CloseTicketForm(request.POST)

                if close_form.is_valid():
                    main_error_type = close_form.cleaned_data['main_error_type']
                    sub_error_type = close_form.cleaned_data['sub_error_type']
                    closing_remarks = close_form.cleaned_data['closing_remarks']

                    old_status = ticket.status
                    ticket.status = 'Closed'
                    ticket.closing_remarks = closing_remarks
                    ticket.closed_by = request.user.username
                    ticket.closed_at = timezone.now()

                    ticket.main_error_type = main_error_type
                    ticket.sub_error_type = sub_error_type

                    ticket.save()

                    TicketHistory.objects.create(
                        ticket=ticket,
                        action=f"Closed by {request.user.username}",
                        remarks=f"Main Error: {main_error_type} | Sub Error: {sub_error_type} | {closing_remarks}",
                        performed_by=f"Admin {request.user.username}"
                    )

                    # ✅ Desktop toast
                    try:
                        from tickets.services.notify import notify_status_changed
                        notify_status_changed(ticket, old_status, 'Closed', actor=request.user)
                    except Exception as _e:
                        logger.warning(f"notify_status_changed (Close) failed: {_e}")

                    messages.success(request, 'Ticket closed successfully.')
                    return redirect('admin_ticket_detail', pk=ticket.id)
                else:
                    messages.error(request, 'Please fix the errors below.')
                    context = {
                        'ticket': ticket,
                        'history': history,
                        'employees': employees,
                        'attachments': attachments,
                        'can_reopen': can_reopen,
                        'time_to_close': time_to_close_str,
                        'reopen_time_left': reopen_time_left,
                        'reopen_deadline_iso': reopen_deadline.isoformat() if reopen_deadline else None,
                        'close_form': close_form,
                        'error_type_map': error_type_map,   # ✅ NEW
                        'erp_id': erp_id,
                        'screen_object': screen_object,
                        'replies': replies,
                        'reply_form': TicketReplyForm(),
                        'can_reply': True,
                        'admin_reply_url': reverse('admin_ticket_reply', args=[ticket.id]),
                    }
                    return render(request, 'admin_panel/ticket_detail.html', context)

            elif action_type == 'Reopen':
                if not can_reopen:
                    messages.error(request, "Cannot reopen - 48 hours elapsed.")
                    return redirect('admin_ticket_detail', pk=ticket.id)
                remarks = request.POST.get('remarks', '').strip()
                if not remarks:
                    messages.error(request, "Reason for reopening is mandatory.")
                    return redirect('admin_ticket_detail', pk=ticket.id)
                uploaded_files = request.FILES.getlist('reopen_attachments')
                try:
                    for uploaded_file in uploaded_files:
                        validate_attachment(uploaded_file)
                except ValidationError as error:
                    messages.error(request, str(error))
                    return redirect('admin_ticket_detail', pk=ticket.id)

                old_status = ticket.status
                reopen_ticket_logic(ticket, f"Admin {request.user.username}", remarks, uploaded_files)

                # ✅ Desktop toast
                try:
                    from tickets.services.notify import notify_status_changed
                    notify_status_changed(ticket, old_status, 'Open', actor=request.user)
                except Exception as _e:
                    logger.warning(f"notify_status_changed (Reopen) failed: {_e}")

                messages.success(request, 'Ticket reopened successfully.')
                return redirect('admin_ticket_detail', pk=ticket.id)

            elif action_type == 'ChangePriority':
                if ticket.status == 'Closed':
                    messages.error(request, "Cannot change priority of a closed ticket.")
                    return redirect('admin_ticket_detail', pk=ticket.id)

                new_priority = request.POST.get('new_priority', '').strip()
                priority_reason = request.POST.get('priority_reason', '').strip()

                valid_priorities = ['Critical', 'High', 'Medium', 'Low']
                if new_priority not in valid_priorities:
                    messages.error(request, "Invalid priority selected.")
                    return redirect('admin_ticket_detail', pk=ticket.id)

                if not priority_reason:
                    messages.error(request, "Please provide a reason for changing priority.")
                    return redirect('admin_ticket_detail', pk=ticket.id)

                old_priority = ticket.priority

                ticket.priority = new_priority
                ticket.save()

                history_remark = f"Priority changed from {old_priority} to {new_priority}. Reason: {priority_reason}"
                TicketHistory.objects.create(
                    ticket=ticket,
                    action="Priority Changed",
                    remarks=history_remark,
                    performed_by=f"Admin {request.user.username}"
                )

                # ✅ Desktop toast
                try:
                    from tickets.services.notify import notify_priority_changed
                    notify_priority_changed(ticket, old_priority, new_priority, actor=request.user)
                except Exception as _e:
                    logger.warning(f"notify_priority_changed failed: {_e}")

                messages.success(request, f'Priority changed from {old_priority} to {new_priority}.')
                return redirect('admin_ticket_detail', pk=ticket.id)

            elif action_type == 'UpdateTargetDate':
                target_date_str = request.POST.get('target_date', '').strip()

                if not target_date_str:
                    messages.error(request, "Target date is required.")
                    return redirect('admin_ticket_detail', pk=ticket.id)

                try:
                    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

                    if target_date < timezone.now().date():
                        messages.error(request, "Target date cannot be in the past.")
                        return redirect('admin_ticket_detail', pk=ticket.id)

                    old_target_date = ticket.target_date
                    ticket.target_date = target_date
                    ticket.save()

                    TicketHistory.objects.create(
                        ticket=ticket,
                        action="Target Date Updated",
                        remarks=f"Target date changed from {old_target_date.strftime('%d-%b-%Y') if old_target_date else 'Not set'} to {target_date.strftime('%d-%b-%Y')}",
                        performed_by=f"Admin {request.user.username}"
                    )

                    messages.success(request, f'Target date updated to {target_date.strftime("%d-%b-%Y")}.')
                    return redirect('admin_ticket_detail', pk=ticket.id)

                except ValueError:
                    messages.error(request, "Invalid date format.")
                    return redirect('admin_ticket_detail', pk=ticket.id)

        return redirect('admin_ticket_detail', pk=ticket.id)

    context = {
        'ticket': ticket,
        'history': history,
        'replies': replies,
        'reply_form': TicketReplyForm(),
        'can_reply': True,
        'admin_reply_url': reverse('admin_ticket_reply', args=[ticket.id]),
        'employees': employees,
        'attachments': attachments,
        'can_reopen': can_reopen,
        'time_to_close': time_to_close_str,
        'reopen_time_left': reopen_time_left,
        'reopen_deadline_iso': reopen_deadline.isoformat() if reopen_deadline else None,
        'close_form': close_form,
        'error_type_map': error_type_map,   # ✅ NEW
        'erp_id': erp_id,
        'screen_object': screen_object,
    }
    return render(request, 'admin_panel/ticket_detail.html', context)


# ============================================================
# ADMIN TICKET REPLY
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def admin_ticket_reply(request, ticket_id):
    """
    Admin reply to a ticket
    """
    ticket = get_object_or_404(Ticket.objects.with_archived(), id=ticket_id)

    if request.method != 'POST':
        return redirect('admin_ticket_detail', pk=ticket.id)

    form = TicketReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.ticket = ticket
        reply.author = request.user
        reply.author_name = request.user.get_full_name() or request.user.username
        reply.author_role = 'Admin'
        reply.save()

        # ✅ Desktop toast: notify creator + assignee
        try:
            from tickets.services.notify import notify_ticket_replied
            notify_ticket_replied(ticket, reply, actor=request.user)
        except Exception as _e:
            logger.warning(f"notify_ticket_replied failed: {_e}")

        messages.success(request, 'Reply added successfully.')
    else:
        messages.error(request, 'Please fix the errors below.')

    return redirect('admin_ticket_detail', pk=ticket.id)


# ============================================================
# UPDATE TARGET DATE (Standalone Endpoint)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def update_target_date(request, ticket_id):
    """
    Update the target date for an assigned ticket via AJAX
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=400)

    try:
        ticket = Ticket.objects.with_archived().get(id=ticket_id)
    except Ticket.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Ticket not found'}, status=404)

    target_date_str = request.POST.get('target_date', '').strip()

    if not target_date_str:
        return JsonResponse({'success': False, 'message': 'Target date is required'})

    try:
        from datetime import date
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

        if target_date < date.today():
            return JsonResponse({'success': False, 'message': 'Target date cannot be in the past'})

        if ticket.status not in ['Assigned', 'Open']:
            return JsonResponse({'success': False, 'message': 'Ticket must be in Assigned or Open status to set target date'})

        old_target_date = ticket.target_date
        ticket.target_date = target_date
        ticket.save()

        TicketHistory.objects.create(
            ticket=ticket,
            action="Target Date Updated",
            remarks=f"Target date changed from {old_target_date.strftime('%d-%b-%Y') if old_target_date else 'Not set'} to {target_date.strftime('%d-%b-%Y')}",
            performed_by=f"Admin {request.user.username}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Target date updated to {target_date.strftime("%d-%b-%Y")}',
            'target_date': target_date.strftime('%d-%b-%Y')
        })

    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid date format'}, status=400)


# ============================================================
# DOWNLOAD INDIVIDUAL TICKET EXCEL
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def download_individual_ticket_excel(request, ticket_id):
    """
    Download a single ticket details as Excel file
    Includes: Ticket Details, Audit History, and Replies
    """
    ticket = get_object_or_404(Ticket.objects.with_archived(), id=ticket_id)
    history = ticket.history.all().order_by('timestamp')
    replies = ticket.replies.select_related('author').all().order_by('created_at')

    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    now_local = now_utc.astimezone(current_tz)
    report_time = now_local.strftime('%d-%b-%Y %I:%M:%S %p')

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

    ws1.merge_cells('A1:F1')
    ws1['A1'] = f"GPLAST TICKET DETAILS - {ticket.ticket_number}"
    ws1['A1'].font = title_font
    ws1['A1'].fill = title_fill
    ws1['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws1.row_dimensions[1].height = 40

    row = 3

    ws1.merge_cells(f'A{row}:F{row}')
    ws1[f'A{row}'] = "BASIC INFORMATION"
    ws1[f'A{row}'].font = section_font
    ws1[f'A{row}'].fill = section_fill
    ws1[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws1.row_dimensions[row].height = 30
    row += 1

    basic_info = [
        ('Ticket Number', ticket.ticket_number),
        ('Subject', ticket.subject),
        ('Description', ticket.description or ''),
        ('Priority', ticket.priority),
        ('Status', ticket.status),
        ('Error Type', ticket.error_type or 'Not Set'),
        ('Target Date', ticket.target_date.strftime('%d-%b-%Y') if ticket.target_date else 'Not Set'),
        ('Created Date', timezone.localtime(ticket.created_at).strftime('%d-%b-%Y %I:%M %p') if ticket.created_at else ''),
        ('Updated Date', ticket.updated_at.strftime('%d-%b-%Y %I:%M %p') if ticket.updated_at else ''),
    ]

    for label, value in basic_info:
        ws1.cell(row=row, column=1, value=label).font = label_font
        ws1.cell(row=row, column=1).fill = label_fill
        ws1.cell(row=row, column=1).border = thin_border
        ws1.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

        ws1.cell(row=row, column=2, value=value).font = data_font
        ws1.cell(row=row, column=2).border = thin_border
        ws1.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws1.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        row += 1

    row += 1

    ws1.merge_cells(f'A{row}:F{row}')
    ws1[f'A{row}'] = "EMPLOYEE DETAILS"
    ws1[f'A{row}'].font = section_font
    ws1[f'A{row}'].fill = section_fill
    ws1[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws1.row_dimensions[row].height = 30
    row += 1

    emp_info = [
        ('Employee Name', ticket.employee_name),
        ('Employee ID', ticket.employee_id),
        ('Mobile', ticket.mobile or ''),
        ('Email', ticket.email or ''),
        ('Unit', ticket.unit.full_name if ticket.unit else ''),
        ('Department', ticket.department.name if ticket.department else ''),
        ('Screen/Module', ticket.screen_number),
        ('ERP ID', erp_id if ticket.employee_id else 'Not Mapped'),
    ]

    for label, value in emp_info:
        ws1.cell(row=row, column=1, value=label).font = label_font
        ws1.cell(row=row, column=1).fill = label_fill
        ws1.cell(row=row, column=1).border = thin_border
        ws1.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

        ws1.cell(row=row, column=2, value=value).font = data_font
        ws1.cell(row=row, column=2).border = thin_border
        ws1.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws1.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        row += 1

    row += 1

    ws1.merge_cells(f'A{row}:F{row}')
    ws1[f'A{row}'] = "ASSIGNMENT & STATUS"
    ws1[f'A{row}'].font = section_font
    ws1[f'A{row}'].fill = section_fill
    ws1[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws1.row_dimensions[row].height = 30
    row += 1

    assign_info = [
        ('Created By Role', ticket.created_by_role),
        ('Assigned To', ticket.assigned_person or 'Not Assigned'),
        ('Hold Reason', ticket.hold_reason or ''),
        ('Vendor Ticket', ticket.vendor_ticket_number or ''),
        ('Admin Creation Reason', ticket.admin_creation_reason or ''),
    ]

    for label, value in assign_info:
        ws1.cell(row=row, column=1, value=label).font = label_font
        ws1.cell(row=row, column=1).fill = label_fill
        ws1.cell(row=row, column=1).border = thin_border
        ws1.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

        ws1.cell(row=row, column=2, value=value).font = data_font
        ws1.cell(row=row, column=2).border = thin_border
        ws1.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws1.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        row += 1

    row += 1

    if ticket.status == 'Closed':
        ws1.merge_cells(f'A{row}:F{row}')
        ws1[f'A{row}'] = "CLOSING DETAILS"
        ws1[f'A{row}'].font = section_font
        ws1[f'A{row}'].fill = section_fill
        ws1[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws1.row_dimensions[row].height = 30
        row += 1

        time_to_close_str = ''
        if ticket.created_at and ticket.closed_at:
            duration = ticket.closed_at - ticket.created_at
            days = duration.days
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if days > 0:
                time_to_close_str = f"{days}d {hours}h {minutes}m"
            else:
                time_to_close_str = f"{hours}h {minutes}m"

        closing_info = [
            ('Closed By', ticket.closed_by or ''),
            ('Closed Date', timezone.localtime(ticket.closed_at).strftime('%d-%b-%Y %I:%M %p') if ticket.closed_at else ''),
            ('Main Error Type', ticket.main_error_type or 'N/A'),
            ('Sub Error Type', ticket.sub_error_type or 'N/A'),
            ('Closing Remarks', ticket.closing_remarks or ''),
            ('Time to Close', time_to_close_str),
        ]

        for label, value in closing_info:
            ws1.cell(row=row, column=1, value=label).font = label_font
            ws1.cell(row=row, column=1).fill = label_fill
            ws1.cell(row=row, column=1).border = thin_border
            ws1.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)

            ws1.cell(row=row, column=2, value=value).font = data_font
            ws1.cell(row=row, column=2).border = thin_border
            ws1.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            ws1.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
            row += 1

        row += 1

    ws1.merge_cells(f'A{row}:F{row}')
    ws1[f'A{row}'] = f"Report generated on {report_time} | GPLAST Support System"
    ws1[f'A{row}'].font = Font(name='Calibri', size=9, italic=True, color='666666')
    ws1[f'A{row}'].alignment = Alignment(horizontal='center', vertical='center')
    ws1.row_dimensions[row].height = 25

    ws1.column_dimensions['A'].width = 28
    ws1.column_dimensions['B'].width = 35
    ws1.column_dimensions['C'].width = 30
    ws1.column_dimensions['D'].width = 30
    ws1.column_dimensions['E'].width = 15
    ws1.column_dimensions['F'].width = 15

    # SHEET 2: AUDIT HISTORY
    ws2 = wb.create_sheet("Audit History")

    ws2.merge_cells('A1:D1')
    ws2['A1'] = f"AUDIT HISTORY - Ticket #{ticket.ticket_number}"
    ws2['A1'].font = title_font
    ws2['A1'].fill = title_fill
    ws2['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws2.row_dimensions[1].height = 40

    ws2.merge_cells('A2:D2')
    ws2['A2'] = f"Generated: {report_time}  |  Total Entries: {history.count()}"
    ws2['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws2['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws2.row_dimensions[2].height = 25

    headers2 = ['#', 'Timestamp', 'Action', 'Remarks', 'Performed By']
    for col_idx, header in enumerate(headers2, 1):
        cell = ws2.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    ws2.row_dimensions[4].height = 30

    row_idx = 5
    for idx, log in enumerate(history, 1):
        if log.timestamp:
            if timezone.is_naive(log.timestamp):
                utc_time = timezone.make_aware(log.timestamp, timezone.utc)
            else:
                utc_time = log.timestamp
            timestamp_local = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            timestamp_local = ''

        ws2.cell(row=row_idx, column=1, value=idx).font = data_font
        ws2.cell(row=row_idx, column=1).alignment = Alignment(horizontal='center', vertical='center')
        ws2.cell(row=row_idx, column=1).border = thin_border

        ws2.cell(row=row_idx, column=2, value=timestamp_local).font = data_font
        ws2.cell(row=row_idx, column=2).alignment = Alignment(horizontal='left', vertical='center')
        ws2.cell(row=row_idx, column=2).border = thin_border

        ws2.cell(row=row_idx, column=3, value=log.action).font = data_font
        ws2.cell(row=row_idx, column=3).alignment = Alignment(horizontal='left', vertical='center')
        ws2.cell(row=row_idx, column=3).border = thin_border

        ws2.cell(row=row_idx, column=4, value=log.remarks or '').font = data_font
        ws2.cell(row=row_idx, column=4).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws2.cell(row=row_idx, column=4).border = thin_border

        ws2.cell(row=row_idx, column=5, value=log.get_performed_by_display()).font = data_font
        ws2.cell(row=row_idx, column=5).alignment = Alignment(horizontal='left', vertical='center')
        ws2.cell(row=row_idx, column=5).border = thin_border

        row_idx += 1

    ws2.column_dimensions['A'].width = 8
    ws2.column_dimensions['B'].width = 22
    ws2.column_dimensions['C'].width = 30
    ws2.column_dimensions['D'].width = 50
    ws2.column_dimensions['E'].width = 22

    # SHEET 3: REPLIES
    ws3 = wb.create_sheet("Replies")

    ws3.merge_cells('A1:D1')
    ws3['A1'] = f"REPLIES - Ticket #{ticket.ticket_number}"
    ws3['A1'].font = title_font
    ws3['A1'].fill = title_fill
    ws3['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws3.row_dimensions[1].height = 40

    ws3.merge_cells('A2:D2')
    ws3['A2'] = f"Generated: {report_time}  |  Total Replies: {replies.count()}"
    ws3['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws3['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws3.row_dimensions[2].height = 25

    headers3 = ['#', 'Date/Time', 'Author', 'Reply', 'Role']
    for col_idx, header in enumerate(headers3, 1):
        cell = ws3.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    ws3.row_dimensions[4].height = 30

    row_idx = 5
    for idx, reply in enumerate(replies, 1):
        if reply.created_at:
            if timezone.is_naive(reply.created_at):
                utc_time = timezone.make_aware(reply.created_at, timezone.utc)
            else:
                utc_time = reply.created_at
            created_at_local = utc_time.astimezone(current_tz).strftime('%d-%b-%Y %I:%M:%S %p')
        else:
            created_at_local = ''

        ws3.cell(row=row_idx, column=1, value=idx).font = data_font
        ws3.cell(row=row_idx, column=1).alignment = Alignment(horizontal='center', vertical='center')
        ws3.cell(row=row_idx, column=1).border = thin_border

        ws3.cell(row=row_idx, column=2, value=created_at_local).font = data_font
        ws3.cell(row=row_idx, column=2).alignment = Alignment(horizontal='left', vertical='center')
        ws3.cell(row=row_idx, column=2).border = thin_border

        ws3.cell(row=row_idx, column=3, value=reply.author_name or 'Unknown').font = data_font
        ws3.cell(row=row_idx, column=3).alignment = Alignment(horizontal='left', vertical='center')
        ws3.cell(row=row_idx, column=3).border = thin_border

        ws3.cell(row=row_idx, column=4, value=reply.body or '').font = data_font
        ws3.cell(row=row_idx, column=4).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws3.cell(row=row_idx, column=4).border = thin_border

        ws3.cell(row=row_idx, column=5, value=reply.author_role or 'Admin').font = data_font
        ws3.cell(row=row_idx, column=5).alignment = Alignment(horizontal='left', vertical='center')
        ws3.cell(row=row_idx, column=5).border = thin_border

        row_idx += 1

    ws3.column_dimensions['A'].width = 8
    ws3.column_dimensions['B'].width = 22
    ws3.column_dimensions['C'].width = 25
    ws3.column_dimensions['D'].width = 50
    ws3.column_dimensions['E'].width = 18

    wb.save(response)
    return response


# ============================================================
# GET EMPLOYEES BY DEPARTMENT (AJAX)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def get_employees_by_department(request):
    """
    AJAX endpoint to get employees by department
    """
    department_id = request.GET.get('department_id')

    if not department_id:
        return JsonResponse({
            'success': False,
            'message': 'Department ID is required',
            'employees': [],
            'count': 0
        }, status=400)

    try:
        employees = EmployeeMaster.objects.filter(
            department_id=department_id,
            is_active=True
        ).order_by('employee_name')

        employee_data = []
        for emp in employees:
            employee_data.append({
                'id': emp.id,
                'employee_id': emp.employee_id or '',
                'employee_name': emp.employee_name or '',
                'mobile': emp.mobile or '',
                'email': emp.email or '',
                'is_active': emp.is_active,
            })

        return JsonResponse({
            'success': True,
            'employees': employee_data,
            'count': len(employee_data)
        })

    except Exception as e:
        logger.error(f"Error fetching employees by department: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'employees': [],
            'count': 0
        }, status=500)


# ============================================================
# NOTIFICATION FUNCTIONS
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='login')
def get_notifications(request):
    """
    Get unviewed tickets for AJAX dropdown refresh
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        try:
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
        except Exception as e:
            logger.error(f"Error in get_notifications: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e),
                'count': 0,
                'html': ''
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Invalid request. This endpoint only accepts AJAX requests.',
        'count': 0,
        'html': ''
    }, status=400)


@login_required
@user_passes_test(is_admin, login_url='login')
def refresh_notifications(request):
    """
    AJAX view to refresh notification dropdown content
    """
    try:
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
    except Exception as e:
        logger.error(f"Error in refresh_notifications: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'html': '',
            'count': 0
        }, status=500)


@login_required
@user_passes_test(is_admin, login_url='login')
def mark_all_notifications_read(request):
    """
    Mark all tickets as viewed
    """
    if request.method == 'POST':
        try:
            count = Ticket.objects.filter(is_viewed=False).update(
                is_viewed=True,
                viewed_at=timezone.now()
            )
            return JsonResponse({
                'success': True,
                'message': f'Marked {count} tickets as read',
                'count': 0
            })
        except Exception as e:
            logger.error(f"Error in mark_all_notifications_read: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request. Use POST.'}, status=400)


@login_required
@user_passes_test(is_admin, login_url='login')
def mark_notification_read(request, ticket_id):
    """
    Mark a single ticket as viewed
    """
    if request.method == 'POST':
        try:
            ticket = get_object_or_404(Ticket.objects.with_archived(), pk=ticket_id)
            ticket.is_viewed = True
            ticket.viewed_at = timezone.now()
            ticket.save()
            return JsonResponse({
                'success': True,
                'message': f'Ticket {ticket.ticket_number} marked as read'
            })
        except Exception as e:
            logger.error(f"Error in mark_notification_read: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request. Use POST.'}, status=400)


# ============================================================
# TEST NOTIFICATIONS
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='login')
def test_notifications(request):
    return render(request, 'admin_panel/test_notifications.html')


@login_required
@user_passes_test(is_admin, login_url='login')
def test_success_message(request):
    messages.success(request, 'Test success message.')
    return redirect('test_notifications')


@login_required
@user_passes_test(is_admin, login_url='login')
def test_error_message(request):
    messages.error(request, 'Test error message.')
    return redirect('test_notifications')


@login_required
@user_passes_test(is_admin, login_url='login')
def test_warning_message(request):
    messages.warning(request, 'Test warning message.')
    return redirect('test_notifications')


@login_required
@user_passes_test(is_admin, login_url='login')
def test_info_message(request):
    messages.info(request, 'Test info message.')
    return redirect('test_notifications')


# ============================================================
# DOWNLOAD AUDIT LOG EXCEL
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='login')
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


# ============================================================
# ARCHIVE / RESTORE VIEWS
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def restore_ticket(request, pk):
    """
    Restore a single archived ticket back to active lists.
    """
    ticket = get_object_or_404(Ticket.objects.with_archived(), pk=pk)

    if ticket.restore():
        TicketHistory.objects.create(
            ticket=ticket,
            action="Restored Ticket",
            remarks="Restored from archive by admin",
            performed_by=f"Admin {request.user.username}",
        )
        messages.success(request, f"Ticket #{ticket.ticket_number} restored.")
    else:
        messages.info(request, "Ticket is not archived.")

    return redirect(f"{reverse('all_tickets')}?show=archived")


@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def bulk_restore_tickets(request):
    """
    Restore multiple archived tickets at once.
    Reads ticket_ids[] from POST.
    """
    ids = request.POST.getlist('ticket_ids')

    if not ids:
        messages.warning(request, "No tickets selected.")
        return redirect(f"{reverse('all_tickets')}?show=archived")

    qs = Ticket.objects.with_archived().filter(pk__in=ids, is_archived=True)

    restored = 0
    for ticket in qs:
        ticket.is_archived = False
        ticket.archived_at = None
        ticket.archived_by = ""
        ticket.save(update_fields=["is_archived", "archived_at", "archived_by"])

        TicketHistory.objects.create(
            ticket=ticket,
            action="Restored Ticket",
            remarks="Bulk restored from archive",
            performed_by=f"Admin {request.user.username}",
        )
        restored += 1

    if restored == 0:
        messages.info(request, "No archived tickets matched the selection.")
    else:
        messages.success(request, f"Restored {restored} ticket(s).")

    return redirect(f"{reverse('all_tickets')}?show=archived")


@login_required
@user_passes_test(is_admin, login_url='login')
def export_archived_tickets_excel(request):
    """
    Export every archived ticket to Excel, with archive metadata.
    """
    tickets_qs = Ticket.objects.archived_only().order_by('-archived_at')

    priority = request.GET.get('priority', '').strip()
    unit_id = request.GET.get('unit', '').strip()
    search = request.GET.get('search', '').strip()

    if priority:
        tickets_qs = tickets_qs.filter(priority=priority)
    if unit_id:
        tickets_qs = tickets_qs.filter(unit_id=unit_id)
    if search:
        tickets_qs = tickets_qs.filter(
            Q(ticket_number__icontains=search) |
            Q(subject__icontains=search) |
            Q(employee_name__icontains=search)
        )

    current_tz = timezone.get_current_timezone()
    now_utc = timezone.now()
    if timezone.is_naive(now_utc):
        now_utc = timezone.make_aware(now_utc, timezone.utc)
    now_local = now_utc.astimezone(current_tz)
    report_time = now_local.strftime('%d-%b-%Y %I:%M:%S %p')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = (
        f'attachment; filename=Archived_Tickets_'
        f'{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Archived Tickets"

    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    data_font = Font(name='Calibri', size=10)
    title_fill = PatternFill(start_color='475569', end_color='475569', fill_type='solid')
    header_fill = PatternFill(start_color='64748B', end_color='64748B', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )

    ws.merge_cells('A1:S1')
    ws['A1'] = "ARCHIVED TICKETS - GPLAST SUPPORT SYSTEM"
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 45

    ws.merge_cells('A2:S2')
    ws['A2'] = (
        f"Generated: {report_time}  |  "
        f"Total Archived Tickets: {tickets_qs.count()}"
    )
    ws['A2'].font = Font(name='Calibri', size=10, italic=True, color='666666')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 25

    headers = [
        'Ticket Number', 'Subject', 'Employee ID', 'Employee Name',
        'Unit Code', 'Department', 'Priority', 'Status',
        'Created At', 'Closed At', 'Time to Close',
        'Assigned Person', 'Closed By',
        'Main Error Type', 'Sub Error Type',
        'Archived At', 'Archived By',
        'Description', 'Closing Remarks',
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

        time_to_close = ''
        if ticket.created_at and ticket.closed_at:
            d = ticket.closed_at - ticket.created_at
            time_to_close = f"{d.days}d {d.seconds // 3600}h {(d.seconds % 3600) // 60}m"

        row_data = [
            ticket.ticket_number,
            ticket.subject,
            ticket.employee_id,
            ticket.employee_name,
            ticket.unit.code if ticket.unit else '',
            ticket.department.name if ticket.department else '',
            ticket.priority,
            ticket.status,
            fmt(ticket.created_at),
            fmt(ticket.closed_at),
            time_to_close,
            ticket.assigned_person or '',
            ticket.closed_by or '',
            ticket.main_error_type or 'N/A',
            ticket.sub_error_type or 'N/A',
            fmt(ticket.archived_at),
            ticket.archived_by or '',
            ticket.description or '',
            ticket.closing_remarks or '',
        ]

        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = data_font
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = thin_border
        row_idx += 1

    widths = {
        'A': 16, 'B': 34, 'C': 14, 'D': 22, 'E': 12, 'F': 20,
        'G': 12, 'H': 12, 'I': 22, 'J': 22, 'K': 14,
        'L': 20, 'M': 18, 'N': 20, 'O': 20,
        'P': 22, 'Q': 20, 'R': 40, 'S': 34,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    wb.save(response)
    return response


# ============================================================
# DEDICATED ARCHIVE PAGE — browse and restore archived tickets
# ============================================================

@login_required
@user_passes_test(is_admin, login_url='login')
def archived_tickets(request):
    """
    Dedicated page for browsing and restoring archived tickets.
    Shows only tickets where is_archived=True.
    """
    qs = Ticket.objects.archived_only().order_by('-archived_at')

    search = request.GET.get('search', '').strip()
    priority = request.GET.get('priority', '').strip()
    unit_id = request.GET.get('unit', '').strip()
    archived_by = request.GET.get('archived_by', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if search:
        qs = qs.filter(
            Q(ticket_number__icontains=search) |
            Q(subject__icontains=search) |
            Q(employee_name__icontains=search) |
            Q(employee_id__icontains=search)
        )
    if priority:
        qs = qs.filter(priority=priority)
    if unit_id:
        qs = qs.filter(unit_id=unit_id)
    if archived_by:
        qs = qs.filter(archived_by__icontains=archived_by)

    if date_from:
        try:
            d = datetime.strptime(date_from, '%Y-%m-%d').date()
            from_dt = timezone.make_aware(datetime.combine(d, datetime.min.time()))
            qs = qs.filter(archived_at__gte=from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to, '%Y-%m-%d').date()
            to_dt = timezone.make_aware(datetime.combine(d, datetime.max.time()))
            qs = qs.filter(archived_at__lte=to_dt)
        except ValueError:
            pass

    total_archived = qs.count()
    now = timezone.now()
    today = now.date()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    archived_today = Ticket.objects.archived_only().filter(archived_at__date=today).count()
    archived_month = Ticket.objects.archived_only().filter(archived_at__gte=month_start).count()
    oldest = Ticket.objects.archived_only().order_by('archived_at').first()

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    filter_query = request.GET.copy()
    filter_query.pop('page', None)

    context = {
        'page_obj': page_obj,
        'total_archived': total_archived,
        'archived_today': archived_today,
        'archived_month': archived_month,
        'oldest_archive': oldest.archived_at if oldest else None,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'units': Unit.objects.filter(is_active=True).order_by('code'),
        'selected_search': search,
        'selected_priority': priority,
        'selected_unit': unit_id,
        'selected_archived_by': archived_by,
        'date_from': date_from,
        'date_to': date_to,
        'filter_query': filter_query.urlencode(),
    }
    return render(request, 'admin_panel/archived_tickets.html', context)