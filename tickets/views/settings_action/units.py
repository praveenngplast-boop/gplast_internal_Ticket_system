# tickets/views/settings_actions/units.py

"""
Unit and Department Settings - Add, Edit, Toggle Active/Inactive
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from tickets.models import Unit, Department
from tickets.forms import UnitForm, DepartmentForm
from .settings_audit import log_settings_change
from ..utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def settings_units(request):
    """
    Manage Units: Add, Edit, Toggle Active/Inactive
    POST: action (add/edit/toggle), unit_id, code, full_name
    Redirects to: settings_units_departments
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            form = UnitForm(request.POST)
            if form.is_valid(): 
                unit = form.save(commit=False)
                unit.created_by = request.user.username
                unit.save()
                messages.success(request, f"Unit '{unit.code}' added.")
                
                log_settings_change(
                    request,
                    action_type='CREATE',
                    setting_type='UNIT',
                    setting_name=f"Unit: {unit.code}",
                    new_value=f"Code: {unit.code}, Name: {unit.full_name}",
                    change_summary=f"Added unit '{unit.code}' - {unit.full_name}",
                    remarks=f"Unit added by {request.user.username}"
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif action == 'edit':
            unit = get_object_or_404(Unit, pk=request.POST.get('unit_id'))
            old_code = unit.code
            old_name = unit.full_name
            
            form = UnitForm(request.POST, instance=unit)
            if form.is_valid(): 
                form.save()
                messages.success(request, f"Unit '{unit.code}' updated.")
                
                change_details = []
                if old_code != unit.code:
                    change_details.append(f"Code: {old_code} → {unit.code}")
                if old_name != unit.full_name:
                    change_details.append(f"Name: {old_name} → {unit.full_name}")
                
                log_settings_change(
                    request,
                    action_type='UPDATE',
                    setting_type='UNIT',
                    setting_name=f"Unit: {unit.code}",
                    old_value=f"Code: {old_code}, Name: {old_name}",
                    new_value=f"Code: {unit.code}, Name: {unit.full_name}",
                    change_summary='; '.join(change_details) if change_details else 'Unit updated',
                    remarks=f"Unit updated by {request.user.username}"
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif action == 'toggle':
            unit = get_object_or_404(Unit, pk=request.POST.get('unit_id'))
            old_status = 'Active' if unit.is_active else 'Inactive'
            unit.is_active = not unit.is_active
            unit.save()
            new_status = 'Active' if unit.is_active else 'Inactive'
            
            messages.success(request, f"Unit '{unit.code}' {'activated' if unit.is_active else 'deactivated'}.")
            
            log_settings_change(
                request,
                action_type='TOGGLE',
                setting_type='UNIT',
                setting_name=f"Unit: {unit.code}",
                old_value=f"Status: {old_status}",
                new_value=f"Status: {new_status}",
                change_summary=f"Status changed from {old_status} to {new_status}",
                remarks=f"Unit toggled by {request.user.username}"
            )
    
    return redirect('settings_units_departments')


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def settings_departments(request):
    """
    Manage Departments: Add, Edit, Toggle Active/Inactive
    POST: action (add/edit/toggle), dept_id, name, unit
    Redirects to: settings_units_departments
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            form = DepartmentForm(request.POST)
            if form.is_valid(): 
                dept = form.save()
                messages.success(request, f"Department '{dept.name}' added.")
                
                log_settings_change(
                    request,
                    action_type='CREATE',
                    setting_type='DEPARTMENT',
                    setting_name=f"Department: {dept.name}",
                    new_value=f"Name: {dept.name}, Unit: {dept.unit.code}",
                    change_summary=f"Added department '{dept.name}' under unit '{dept.unit.code}'",
                    remarks=f"Department added by {request.user.username}"
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif action == 'edit':
            dept = get_object_or_404(Department, pk=request.POST.get('dept_id'))
            old_name = dept.name
            old_unit = dept.unit.code
            
            form = DepartmentForm(request.POST, instance=dept)
            if form.is_valid(): 
                form.save()
                messages.success(request, f"Department '{dept.name}' updated.")
                
                change_details = []
                if old_name != dept.name:
                    change_details.append(f"Name: {old_name} → {dept.name}")
                if old_unit != dept.unit.code:
                    change_details.append(f"Unit: {old_unit} → {dept.unit.code}")
                
                log_settings_change(
                    request,
                    action_type='UPDATE',
                    setting_type='DEPARTMENT',
                    setting_name=f"Department: {dept.name}",
                    old_value=f"Name: {old_name}, Unit: {old_unit}",
                    new_value=f"Name: {dept.name}, Unit: {dept.unit.code}",
                    change_summary='; '.join(change_details) if change_details else 'Department updated',
                    remarks=f"Department updated by {request.user.username}"
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif action == 'toggle':
            dept = get_object_or_404(Department, pk=request.POST.get('dept_id'))
            old_status = 'Active' if dept.is_active else 'Inactive'
            dept.is_active = not dept.is_active
            dept.save()
            new_status = 'Active' if dept.is_active else 'Inactive'
            
            messages.success(request, f"Department '{dept.name}' {'activated' if dept.is_active else 'deactivated'}.")
            
            log_settings_change(
                request,
                action_type='TOGGLE',
                setting_type='DEPARTMENT',
                setting_name=f"Department: {dept.name}",
                old_value=f"Status: {old_status}",
                new_value=f"Status: {new_status}",
                change_summary=f"Status changed from {old_status} to {new_status}",
                remarks=f"Department toggled by {request.user.username}"
            )
    
    return redirect('settings_units_departments')