# tickets/views/settings_action/settings_auditors.py
# ============================================================
# Auditor Credentials — settings sub-page + POST handler
#
# GET  /custom-admin/settings/auditor/
#       → settings_auditor_page   (renders the page)
#
# POST /custom-admin/settings/auditor/handler/
#       → settings_auditors_handler  (add / reset / delete)
# ============================================================

from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

from tickets.utils import is_admin


# ============================================================
# GET — page render
# ============================================================
@login_required
def settings_auditor_page(request):
    """Display the Auditor Credentials page."""

    if not is_admin(request.user):
        messages.error(request, 'Administrator access required.')
        return redirect('admin_dashboard')

    auditor_group, _ = Group.objects.get_or_create(name='Auditor')

    auditors = (
        User.objects
        .filter(groups=auditor_group)
        .order_by('username')
    )

    context = {
        'page_title': 'Auditor Credentials',
        'auditors': auditors,
    }
    return render(request, 'admin_panel/settings_auditor.html', context)


# ============================================================
# POST — add / reset / delete
# ============================================================
@login_required
@require_http_methods(['POST'])
def settings_auditors_handler(request):
    """POST handler for auditor credential management."""

    if not is_admin(request.user):
        messages.error(request, 'Administrator access required.')
        return redirect('admin_dashboard')

    action   = request.POST.get('action', '').strip()
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    auditor_group, _ = Group.objects.get_or_create(name='Auditor')

    # --------------------------------------------------------
    # ADD / UPDATE
    # --------------------------------------------------------
    if action == 'add':
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('settings_auditor_page')

        if len(password) < 4 or len(password) > 14:
            messages.error(request, 'Password must be 4–14 characters.')
            return redirect('settings_auditor_page')

        existing = User.objects.filter(username=username).first()

        if existing and not existing.groups.filter(name='Auditor').exists():
            messages.error(
                request,
                f'Username "{username}" is already in use by a non-auditor account.'
            )
            return redirect('settings_auditor_page')

        if existing:
            user = existing
            created = False
        else:
            user = User(username=username)
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            created = True

        user.set_password(password)
        user.save()
        user.groups.add(auditor_group)

        if created:
            messages.success(request, f'Auditor "{username}" created.')
        else:
            messages.success(request, f'Auditor "{username}" password updated.')

        return redirect('settings_auditor_page')

    # --------------------------------------------------------
    # RESET PASSWORD
    # --------------------------------------------------------
    if action == 'reset':
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('settings_auditor_page')

        if len(password) < 4 or len(password) > 14:
            messages.error(request, 'Password must be 4–14 characters.')
            return redirect('settings_auditor_page')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, f'Auditor "{username}" not found.')
            return redirect('settings_auditor_page')

        if not user.groups.filter(name='Auditor').exists():
            messages.error(request, f'"{username}" is not an auditor.')
            return redirect('settings_auditor_page')

        user.set_password(password)
        user.save()

        messages.success(request, f'Password reset for "{username}".')
        return redirect('settings_auditor_page')

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------
    if action == 'delete':
        if not username:
            messages.error(request, 'Username is required.')
            return redirect('settings_auditor_page')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, f'Auditor "{username}" not found.')
            return redirect('settings_auditor_page')

        if user.is_superuser:
            messages.error(request, 'Cannot remove a superuser from this page.')
            return redirect('settings_auditor_page')

        # Remove from Auditor group (keeps user record)
        user.groups.remove(auditor_group)
        messages.success(
            request,
            f'Auditor "{username}" removed from the Auditor group.'
        )

        # To fully delete the user instead, uncomment:
        # user.delete()
        # messages.success(request, f'Auditor "{username}" deleted.')

        return redirect('settings_auditor_page')

    # --------------------------------------------------------
    # Unknown action
    # --------------------------------------------------------
    return HttpResponseBadRequest('Unknown action.')