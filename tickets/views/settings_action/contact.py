# tickets/views/settings_actions/contact.py

"""
Contact Settings - Helpdesk Contact Information
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from tickets.models import AdminContact
from .settings_audit import log_settings_change
from ..utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='login')
def settings_contact(request):
    """
    Update Helpdesk Contact information
    POST: admin_name, admin_email
    Redirects to: settings_communication
    """
    if request.method == 'POST':
        contact_obj = AdminContact.objects.first()
        if not contact_obj:
            contact_obj = AdminContact.objects.create(
                admin_name="IT ADMIN",
                admin_phone="9999999999",
                admin_email="admin@gplast.com"
            )
        
        old_name = contact_obj.admin_name
        old_email = contact_obj.admin_email
        admin_name = request.POST.get('admin_name', '').strip()
        admin_email = request.POST.get('admin_email', '').strip()
        
        changed = False
        change_details = []
        
        if admin_name and admin_name != contact_obj.admin_name:
            contact_obj.admin_name = admin_name
            changed = True
            change_details.append(f"Name: {old_name} â†’ {admin_name}")
        
        if admin_email and admin_email != contact_obj.admin_email:
            contact_obj.admin_email = admin_email
            changed = True
            change_details.append(f"Email: {old_email} â†’ {admin_email}")
        
        if changed:
            contact_obj.save()
            messages.success(request, "IT Support Contact updated successfully.")
            
            log_settings_change(
                request,
                action_type='UPDATE',
                setting_type='CONTACT',
                setting_name='Helpdesk Contact',
                old_value=f"Name: {old_name}, Email: {old_email}",
                new_value=f"Name: {admin_name}, Email: {admin_email}",
                change_summary='; '.join(change_details),
                remarks="Contact information updated"
            )
        else:
            messages.info(request, "No changes made to contact information.")
    
    return redirect('settings_communication')
