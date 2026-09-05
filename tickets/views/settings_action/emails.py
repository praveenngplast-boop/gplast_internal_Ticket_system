# tickets/views/settings_actions/emails.py

"""
Email Settings - Manage Notification Emails
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from tickets.models import AdminNotificationEmail
from tickets.forms import AdminNotificationEmailForm
from .settings_audit import log_settings_change
from ..utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='login')
def settings_emails(request):
    """
    Manage Notification Emails: Add, Delete
    POST: action (add/delete), email, email_id
    Redirects to: settings_communication
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            form = AdminNotificationEmailForm(request.POST)
            if form.is_valid(): 
                email = form.save()
                messages.success(request, f"Email '{email.email}' added.")
                
                log_settings_change(
                    request,
                    action_type='CREATE',
                    setting_type='EMAIL',
                    setting_name=f"Email: {email.email}",
                    new_value=email.email,
                    change_summary=f"Added notification email: {email.email}",
                    remarks=f"Email added by {request.user.username}"
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif action == 'delete':
            email_obj = get_object_or_404(AdminNotificationEmail, pk=request.POST.get('email_id'))
            email_str = email_obj.email
            email_obj.delete()
            messages.success(request, f"Email '{email_str}' deleted.")
            
            log_settings_change(
                request,
                action_type='DELETE',
                setting_type='EMAIL',
                setting_name=f"Email: {email_str}",
                old_value=email_str,
                change_summary=f"Deleted notification email: {email_str}",
                remarks=f"Email deleted by {request.user.username}"
            )
    
    return redirect('settings_communication')
