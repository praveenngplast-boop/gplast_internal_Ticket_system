# tickets/views/settings_action/admin_users.py

"""
Admin Users management views.

Provides CRUD operations for system administrators:
- List all admins
- Add a new admin
- Edit an admin's name/email
- Reset an admin's password
- Toggle active status
- Delete an admin (with safety checks)

All views require the requesting user to be an admin (is_staff=True, is_active=True).
Every mutating action is written to SettingsAuditLog.
"""

import json
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_http_methods

from tickets.views.utils import is_admin
from tickets.models import SettingsAuditLog


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def _admin_required(view_func):
    """Login required + must be an active admin."""
    return login_required(
        user_passes_test(is_admin, login_url='login')(view_func)
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(request):
    """Parse JSON body safely; fall back to POST data."""
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body or '{}')
        except (ValueError, TypeError):
            return {}
    return request.POST.dict()


def _error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _ok(message='', **extra):
    payload = {'success': True, 'message': message}
    payload.update(extra)
    return JsonResponse(payload)


def _client_ip(request):
    """Best-effort client IP extraction."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log(request, action_type, setting_name,
         old_value='', new_value='', summary=''):
    """
    Write a SettingsAuditLog entry.

    action_type: CREATE / UPDATE / DELETE / TOGGLE (matches model choices)
    setting_type is always 'PASSWORD' → reused as the closest match for
    admin-account events. If you add 'ADMIN_USER' to SETTING_TYPES later,
    swap it in here.
    """
    try:
        SettingsAuditLog.objects.create(
            performed_by=request.user if request.user.is_authenticated else None,
            performed_by_name=(
                request.user.get_full_name() or request.user.username
            ),
            action_type=action_type,
            setting_type='PASSWORD',   # see docstring above
            setting_name=setting_name,
            old_value=old_value or '',
            new_value=new_value or '',
            change_summary=summary[:500] if summary else '',
            ip_address=_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
    except Exception:
        # Audit failure must never break the main action
        pass


def _active_admin_count(exclude_user_id=None):
    qs = User.objects.filter(is_staff=True, is_active=True)
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    return qs.count()


def _serialize_admin(user):
    return {
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }


# ---------------------------------------------------------------------------
# Page view
# ---------------------------------------------------------------------------

@_admin_required
def settings_admin_users(request):
    """Render the Manage Admins page."""
    admins = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'admin_panel/settings_admin_users.html', {
        'admins': admins,
        'current_user_id': request.user.id,
        'admin_count': admins.count(),
    })


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

@_admin_required
@require_POST
def admin_user_add(request):
    data = _parse_json(request)
    username = (data.get('username') or '').strip()
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    password_confirm = data.get('password_confirm') or ''
    is_active = bool(data.get('is_active', True))

    # --- Validation ---
    if not username:
        return _error('Username is required.')
    if len(username) < 3:
        return _error('Username must be at least 3 characters.')
    if User.objects.filter(username__iexact=username).exists():
        return _error('That username is already taken.')

    if email and User.objects.filter(email__iexact=email).exists():
        return _error('That email is already in use.')

    if not password:
        return _error('Password is required.')
    if len(password) < 4 or len(password) > 14:
        return _error('Password must be 4–14 characters (matches app policy).')
    if password != password_confirm:
        return _error('Passwords do not match.')

    # --- Create ---
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_active=is_active,
            )
            _log(
                request,
                action_type='CREATE',
                setting_name=username,
                new_value=f"{first_name} {last_name} <{email}>",
                summary=f'Created admin "{username}"',
            )
    except Exception as exc:
        return _error(f'Could not create admin: {exc}', status=500)

    return _ok(
        f'Admin "{username}" created.',
        admin=_serialize_admin(user),
    )


# ---------------------------------------------------------------------------
# Edit (name / email)
# ---------------------------------------------------------------------------

@_admin_required
@require_POST
def admin_user_edit(request):
    data = _parse_json(request)
    user_id = data.get('id')
    if not user_id:
        return _error('Missing admin id.')

    try:
        user = User.objects.get(pk=user_id, is_staff=True)
    except User.DoesNotExist:
        return _error('Admin not found.', status=404)

    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip()

    if email:
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            return _error('That email is already in use.')

    old_value = f"{user.first_name} {user.last_name} <{user.email}>"

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save(update_fields=['first_name', 'last_name', 'email'])

    new_value = f"{first_name} {last_name} <{email}>"

    _log(
        request,
        action_type='UPDATE',
        setting_name=user.username,
        old_value=old_value,
        new_value=new_value,
        summary=f'Updated admin "{user.username}"',
    )

    return _ok(
        f'Admin "{user.username}" updated.',
        admin=_serialize_admin(user),
    )


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

@_admin_required
@require_POST
def admin_user_reset_password(request):
    data = _parse_json(request)
    user_id = data.get('id')
    new_password = data.get('password') or ''
    confirm = data.get('password_confirm') or ''

    if not user_id:
        return _error('Missing admin id.')

    try:
        user = User.objects.get(pk=user_id, is_staff=True)
    except User.DoesNotExist:
        return _error('Admin not found.', status=404)

    if not new_password:
        return _error('New password is required.')
    if len(new_password) < 4 or len(new_password) > 14:
        return _error('Password must be 4–14 characters.')
    if new_password != confirm:
        return _error('Passwords do not match.')

    user.set_password(new_password)
    user.save(update_fields=['password'])

    _log(
        request,
        action_type='UPDATE',
        setting_name=user.username,
        summary=f'Password reset for admin "{user.username}"',
    )

    return _ok(f'Password reset for "{user.username}".')


# ---------------------------------------------------------------------------
# Toggle active
# ---------------------------------------------------------------------------

@_admin_required
@require_POST
def admin_user_toggle_active(request):
    data = _parse_json(request)
    user_id = data.get('id')
    if not user_id:
        return _error('Missing admin id.')

    try:
        user = User.objects.get(pk=user_id, is_staff=True)
    except User.DoesNotExist:
        return _error('Admin not found.', status=404)

    if user.pk == request.user.pk:
        return _error('You cannot deactivate your own account.')

    if user.is_active:
        remaining = _active_admin_count(exclude_user_id=user.pk)
        if remaining == 0:
            return _error('Cannot deactivate the last active admin.')

    old_state = user.is_active
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])

    state = 'activated' if user.is_active else 'deactivated'

    _log(
        request,
        action_type='TOGGLE',
        setting_name=user.username,
        old_value=str(old_state),
        new_value=str(user.is_active),
        summary=f'Admin "{user.username}" {state}',
    )

    return _ok(
        f'Admin "{user.username}" {state}.',
        is_active=user.is_active,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@_admin_required
@require_POST
def admin_user_delete(request):
    data = _parse_json(request)
    user_id = data.get('id')
    if not user_id:
        return _error('Missing admin id.')

    try:
        user = User.objects.get(pk=user_id, is_staff=True)
    except User.DoesNotExist:
        return _error('Admin not found.', status=404)

    if user.pk == request.user.pk:
        return _error('You cannot delete your own account.')

    if user.is_active and _active_admin_count(exclude_user_id=user.pk) == 0:
        return _error('Cannot delete the last active admin.')

    username = user.username
    user.delete()

    _log(
        request,
        action_type='DELETE',
        setting_name=username,
        summary=f'Deleted admin "{username}"',
    )

    return _ok(f'Admin "{username}" deleted.')


# ---------------------------------------------------------------------------
# Count endpoint (used by the page + optional navbar badge)
# ---------------------------------------------------------------------------

@_admin_required
@require_http_methods(['GET'])
def admin_user_count(request):
    return JsonResponse({
        'success': True,
        'count': User.objects.filter(is_staff=True, is_active=True).count(),
    })