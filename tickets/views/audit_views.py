# tickets/views/audit_views.py

"""
Views for the Settings Audit Log page and its Excel export.
"""

from datetime import datetime, time, timedelta

import openpyxl
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from openpyxl.styles import Alignment, Font, PatternFill

from tickets.models import SettingsAuditLog

# ✅ utils.py lives in the SAME folder as this file (tickets/views/utils.py)
from .utils import is_admin


DATE_FORMAT = '%Y-%m-%d'

# Allowed page sizes for the audit log
DEFAULT_PER_PAGE = 50
ALLOWED_PER_PAGE = [25, 50, 100, 200]

# Windowed pagination: how many pages on each side of the current page.
# Total numbered buttons shown ≈ (2 * WINDOW) + 5.
PAGINATION_WINDOW = 2
ELLIPSIS = '…'


def _parse_date(value):
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except (TypeError, ValueError):
        return None


def _parse_per_page(value):
    """
    Coerce the ?per_page= query param into one of the allowed values.
    Falls back to DEFAULT_PER_PAGE for anything invalid or out of range.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PER_PAGE
    return n if n in ALLOWED_PER_PAGE else DEFAULT_PER_PAGE


def _build_page_window(current, total, window=PAGINATION_WINDOW):
    """
    Return a list of page numbers (and '…' ellipsis markers) to render.

    Examples:
        current=3, total=94  → [1, 2, 3, 4, 5, '…', 94]
        current=47, total=94 → [1, '…', 45, 46, 47, 48, 49, '…', 94]
        current=92, total=94 → [1, '…', 90, 91, 92, 93, 94]
        current=3, total=5   → [1, 2, 3, 4, 5]
    """
    if total <= (2 * window) + 5:
        return list(range(1, total + 1))

    pages = set()
    pages.add(1)
    pages.add(total)

    # Window around the current page
    for i in range(current - window, current + window + 1):
        if 1 <= i <= total:
            pages.add(i)

    # Edge padding near the ends
    if current <= window + 1:
        for i in range(2, min(2 * window + 2, total)):
            pages.add(i)
    if current >= total - window:
        for i in range(max(2, total - 2 * window), total):
            pages.add(i)

    ordered = sorted(pages)

    # Insert ellipsis where numbers skip
    result = []
    for idx, num in enumerate(ordered):
        if idx > 0:
            prev = ordered[idx - 1]
            if num - prev > 1:
                result.append(ELLIPSIS)
        result.append(num)

    return result


def _filtered_audit_logs(request):
    logs = SettingsAuditLog.objects.all().order_by('-created_at')
    action_type = request.GET.get('action', '').strip()
    setting_type = request.GET.get('setting_type', '').strip()
    performed_by = request.GET.get('performed_by', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search = request.GET.get('search', '').strip()

    if action_type:
        logs = logs.filter(action_type=action_type)
    if setting_type:
        logs = logs.filter(setting_type=setting_type)
    if performed_by:
        logs = logs.filter(performed_by_name__icontains=performed_by)

    current_tz = timezone.get_current_timezone()
    parsed_from = _parse_date(date_from)
    parsed_to = _parse_date(date_to)
    date_error = None

    if date_from and not parsed_from:
        date_error = 'Please enter a valid Date From value.'
    elif date_to and not parsed_to:
        date_error = 'Please enter a valid Date To value.'
    elif parsed_from and parsed_to and parsed_to < parsed_from:
        date_error = 'Date To cannot be earlier than Date From.'

    if date_error:
        return logs.none(), date_error

    if parsed_from:
        start = timezone.make_aware(datetime.combine(parsed_from, time.min), current_tz)
        logs = logs.filter(created_at__gte=start)

    if parsed_to:
        next_day = parsed_to + timedelta(days=1)
        end = timezone.make_aware(datetime.combine(next_day, time.min), current_tz)
        logs = logs.filter(created_at__lt=end)

    if search:
        logs = logs.filter(
            Q(setting_name__icontains=search) |
            Q(change_summary__icontains=search) |
            Q(performed_by_name__icontains=search)
        )

    return logs, None


@login_required
@user_passes_test(is_admin, login_url='login')
def settings_audit_log(request):
    logs, date_error = _filtered_audit_logs(request)

    per_page = _parse_per_page(request.GET.get('per_page'))
    page_obj = Paginator(logs, per_page).get_page(request.GET.get('page'))

    page_window = _build_page_window(
        current=page_obj.number,
        total=page_obj.paginator.num_pages,
    )

    context = {
        'page_obj': page_obj,
        'page_window': page_window,
        'admins': SettingsAuditLog.objects.values_list('performed_by_name', flat=True).distinct(),
        'action_types': SettingsAuditLog.ACTION_TYPES,
        'setting_types': SettingsAuditLog.SETTING_TYPES,
        'selected_action': request.GET.get('action', '').strip(),
        'selected_setting_type': request.GET.get('setting_type', '').strip(),
        'selected_performed_by': request.GET.get('performed_by', '').strip(),
        'date_from': request.GET.get('date_from', '').strip(),
        'date_to': request.GET.get('date_to', '').strip(),
        'date_error': date_error,
        'search_query': request.GET.get('search', '').strip(),
        'per_page': per_page,
        'allowed_per_page': ALLOWED_PER_PAGE,
    }
    return render(request, 'admin_panel/audit_log.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def download_audit_log_excel(request):
    logs, date_error = _filtered_audit_logs(request)
    generated_at = timezone.localtime(timezone.now())

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = (
        f'attachment; filename=Audit_Log_{generated_at.strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Audit Log'
    headers = [
        'ID', 'Action', 'Setting Type', 'Setting Name', 'Old Value', 'New Value',
        'Change Summary', 'Performed By', 'IP Address', 'Remarks', 'Created At',
    ]
    worksheet.append(headers)
    for cell in worksheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')

    current_tz = timezone.get_current_timezone()
    for log in logs:
        created_at = log.created_at
        if created_at and timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.utc)
        created_at = created_at.astimezone(current_tz) if created_at else None
        worksheet.append([
            log.id,
            log.get_action_type_display(),
            log.get_setting_type_display(),
            log.setting_name,
            log.old_value or '',
            log.new_value or '',
            log.change_summary or '',
            log.get_performed_by_display(),
            log.ip_address or 'N/A',
            log.remarks or '',
            created_at.strftime('%d-%b-%Y %I:%M:%S %p') if created_at else '',
        ])

    workbook.save(response)
    return response