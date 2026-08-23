# tickets/views/settings_actions/credentials.py

"""
Credentials Management - Add, Edit, Toggle, Delete, Download
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

from tickets.models import DepartmentCredential, Unit, Department
from .settings_audit import log_settings_change
from ..utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def settings_credentials(request):
    """
    Manage Department Credentials:
    - Add Credential
    - Edit Credential
    - Toggle Active/Inactive
    - Delete Credential
    POST: action (add_credential, edit_credential, toggle_credential, delete_credential)
    Redirects to: settings_credentials_page
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # ========== ADD CREDENTIAL ==========
        if action == 'add_credential':
            uid = request.POST.get('unit')
            did = request.POST.get('department')
            uname = request.POST.get('username', '').strip()
            pwd = request.POST.get('password', '').strip()
            
            if not all([uid, did, uname, pwd]):
                messages.error(request, "All fields are required.")
                return redirect('settings_credentials_page')
            
            if DepartmentCredential.objects.filter(unit_id=uid, department_id=did).exists():
                messages.error(request, "Credential already exists for this department.")
                return redirect('settings_credentials_page')
            
            try:
                cred = DepartmentCredential.objects.create(
                    unit_id=uid,
                    department_id=did,
                    username=uname,
                    password=pwd
                )
                if not User.objects.filter(username=uname).exists():
                    User.objects.create_user(username=uname, password=pwd, is_staff=False)
                u = Unit.objects.get(pk=uid)
                d = Department.objects.get(pk=did)
                messages.success(request, f'Credential for {u.code}-{d.name} added successfully!')
                
                log_settings_change(
                    request,
                    action_type='CREATE',
                    setting_type='CREDENTIAL',
                    setting_name=f"Credential: {u.code} - {d.name}",
                    new_value=f"Username: {uname}, Unit: {u.code}, Department: {d.name}",
                    change_summary=f"Added credential for {u.code} - {d.name}",
                    remarks=f"Credential added by {request.user.username}"
                )
            except Exception as ex:
                messages.error(request, f'Error: {ex}')
        
        # ========== EDIT CREDENTIAL ==========
        elif action == 'edit_credential':
            cred = get_object_or_404(DepartmentCredential, pk=request.POST.get('cred_id'))
            ou = cred.username
            nu = request.POST.get('username', '').strip()
            np = request.POST.get('password', '').strip()
            
            old_username = cred.username
            old_password = cred.password
            
            cred.username = nu
            if np:
                cred.password = np
            try:
                cred.save()
                user = User.objects.filter(username=ou).first()
                if user:
                    if ou != nu:
                        user.username = nu
                    if np:
                        user.set_password(np)
                    user.save()
                elif not User.objects.filter(username=nu).exists():
                    User.objects.create_user(username=nu, password=np or cred.password, is_staff=False)
                messages.success(request, 'Credential updated successfully!')
                
                change_details = []
                if old_username != nu:
                    change_details.append(f"Username: {old_username} → {nu}")
                if np:
                    change_details.append("Password changed")
                
                log_settings_change(
                    request,
                    action_type='UPDATE',
                    setting_type='CREDENTIAL',
                    setting_name=f"Credential: {cred.unit.code} - {cred.department.name}",
                    old_value=f"Username: {old_username}",
                    new_value=f"Username: {nu}",
                    change_summary='; '.join(change_details) if change_details else 'Credential updated',
                    remarks=f"Credential updated by {request.user.username}"
                )
            except Exception as ex:
                messages.error(request, f'Error: {ex}')
        
        # ========== TOGGLE CREDENTIAL ==========
        elif action == 'toggle_credential':
            cred = get_object_or_404(DepartmentCredential, pk=request.POST.get('cred_id'))
            old_status = 'Active' if cred.is_active else 'Inactive'
            cred.is_active = not cred.is_active
            cred.save()
            new_status = 'Active' if cred.is_active else 'Inactive'
            
            user = User.objects.filter(username=cred.username).first()
            if user:
                user.is_active = cred.is_active
                user.save()
            messages.success(request, f'Credential {"activated" if cred.is_active else "deactivated"}.')
            
            log_settings_change(
                request,
                action_type='TOGGLE',
                setting_type='CREDENTIAL',
                setting_name=f"Credential: {cred.unit.code} - {cred.department.name}",
                old_value=f"Status: {old_status}",
                new_value=f"Status: {new_status}",
                change_summary=f"Status changed from {old_status} to {new_status}",
                remarks=f"Credential toggled by {request.user.username}"
            )
        
        # ========== DELETE CREDENTIAL ==========
        elif action == 'delete_credential':
            cred = get_object_or_404(DepartmentCredential, pk=request.POST.get('cred_id'))
            info = f'{cred.unit.code}-{cred.department.name}'
            uname = cred.username
            
            user = User.objects.filter(username=uname).first()
            if user:
                user.is_active = False
                user.save()
            cred.delete()
            messages.success(request, f'Credential for {info} deleted.')
            
            log_settings_change(
                request,
                action_type='DELETE',
                setting_type='CREDENTIAL',
                setting_name=f"Credential: {info}",
                old_value=f"Username: {uname}",
                change_summary=f"Deleted credential for {info}",
                remarks=f"Credential deleted by {request.user.username}"
            )
    
    return redirect('settings_credentials_page')


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def download_credentials(request):
    """
    Download all department credentials as Excel
    Includes: Unit Code, Unit Name, Department, Username, Password, Status
    """
    creds = DepartmentCredential.objects.all().select_related('unit', 'department').order_by('unit__code', 'department__name')
    resp = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename=Credentials_{timezone.now().strftime("%Y%m%d")}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Credentials"
    
    tf = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    hf = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    df = Font(name='Calibri', size=11)
    tfill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    hfill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    
    ws.merge_cells('A1:F1')
    ws['A1'] = "Department Credentials"
    ws['A1'].font = tf
    ws['A1'].fill = tfill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 35
    
    for ci, h in enumerate(['Unit Code', 'Unit Name', 'Department', 'Username', 'Password', 'Status'], 1):
        c = ws.cell(row=3, column=ci)
        c.value = h
        c.font = hf
        c.fill = hfill
        c.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[3].height = 25
    
    for ri, cred in enumerate(creds, 4):
        rd = [
            cred.unit.code,
            cred.unit.full_name,
            cred.department.name,
            cred.username,
            cred.password,
            'Active' if cred.is_active else 'Inactive'
        ]
        for ci, v in enumerate(rd, 1):
            c = ws.cell(row=ri, column=ci)
            c.value = v
            c.font = df
    
    for col in ws.columns:
        ws.column_dimensions[openpyxl.utils.get_column_letter(col[0].column)].width = max(
            max(len(str(c.value or '')) for c in col if c.row > 1) + 3, 12
        )
    wb.save(resp)
    return resp