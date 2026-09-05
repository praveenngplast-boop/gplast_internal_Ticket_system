# tickets/views/settings_action/unit_heads.py

"""
Unit Head Management - Add, Edit, Toggle, Delete
Admin settings actions for managing Unit Heads
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
import logging

from tickets.models import UnitHead, Unit, SettingsAuditLog, EmployeeMaster
from tickets.forms import UnitHeadForm
from .settings_audit import log_settings_change
from ..utils import is_admin, get_client_ip

logger = logging.getLogger(__name__)


# ============================================================
# UNIT HEAD MANAGEMENT PAGE (GET)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def settings_unit_heads_page(request):
    """
    Display Unit Head management page with all unit heads
    URL: /custom-admin/settings/unit-heads/
    """
    unit_heads = UnitHead.objects.all().select_related('user', 'unit').order_by('unit__code')
    
    # Get units that don't have a unit head yet
    available_units = Unit.objects.filter(
        is_active=True
    ).exclude(
        id__in=UnitHead.objects.filter(is_active=True).values_list('unit_id', flat=True)
    ).order_by('code')
    
    # Get users who are not already unit heads
    existing_unit_head_user_ids = UnitHead.objects.values_list('user_id', flat=True)
    available_users = User.objects.filter(
        is_active=True,
        is_staff=False
    ).exclude(
        id__in=existing_unit_head_user_ids
    ).order_by('username')
    
    context = {
        'unit_heads': unit_heads,
        'available_units': available_units,
        'available_users': available_users,
        'total_unit_heads': unit_heads.count(),
        'all_units': Unit.objects.filter(is_active=True).order_by('code'),
    }
    return render(request, 'admin_panel/settings_unit_heads.html', context)


# ============================================================
# UNIT HEAD MANAGEMENT - POST ACTIONS
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def settings_unit_heads(request):
    """
    Handle Unit Head management POST actions:
    - Add Unit Head
    - Edit Unit Head
    - Toggle Unit Head Active/Inactive
    - Delete Unit Head
    URL: /custom-admin/settings/unit-heads/handler/
    """
    if request.method != 'POST':
        return redirect('settings_unit_heads_page')
    
    action = request.POST.get('action')
    
    # ============================================================
    # ADD UNIT HEAD - âœ… Auto-create Employee
    # ============================================================
    if action == 'add_unit_head':
        form = UnitHeadForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    unit_head = form.save()
                    
                    # âœ… CREATE EMPLOYEE MASTER RECORD
                    employee_id = unit_head.user.username.upper()
                    
                    # Check if employee already exists with this ID
                    existing_employee = EmployeeMaster.objects.filter(employee_id=employee_id).first()
                    
                    if existing_employee:
                        # Update existing employee
                        existing_employee.employee_name = unit_head.name
                        existing_employee.email = unit_head.email
                        existing_employee.unit = unit_head.unit
                        existing_employee.is_active = unit_head.is_active
                        existing_employee.can_assign_ticket = True
                        existing_employee.save()
                        employee_created = False
                    else:
                        # Create new employee
                        employee = EmployeeMaster.objects.create(
                            employee_id=employee_id,
                            employee_name=unit_head.name,
                            email=unit_head.email,
                            unit=unit_head.unit,
                            department=None,  # No department assigned
                            mobile=None,  # No mobile initially
                            is_active=unit_head.is_active,
                            can_assign_ticket=True,
                        )
                        employee_created = True
                    
                    messages.success(
                        request, 
                        f'âœ… Unit Head "{unit_head.name}" added successfully! '
                        f'User "{unit_head.user.username}" created with password. '
                        f'{"Employee" if employee_created else "Employee"} record updated.'
                    )
                    
                    log_settings_change(
                        request,
                        action_type='CREATE',
                        setting_type='EMPLOYEE',
                        setting_name=f"Unit Head: {unit_head.name} - {unit_head.unit.code}",
                        new_value=f"Name: {unit_head.name}, Unit: {unit_head.unit.code}, Email: {unit_head.email}, Username: {unit_head.user.username}",
                        change_summary=f"Added Unit Head {unit_head.name} for {unit_head.unit.code}",
                        remarks=f"Unit Head added by {request.user.username}"
                    )
                    
            except IntegrityError as e:
                logger.error(f"IntegrityError while adding Unit Head: {str(e)}")
                messages.error(request, f'âŒ Database error: {str(e)}')
            except Exception as e:
                logger.error(f"Error adding Unit Head: {str(e)}")
                messages.error(request, f'âŒ Error adding Unit Head: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'âŒ {error}')
                    else:
                        messages.error(request, f'âŒ {field.replace("_", " ").title()}: {error}')
        
        return redirect('settings_unit_heads_page')
    
    # ============================================================
    # EDIT UNIT HEAD - âœ… Update Employee
    # ============================================================
    elif action == 'edit_unit_head':
        unit_head_id = request.POST.get('unit_head_id')
        unit_head = get_object_or_404(UnitHead, id=unit_head_id)
        
        # Store old values for audit log
        old_name = unit_head.name
        old_email = unit_head.email
        old_unit = unit_head.unit
        old_is_active = unit_head.is_active
        old_username = unit_head.user.username if unit_head.user else None
        
        form = UnitHeadForm(request.POST, instance=unit_head, is_edit=True)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    unit_head = form.save()
                    
                    # âœ… UPDATE EMPLOYEE MASTER RECORD
                    employee_id = unit_head.user.username.upper()
                    employee = EmployeeMaster.objects.filter(employee_id=employee_id).first()
                    
                    if employee:
                        employee.employee_name = unit_head.name
                        employee.email = unit_head.email
                        employee.unit = unit_head.unit
                        employee.is_active = unit_head.is_active
                        employee.can_assign_ticket = True
                        employee.save()
                    else:
                        # Create employee if doesn't exist (shouldn't happen)
                        EmployeeMaster.objects.create(
                            employee_id=employee_id,
                            employee_name=unit_head.name,
                            email=unit_head.email,
                            unit=unit_head.unit,
                            department=None,
                            mobile=None,
                            is_active=unit_head.is_active,
                            can_assign_ticket=True,
                        )
                    
                    # Track changes for audit
                    changes = []
                    if old_name != unit_head.name:
                        changes.append(f"Name: {old_name} â†’ {unit_head.name}")
                    if old_email != unit_head.email:
                        changes.append(f"Email: {old_email} â†’ {unit_head.email}")
                    if old_unit != unit_head.unit:
                        changes.append(f"Unit: {old_unit.code if old_unit else 'None'} â†’ {unit_head.unit.code if unit_head.unit else 'None'}")
                    if old_is_active != unit_head.is_active:
                        changes.append(f"Status: {'Active' if old_is_active else 'Inactive'} â†’ {'Active' if unit_head.is_active else 'Inactive'}")
                    if old_username != unit_head.user.username:
                        changes.append(f"Username: {old_username} â†’ {unit_head.user.username}")
                    
                    messages.success(
                        request, 
                        f'âœ… Unit Head "{unit_head.name}" updated successfully! Employee record also updated.'
                    )
                    
                    log_settings_change(
                        request,
                        action_type='UPDATE',
                        setting_type='EMPLOYEE',
                        setting_name=f"Unit Head: {unit_head.name} - {unit_head.unit.code}",
                        old_value=f"Name: {old_name}, Unit: {old_unit.code if old_unit else 'None'}, Email: {old_email}",
                        new_value=f"Name: {unit_head.name}, Unit: {unit_head.unit.code if unit_head.unit else 'None'}, Email: {unit_head.email}",
                        change_summary='; '.join(changes) if changes else 'Unit Head updated',
                        remarks=f"Unit Head updated by {request.user.username}"
                    )
                    
            except IntegrityError as e:
                logger.error(f"IntegrityError while editing Unit Head: {str(e)}")
                messages.error(request, f'âŒ Database error: {str(e)}')
            except Exception as e:
                logger.error(f"Error editing Unit Head: {str(e)}")
                messages.error(request, f'âŒ Error editing Unit Head: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'âŒ {error}')
                    else:
                        messages.error(request, f'âŒ {field.replace("_", " ").title()}: {error}')
        
        return redirect('settings_unit_heads_page')
    
    # ============================================================
    # TOGGLE UNIT HEAD ACTIVE/INACTIVE - âœ… Toggle Employee
    # ============================================================
    elif action == 'toggle_unit_head':
        unit_head_id = request.POST.get('unit_head_id')
        unit_head = get_object_or_404(UnitHead, id=unit_head_id)
        
        old_status = 'Active' if unit_head.is_active else 'Inactive'
        
        with transaction.atomic():
            unit_head.is_active = not unit_head.is_active
            unit_head.save()
            
            # Also toggle the user's active status
            if unit_head.user:
                unit_head.user.is_active = unit_head.is_active
                unit_head.user.save()
            
            # âœ… TOGGLE EMPLOYEE MASTER RECORD
            employee_id = unit_head.user.username.upper()
            employee = EmployeeMaster.objects.filter(employee_id=employee_id).first()
            if employee:
                employee.is_active = unit_head.is_active
                employee.save()
            
            new_status = 'Active' if unit_head.is_active else 'Inactive'
        
        messages.success(
            request, 
            f'âœ… Unit Head "{unit_head.name}" {"activated" if unit_head.is_active else "deactivated"}. '
            f'Employee record also {"activated" if unit_head.is_active else "deactivated"}.'
        )
        
        log_settings_change(
            request,
            action_type='TOGGLE',
            setting_type='EMPLOYEE',
            setting_name=f"Unit Head: {unit_head.name} - {unit_head.unit.code}",
            old_value=f"Status: {old_status}",
            new_value=f"Status: {new_status}",
            change_summary=f"Status changed from {old_status} to {new_status}",
            remarks=f"Unit Head toggled by {request.user.username}"
        )
        
        return redirect('settings_unit_heads_page')
    
    # ============================================================
    # DELETE UNIT HEAD - âœ… Delete Employee
    # ============================================================
    elif action == 'delete_unit_head':
        unit_head_id = request.POST.get('unit_head_id')
        unit_head = get_object_or_404(UnitHead, id=unit_head_id)
        
        # Store info for audit before deletion
        name = unit_head.name
        unit_code = unit_head.unit.code if unit_head.unit else 'None'
        email = unit_head.email
        username = unit_head.user.username if unit_head.user else 'None'
        employee_id = username.upper() if username else None
        
        # Check if unit head is active
        if unit_head.is_active:
            messages.error(
                request, 
                f'âŒ Cannot delete "{name}" because they are still ACTIVE. '
                f'Please deactivate the Unit Head first, then try deleting again.'
            )
            return redirect('settings_unit_heads_page')
        
        try:
            with transaction.atomic():
                # Store user reference before deleting unit head
                user = unit_head.user
                
                # âœ… DELETE EMPLOYEE MASTER RECORD
                if employee_id:
                    employee = EmployeeMaster.objects.filter(employee_id=employee_id).first()
                    if employee:
                        # Delete the employee record
                        employee.delete()
                
                # Delete the unit head
                unit_head.delete()
                
                # Optionally delete the user account (or keep it)
                # For safety, we'll keep the user but remove the unit head association
                # If you want to delete the user as well, uncomment the line below:
                # user.delete()
                
                messages.success(
                    request, 
                    f'âœ… Unit Head "{name}" has been permanently deleted. Employee record also deleted.'
                )
                
                log_settings_change(
                    request,
                    action_type='DELETE',
                    setting_type='EMPLOYEE',
                    setting_name=f"Unit Head: {name} - {unit_code}",
                    old_value=f"Name: {name}, Unit: {unit_code}, Email: {email}, Username: {username}, Status: Inactive",
                    change_summary=f"Permanently deleted Unit Head {name} and associated employee",
                    remarks=f"Unit Head permanently deleted by {request.user.username}"
                )
                
        except Exception as e:
            logger.error(f"Error deleting Unit Head: {str(e)}")
            messages.error(request, f'âŒ Error deleting Unit Head: {str(e)}')
        
        return redirect('settings_unit_heads_page')
    
    # ============================================================
    # AJAX: GET UNIT HEAD DETAILS
    # ============================================================
    elif action == 'get_unit_head_details':
        unit_head_id = request.POST.get('unit_head_id')
        unit_head = get_object_or_404(UnitHead, id=unit_head_id)
        
        data = {
            'id': unit_head.id,
            'name': unit_head.name,
            'email': unit_head.email,
            'unit_id': unit_head.unit_id,
            'unit_code': unit_head.unit.code if unit_head.unit else '',
            'username': unit_head.user.username if unit_head.user else '',
            'user_id': unit_head.user.id if unit_head.user else None,
            'is_active': unit_head.is_active,
            'created_at': unit_head.created_at.strftime('%Y-%m-%d %H:%M:%S') if unit_head.created_at else '',
            'created_by': unit_head.created_by or '',
        }
        return JsonResponse({'success': True, 'data': data})
    
    # ============================================================
    # AJAX: CHECK USERNAME AVAILABILITY
    # ============================================================
    elif action == 'check_username':
        username = request.POST.get('username', '').strip().lower()
        exclude_id = request.POST.get('exclude_id')
        
        if not username:
            return JsonResponse({'success': False, 'available': False, 'message': 'Username is required'})
        
        existing_user = User.objects.filter(username=username)
        if exclude_id:
            existing_user = existing_user.exclude(id=exclude_id)
        
        available = not existing_user.exists()
        
        return JsonResponse({
            'success': True,
            'available': available,
            'message': 'Username is available' if available else 'Username is already taken'
        })
    
    # ============================================================
    # AJAX: CHECK EMAIL AVAILABILITY
    # ============================================================
    elif action == 'check_email':
        email = request.POST.get('email', '').strip().lower()
        exclude_id = request.POST.get('exclude_id')
        
        if not email:
            return JsonResponse({'success': False, 'available': False, 'message': 'Email is required'})
        
        existing = UnitHead.objects.filter(email=email)
        if exclude_id:
            existing = existing.exclude(id=exclude_id)
        
        available = not existing.exists()
        
        return JsonResponse({
            'success': True,
            'available': available,
            'message': 'Email is available' if available else 'Email is already in use'
        })
    
    # ============================================================
    # INVALID ACTION
    # ============================================================
    else:
        messages.error(request, f'âŒ Invalid action: {action}')
        return redirect('settings_unit_heads_page')
