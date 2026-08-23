# tickets/views/settings_actions/screen_mapping.py

"""
Screen Mapping - Add, Remove, Delete ERP, Export Excel, Page View, AJAX
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
import json
import logging

from tickets.models import ScreenMaster, ScreenMapping, ERPHolderMapping
from .settings_audit import log_settings_change
from ..utils import is_admin

logger = logging.getLogger(__name__)


# ============================================================
# SCREEN MAPPING - ADD (AJAX)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def screen_mapping_add(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=400)

    screen_id = request.POST.get('screen_id', '').strip()
    erp_user_id = request.POST.get('erp_user_id', '').strip()

    if not screen_id:
        return JsonResponse({'success': False, 'message': 'Screen is required'})
    if not erp_user_id:
        return JsonResponse({'success': False, 'message': 'ERP User ID is required'})

    try:
        screen = ScreenMaster.objects.get(id=screen_id)
    except ScreenMaster.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Screen not found'})

    if ScreenMapping.objects.filter(screen=screen, erp_user_id=erp_user_id).exists():
        return JsonResponse({'success': False, 'message': f'Mapping already exists: {screen.screen_code} → ERP {erp_user_id}'})

    try:
        mapping = ScreenMapping.objects.create(
            screen=screen, erp_user_id=erp_user_id, created_by=request.user.username
        )
        log_settings_change(
            request, 'CREATE', 'SCREEN',
            f'{screen.screen_code} → ERP {erp_user_id}',
            new_value=f'Screen: {screen.screen_code}, ERP ID: {erp_user_id}',
            change_summary=f'Mapped screen {screen.screen_code} to ERP {erp_user_id}'
        )
        # Get employee info for response
        emp_mappings = ERPHolderMapping.objects.filter(erp_user_id=erp_user_id).select_related('employee')
        emp_names = ', '.join([m.employee.employee_name for m in emp_mappings]) or 'N/A'
        return JsonResponse({
            'success': True,
            'message': f'Screen mapped successfully',
            'mapping': {
                'id': mapping.id,
                'screen_id': screen.id,
                'screen_code': screen.screen_code,
                'screen_name': screen.screen_name,
                'erp_user_id': erp_user_id,
                'employee_names': emp_names,
            }
        })
    except Exception as e:
        logger.error(f'Error adding screen mapping: {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============================================================
# SCREEN MAPPING - REMOVE (AJAX)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def screen_mapping_remove(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=400)

    mapping_id = request.POST.get('mapping_id', '').strip()
    if not mapping_id:
        return JsonResponse({'success': False, 'message': 'Mapping ID is required'})

    try:
        mapping = ScreenMapping.objects.select_related('screen').get(id=mapping_id)
    except ScreenMapping.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Mapping not found'})

    screen_code = mapping.screen.screen_code
    erp_user_id = mapping.erp_user_id
    mapping.delete()

    log_settings_change(
        request, 'DELETE', 'SCREEN',
        f'{screen_code} → ERP {erp_user_id}',
        old_value=f'Screen: {screen_code}, ERP ID: {erp_user_id}',
        change_summary=f'Removed screen mapping: {screen_code} from ERP {erp_user_id}'
    )
    return JsonResponse({'success': True, 'message': 'Mapping removed successfully'})


# ============================================================
# SCREEN MAPPING - DELETE ALL FOR ERP ID (AJAX)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def screen_mapping_delete_erp(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=400)

    erp_user_id = request.POST.get('erp_user_id', '').strip()
    if not erp_user_id:
        return JsonResponse({'success': False, 'message': 'ERP User ID is required'})

    mappings = ScreenMapping.objects.filter(erp_user_id=erp_user_id)
    count = mappings.count()

    if count == 0:
        return JsonResponse({'success': False, 'message': f'No mappings found for ERP ID "{erp_user_id}"'})

    mappings.delete()

    log_settings_change(
        request, 'DELETE', 'SCREEN',
        f'All mappings for ERP {erp_user_id}',
        old_value=f'Removed {count} mappings for ERP ID: {erp_user_id}',
        change_summary=f'Deleted all {count} screen mappings for ERP ID {erp_user_id}'
    )
    return JsonResponse({'success': True, 'message': f'Successfully deleted {count} mappings for ERP ID "{erp_user_id}"'})


# ============================================================
# SCREEN MAPPING - EXPORT EXCEL
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def screen_mapping_export_excel(request):
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from django.utils import timezone
    from django.http import HttpResponse

    erp_filter = request.GET.get('erp_user_id', '').strip()
    emp_filter = request.GET.get('employee_id', '').strip()

    mappings = ScreenMapping.objects.all().select_related('screen').order_by('erp_user_id', 'screen__screen_name')

    if erp_filter:
        mappings = mappings.filter(erp_user_id=erp_filter)
    if emp_filter:
        erp_ids = ERPHolderMapping.objects.filter(
            employee__employee_id__icontains=emp_filter
        ).values_list('erp_user_id', flat=True).distinct()
        mappings = mappings.filter(erp_user_id__in=erp_ids)

    current_tz = timezone.get_current_timezone()
    now_local = timezone.now().astimezone(current_tz)
    report_time = now_local.strftime('%d-%b-%Y %I:%M:%S %p')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Screen_Mapping_{now_local.strftime("%Y%m%d_%H%M%S")}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Screen Mapping'

    title_font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    data_font = Font(name='Calibri', size=10)
    title_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'), right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'), bottom=Side(style='thin', color='D0D0D0')
    )

    ws.merge_cells('A1:G1')
    ws['A1'] = f'SCREEN MAPPING REPORT - Generated: {report_time}  |  Total: {mappings.count()}'
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 40

    headers = ['#', 'ERP User ID', 'Employee ID(s)', 'Employee Name(s)', 'Screen Code', 'Screen Name', 'Mapped On']
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=ci)
        cell.value = h
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    ws.row_dimensions[3].height = 25

    # Build ERP→Employee lookup
    all_erp_ids = mappings.values_list('erp_user_id', flat=True).distinct()
    erp_emp_map = {}
    for erp_id in all_erp_ids:
        emps = ERPHolderMapping.objects.filter(erp_user_id=erp_id).select_related('employee')
        erp_emp_map[erp_id] = emps

    for ri, mapping in enumerate(mappings, 1):
        emps = erp_emp_map.get(mapping.erp_user_id, [])
        emp_ids = ', '.join([e.employee.employee_id for e in emps]) or 'Not Mapped'
        emp_names = ', '.join([e.employee.employee_name for e in emps]) or 'Not Mapped'
        mapped_on = mapping.created_at.astimezone(current_tz).strftime('%d-%b-%Y %I:%M %p') if mapping.created_at else ''
        row_data = [ri, mapping.erp_user_id, emp_ids, emp_names, mapping.screen.screen_code, mapping.screen.screen_name, mapped_on]
        for ci, val in enumerate(row_data, 1):
            cell = ws.cell(row=ri + 3, column=ci)
            cell.value = val
            cell.font = data_font
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = thin_border

    for col_letter, width in {'A': 8, 'B': 16, 'C': 22, 'D': 35, 'E': 18, 'F': 40, 'G': 22}.items():
        ws.column_dimensions[col_letter].width = width

    wb.save(response)
    return response


# ============================================================
# SCREEN MAPPING PAGE VIEW
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def settings_screen_mapping_page(request):
    """
    Screen Mapping Settings Page - Compact Table View with Modal
    Shows ERP IDs in a table with screen count, click to view screens in modal
    """
    erp_filter = request.GET.get('erp_user_id', '').strip()
    screen_search = request.GET.get('screen_search', '').strip()

    # Get all mappings with related screen data
    mappings = ScreenMapping.objects.all().select_related('screen').order_by('erp_user_id', 'screen__screen_name')

    # Apply filters
    if erp_filter:
        mappings = mappings.filter(erp_user_id=erp_filter)
    if screen_search:
        mappings = mappings.filter(
            Q(screen__screen_code__icontains=screen_search) |
            Q(screen__screen_name__icontains=screen_search)
        )

    # Get all ERP User IDs for dropdown - from ERPHolderMapping
    all_erp_user_ids = ERPHolderMapping.objects.values_list('erp_user_id', flat=True).distinct().order_by('erp_user_id')
    
    # Get all screens for dropdown
    screens = ScreenMaster.objects.filter(is_active=True).order_by('screen_name')

    # Group mappings by ERP User ID - COMPACT DATA
    erp_data = []
    erp_screens_map = {}  # Store screens for modal view
    
    for erp_id in all_erp_user_ids:
        erp_mappings = mappings.filter(erp_user_id=erp_id)
        screen_count = erp_mappings.count()
        
        # Get screens for this ERP (for modal)
        screen_list = []
        for mapping in erp_mappings:
            screen_list.append({
                'mapping_id': mapping.id,
                'screen_code': mapping.screen.screen_code,
                'screen_name': mapping.screen.screen_name,
                'screen_type': mapping.screen.screen_type,
            })
        
        erp_screens_map[erp_id] = screen_list
        
        erp_data.append({
            'erp_user_id': erp_id,
            'screen_count': screen_count,
            'screens': screen_list,
        })

    # Paginate the ERP data (15 per page)
    paginator = Paginator(erp_data, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Convert erp_screens_map to JSON for template
    erp_screens_json = json.dumps(erp_screens_map)

    context = {
        'page_obj': page_obj,
        'erp_data': page_obj,
        'erp_user_ids': all_erp_user_ids,
        'screens': screens,
        'erp_screens_map': erp_screens_map,
        'erp_screens_json': erp_screens_json,
        'erp_filter': erp_filter,
        'screen_search': screen_search,
        'total_erps': len(erp_data),
        'total_mappings': mappings.count(),
    }
    return render(request, 'admin_panel/settings_screen_mapping.html', context)


# ============================================================
# AJAX - GET SCREENS FOR ERP USER ID
# ============================================================
@login_required
def ajax_get_screens_for_erp(request):
    """Return screens mapped to a given ERP User ID (for ticket creation)"""
    erp_user_id = request.GET.get('erp_user_id', '').strip()
    if not erp_user_id:
        return JsonResponse({'success': False, 'screens': []})

    screens = ScreenMapping.objects.filter(
        erp_user_id=erp_user_id
    ).select_related('screen').order_by('screen__screen_name')

    screen_list = [{
        'id': sm.screen.id,
        'screen_code': sm.screen.screen_code,
        'screen_name': sm.screen.screen_name,
        'display': f'{sm.screen.screen_code} - {sm.screen.screen_name} ({sm.screen.get_screen_type_display()})'
    } for sm in screens]

    return JsonResponse({'success': True, 'screens': screen_list})