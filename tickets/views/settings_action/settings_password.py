# tickets/views/settings_actions/settings_password.py

"""
Password Settings - Change Admin Password and Reset Employee Password
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages

from tickets.forms import AdminPasswordChangeForm, AdminSetUserPasswordForm
from .settings_audit import log_settings_change
from ..utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='tickets:login')
def settings_passwords(request):
    """
    Change Admin Password and Reset Employee Password
    POST: action (change_my_password / set_user_password)
    Redirects to: settings_credentials_page
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_my_password':
            form = AdminPasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid(): 
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated!')
                
                log_settings_change(
                    request,
                    action_type='UPDATE',
                    setting_type='PASSWORD',
                    setting_name=f"Admin: {request.user.username}",
                    change_summary="Admin password changed",
                    remarks=f"Admin password changed by {request.user.username}"
                )
            else:
                for e in form.errors.values():
                    for err in e: 
                        messages.error(request, f"Error: {err}")
        
        elif action == 'set_user_password':
            user_id = request.POST.get('user')
            if not user_id:
                messages.error(request, "Please select an employee.")
                return redirect('settings_credentials_page')
            
            selected_user = get_object_or_404(User, pk=user_id, is_staff=False)
            form = AdminSetUserPasswordForm(user=selected_user, data=request.POST)
            if form.is_valid(): 
                form.save()
                messages.success(request, f"Password reset for '{selected_user.username}'.")
                
                log_settings_change(
                    request,
                    action_type='UPDATE',
                    setting_type='PASSWORD',
                    setting_name=f"Employee: {selected_user.username}",
                    change_summary=f"Password reset for {selected_user.username}",
                    remarks=f"Employee password reset by {request.user.username}"
                )
            else:
                for e in form.errors.values():
                    for err in e: 
                        messages.error(request, f"Error: {err}")
    
    return redirect('settings_credentials_page')