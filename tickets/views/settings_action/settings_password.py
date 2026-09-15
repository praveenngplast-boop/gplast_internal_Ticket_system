# tickets/views/settings_action/settings_password.py

"""
Password Settings - Change Admin Password and Reset Employee Password
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages

from tickets.forms import AdminPasswordChangeForm, AdminSetUserPasswordForm
from tickets.views.utils import sync_department_credential_password
from .settings_audit import log_settings_change
from ..utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='login')
def settings_passwords(request):
    """
    Change Admin Password and Reset Employee Password
    POST: action (change_my_password / set_user_password)
    Redirects to: settings_credentials_page
    """
    if request.method == 'POST':
        action = request.POST.get('action')

        # ============================================================
        # CHANGE ADMIN PASSWORD
        # ============================================================
        if action == 'change_my_password':

            # ---------- Read + validate manually ----------
            old_pw = request.POST.get('old_password', '').strip()

            # Fallback for older templates still sending current_password
            if not old_pw:
                old_pw = request.POST.get('current_password', '').strip()

            new_pw1 = request.POST.get('new_password1', '').strip()
            new_pw2 = request.POST.get('new_password2', '').strip()

            errors = []

            if not old_pw:
                errors.append("Current password is required.")
            elif not request.user.check_password(old_pw):
                errors.append("Current password is incorrect.")

            if not new_pw1:
                errors.append("New password is required.")
            elif len(new_pw1) < 4:
                errors.append("Password must be at least 4 characters.")
            elif len(new_pw1) > 14:
                errors.append("Password must be at most 14 characters.")

            if new_pw1 and new_pw2 and new_pw1 != new_pw2:
                errors.append("New passwords do not match.")

            if new_pw1 and old_pw and new_pw1 == old_pw:
                errors.append("New password cannot be the same as the current one.")

            # ---------- Apply or report ----------
            if errors:
                for e in errors:
                    messages.error(request, e)
            else:
                try:
                    # 1. Update the login password
                    request.user.set_password(new_pw1)
                    request.user.save()
                    update_session_auth_hash(request, request.user)

                    # 2. ✅ Sync the plain password into DepartmentCredential
                    updated = sync_department_credential_password(
                        request.user, new_pw1
                    )
                    if updated:
                        messages.info(
                            request,
                            "Your department credential has also been updated."
                        )

                    messages.success(request, "Password updated successfully!")

                    # 3. Audit log (best effort)
                    try:
                        log_settings_change(
                            request,
                            action_type='UPDATE',
                            setting_type='PASSWORD',
                            setting_name=f"Admin: {request.user.username}",
                            change_summary="Admin password changed",
                            remarks=f"Admin password changed by {request.user.username}"
                        )
                    except Exception as log_err:
                        print("⚠️  Audit log failed:", log_err)

                except Exception as ex:
                    messages.error(request, f"Could not update password: {ex}")

            return redirect('settings_credentials_page')

        # ============================================================
        # RESET ANOTHER USER'S PASSWORD
        # ============================================================
        elif action == 'set_user_password':
            user_id = request.POST.get('user')
            if not user_id:
                messages.error(request, "Please select an employee.")
                return redirect('settings_credentials_page')

            selected_user = get_object_or_404(User, pk=user_id, is_staff=False)
            form = AdminSetUserPasswordForm(user=selected_user, data=request.POST)

            if form.is_valid():
                # Extract the plain new password BEFORE saving
                new_plain = form.cleaned_data.get('new_password1', '')

                form.save()
                messages.success(
                    request,
                    f"Password reset for '{selected_user.username}'."
                )

                # ✅ Sync the new plain password into DepartmentCredential
                if new_plain:
                    try:
                        updated = sync_department_credential_password(
                            selected_user, new_plain
                        )
                        if updated:
                            messages.info(
                                request,
                                f"Department credential for "
                                f"'{selected_user.username}' has also been updated."
                            )
                    except Exception as sync_err:
                        print("⚠️  Credential sync failed:", sync_err)

                # Audit log
                try:
                    log_settings_change(
                        request,
                        action_type='UPDATE',
                        setting_type='PASSWORD',
                        setting_name=f"Employee: {selected_user.username}",
                        change_summary=f"Password reset for {selected_user.username}",
                        remarks=f"Employee password reset by {request.user.username}"
                    )
                except Exception as log_err:
                    print("⚠️  Audit log failed:", log_err)
            else:
                for field, errs in form.errors.items():
                    for err in errs:
                        messages.error(request, f"{field}: {err}")

            return redirect('settings_credentials_page')

        # ============================================================
        # UNKNOWN ACTION
        # ============================================================
        else:
            messages.warning(request, f"Unknown action: {action}")

    return redirect('settings_credentials_page')
