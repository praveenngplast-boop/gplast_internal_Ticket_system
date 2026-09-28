# tickets/views/settings_action/error_types.py

"""
Error Type Master — Admin-only settings page.

Manages the Main + Sub error types that appear in the
"Close Ticket" modal.  Replaces the previously hardcoded
lists in forms.py / models.py.

Page:
    GET  /custom-admin/settings/error-types/       → page

AJAX (all POST unless noted):
    /error-types/main/add/          → add main
    /error-types/main/edit/         → rename / reorder / toggle main
    /error-types/main/delete/       → delete main (cascades)
    /error-types/main/toggle/       → quick toggle active
    /error-types/sub/add/           → add sub
    /error-types/sub/edit/          → rename / reorder / toggle sub
    /error-types/sub/delete/        → delete sub
    /error-types/sub/toggle/        → quick toggle active
    /error-types/subs-for/<id>/     → GET — subs for a main (AJAX)
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
import logging

from tickets.models import ErrorTypeMain, ErrorTypeSub
from .settings_audit import log_settings_change
from ..utils import is_admin

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================
def _client_ip(request):
    """Return client IP, honouring X-Forwarded-For if behind a proxy."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _json_error(message, status=400):
    return JsonResponse({'success': False, 'message': message}, status=status)


# ============================================================
# PAGE VIEW
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
def settings_error_type_master(request):
    """
    Render the Error Type Master page.

    Loads all mains (active + inactive) with their subs attached,
    so the page renders fully without needing an initial AJAX call.
    """
    mains = (
        ErrorTypeMain.objects
        .prefetch_related('sub_types')
        .order_by('display_order', 'name')
    )

    # Build a serialisable structure for JS (mains + subs)
    mains_payload = []
    for main in mains:
        subs = list(
            main.sub_types
            .all()
            .order_by('display_order', 'name')
            .values('id', 'name', 'display_order', 'is_active')
        )
        mains_payload.append({
            'id': main.id,
            'name': main.name,
            'display_order': main.display_order,
            'is_active': main.is_active,
            'subs': subs,
        })

    # Counters for the header stats
    total_mains = ErrorTypeMain.objects.count()
    total_subs = ErrorTypeSub.objects.count()
    active_mains = ErrorTypeMain.objects.filter(is_active=True).count()
    active_subs = ErrorTypeSub.objects.filter(is_active=True).count()

    context = {
        'mains': mains,
        'mains_payload': mains_payload,
        'total_mains': total_mains,
        'total_subs': total_subs,
        'active_mains': active_mains,
        'active_subs': active_subs,
    }
    return render(
        request,
        'admin_panel/settings_error_type_master.html',
        context,
    )


# ============================================================
# MAIN — ADD
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_main_add(request):
    """
    Add a new Main Error Type.
    POST params:
        name           (required, unique, case-insensitive)
        display_order  (optional int, default 0)
        is_active      (optional 'true'/'false', default true)
    """
    name = (request.POST.get('name') or '').strip()
    display_order_raw = (request.POST.get('display_order') or '0').strip()
    is_active_raw = (request.POST.get('is_active') or 'true').strip().lower()

    if not name:
        return _json_error('Main error type name is required.')

    if len(name) > 100:
        return _json_error('Name is too long (max 100 characters).')

    try:
        display_order = int(display_order_raw)
        if display_order < 0:
            display_order = 0
    except (ValueError, TypeError):
        display_order = 0

    is_active = is_active_raw in ('true', '1', 'yes', 'on')

    if ErrorTypeMain.objects.filter(name__iexact=name).exists():
        return _json_error(f'A main error type named "{name}" already exists.')

    try:
        with transaction.atomic():
            main = ErrorTypeMain.objects.create(
                name=name,
                display_order=display_order,
                is_active=is_active,
                created_by=request.user.username,
            )
            log_settings_change(
                request, 'CREATE', 'ERROR_TYPE',
                f'Main: {name}',
                new_value=f'Name: {name}, Order: {display_order}, Active: {is_active}',
                change_summary=f'Added main error type: {name}',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'Main error type "{name}" added.',
            'main': {
                'id': main.id,
                'name': main.name,
                'display_order': main.display_order,
                'is_active': main.is_active,
                'subs': [],
            },
        })
    except Exception as e:
        logger.exception('Error adding main error type')
        return _json_error(f'Could not add main error type: {e}', status=500)


# ============================================================
# MAIN — EDIT
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_main_edit(request):
    """
    Edit an existing Main Error Type.
    POST params:
        id             (required)
        name           (required, unique, case-insensitive)
        display_order  (optional int)
        is_active      (optional bool)
    """
    main_id = (request.POST.get('id') or '').strip()
    name = (request.POST.get('name') or '').strip()
    display_order_raw = (request.POST.get('display_order') or '').strip()
    is_active_raw = request.POST.get('is_active', None)

    if not main_id.isdigit():
        return _json_error('Invalid main ID.')

    main = get_object_or_404(ErrorTypeMain, pk=int(main_id))

    if not name:
        return _json_error('Main error type name is required.')

    if len(name) > 100:
        return _json_error('Name is too long (max 100 characters).')

    if ErrorTypeMain.objects.filter(name__iexact=name).exclude(pk=main.pk).exists():
        return _json_error(f'A main error type named "{name}" already exists.')

    old_value = f'Name: {main.name}, Order: {main.display_order}, Active: {main.is_active}'

    # Optional fields
    if display_order_raw:
        try:
            new_order = int(display_order_raw)
            if new_order < 0:
                new_order = 0
            main.display_order = new_order
        except (ValueError, TypeError):
            pass

    if is_active_raw is not None:
        main.is_active = is_active_raw.strip().lower() in ('true', '1', 'yes', 'on')

    main.name = name

    try:
        with transaction.atomic():
            main.save()
            log_settings_change(
                request, 'UPDATE', 'ERROR_TYPE',
                f'Main: {name}',
                old_value=old_value,
                new_value=f'Name: {main.name}, Order: {main.display_order}, Active: {main.is_active}',
                change_summary=f'Updated main error type: {main.name}',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'Main error type "{main.name}" updated.',
            'main': {
                'id': main.id,
                'name': main.name,
                'display_order': main.display_order,
                'is_active': main.is_active,
            },
        })
    except Exception as e:
        logger.exception('Error editing main error type')
        return _json_error(f'Could not update main error type: {e}', status=500)


# ============================================================
# MAIN — DELETE (cascades to subs)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_main_delete(request):
    """
    Delete a Main Error Type.
    Cascades to all its Subs (FK ON DELETE CASCADE).
    POST params:
        id  (required)
    """
    main_id = (request.POST.get('id') or '').strip()
    if not main_id.isdigit():
        return _json_error('Invalid main ID.')

    main = get_object_or_404(ErrorTypeMain, pk=int(main_id))

    name = main.name
    sub_count = main.sub_types.count()

    try:
        with transaction.atomic():
            main.delete()
            log_settings_change(
                request, 'DELETE', 'ERROR_TYPE',
                f'Main: {name}',
                old_value=f'Main: {name} (had {sub_count} sub types)',
                change_summary=f'Deleted main error type: {name} and {sub_count} sub type(s)',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'Deleted "{name}" and {sub_count} sub type(s).',
            'deleted_main_id': int(main_id),
            'deleted_subs_count': sub_count,
        })
    except Exception as e:
        logger.exception('Error deleting main error type')
        return _json_error(f'Could not delete main error type: {e}', status=500)


# ============================================================
# MAIN — TOGGLE ACTIVE
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_main_toggle(request):
    """
    Flip is_active on a Main Error Type.
    POST params:
        id  (required)
    """
    main_id = (request.POST.get('id') or '').strip()
    if not main_id.isdigit():
        return _json_error('Invalid main ID.')

    main = get_object_or_404(ErrorTypeMain, pk=int(main_id))
    old = main.is_active
    main.is_active = not old

    try:
        with transaction.atomic():
            main.save(update_fields=['is_active'])
            log_settings_change(
                request, 'TOGGLE', 'ERROR_TYPE',
                f'Main: {main.name}',
                old_value=f'Active: {old}',
                new_value=f'Active: {main.is_active}',
                change_summary=f'Toggled main error type "{main.name}" to {"active" if main.is_active else "inactive"}',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'"{main.name}" is now {"active" if main.is_active else "inactive"}.',
            'id': main.id,
            'is_active': main.is_active,
        })
    except Exception as e:
        logger.exception('Error toggling main error type')
        return _json_error(f'Could not toggle main error type: {e}', status=500)


# ============================================================
# SUB — ADD
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='/login')
@require_POST
def error_type_sub_add(request):
    """
    Add a Sub Error Type under a Main.
    POST params:
        main_id        (required)
        name           (required, unique within main, case-insensitive)
        display_order  (optional int, default 0)
        is_active      (optional bool, default true)
    """
    main_id = (request.POST.get('main_id') or '').strip()
    name = (request.POST.get('name') or '').strip()
    display_order_raw = (request.POST.get('display_order') or '0').strip()
    is_active_raw = (request.POST.get('is_active') or 'true').strip().lower()

    if not main_id.isdigit():
        return _json_error('Invalid main ID.')

    if not name:
        return _json_error('Sub error type name is required.')

    if len(name) > 150:
        return _json_error('Name is too long (max 150 characters).')

    main = get_object_or_404(ErrorTypeMain, pk=int(main_id))

    try:
        display_order = int(display_order_raw)
        if display_order < 0:
            display_order = 0
    except (ValueError, TypeError):
        display_order = 0

    is_active = is_active_raw in ('true', '1', 'yes', 'on')

    if ErrorTypeSub.objects.filter(main=main, name__iexact=name).exists():
        return _json_error(f'A sub error type named "{name}" already exists under "{main.name}".')

    try:
        with transaction.atomic():
            sub = ErrorTypeSub.objects.create(
                main=main,
                name=name,
                display_order=display_order,
                is_active=is_active,
                created_by=request.user.username,
            )
            log_settings_change(
                request, 'CREATE', 'ERROR_TYPE',
                f'Sub: {main.name} / {name}',
                new_value=f'Name: {name}, Order: {display_order}, Active: {is_active}',
                change_summary=f'Added sub error type "{name}" under "{main.name}"',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'Sub error type "{name}" added.',
            'sub': {
                'id': sub.id,
                'main_id': main.id,
                'name': sub.name,
                'display_order': sub.display_order,
                'is_active': sub.is_active,
            },
        })
    except Exception as e:
        logger.exception('Error adding sub error type')
        return _json_error(f'Could not add sub error type: {e}', status=500)


# ============================================================
# SUB — EDIT
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_sub_edit(request):
    """
    Edit a Sub Error Type.
    POST params:
        id             (required)
        name           (required)
        display_order  (optional)
        is_active      (optional)
    """
    sub_id = (request.POST.get('id') or '').strip()
    name = (request.POST.get('name') or '').strip()
    display_order_raw = (request.POST.get('display_order') or '').strip()
    is_active_raw = request.POST.get('is_active', None)

    if not sub_id.isdigit():
        return _json_error('Invalid sub ID.')

    sub = get_object_or_404(ErrorTypeSub, pk=int(sub_id))

    if not name:
        return _json_error('Sub error type name is required.')

    if len(name) > 150:
        return _json_error('Name is too long (max 150 characters).')

    if ErrorTypeSub.objects.filter(main=sub.main, name__iexact=name).exclude(pk=sub.pk).exists():
        return _json_error(f'A sub error type named "{name}" already exists under "{sub.main.name}".')

    old_value = f'Name: {sub.name}, Order: {sub.display_order}, Active: {sub.is_active}'

    if display_order_raw:
        try:
            new_order = int(display_order_raw)
            if new_order < 0:
                new_order = 0
            sub.display_order = new_order
        except (ValueError, TypeError):
            pass

    if is_active_raw is not None:
        sub.is_active = is_active_raw.strip().lower() in ('true', '1', 'yes', 'on')

    sub.name = name

    try:
        with transaction.atomic():
            sub.save()
            log_settings_change(
                request, 'UPDATE', 'ERROR_TYPE',
                f'Sub: {sub.main.name} / {sub.name}',
                old_value=old_value,
                new_value=f'Name: {sub.name}, Order: {sub.display_order}, Active: {sub.is_active}',
                change_summary=f'Updated sub error type "{sub.name}" under "{sub.main.name}"',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'Sub error type "{sub.name}" updated.',
            'sub': {
                'id': sub.id,
                'main_id': sub.main.id,
                'name': sub.name,
                'display_order': sub.display_order,
                'is_active': sub.is_active,
            },
        })
    except Exception as e:
        logger.exception('Error editing sub error type')
        return _json_error(f'Could not update sub error type: {e}', status=500)


# ============================================================
# SUB — DELETE
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_sub_delete(request):
    """
    Delete a Sub Error Type.
    POST params:
        id  (required)
    """
    sub_id = (request.POST.get('id') or '').strip()
    if not sub_id.isdigit():
        return _json_error('Invalid sub ID.')

    sub = get_object_or_404(ErrorTypeSub, pk=int(sub_id))
    name = sub.name
    main_name = sub.main.name
    main_id = sub.main.id

    try:
        with transaction.atomic():
            sub.delete()
            log_settings_change(
                request, 'DELETE', 'ERROR_TYPE',
                f'Sub: {main_name} / {name}',
                old_value=f'Sub: {name} (under {main_name})',
                change_summary=f'Deleted sub error type "{name}" from "{main_name}"',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'Deleted sub error type "{name}".',
            'deleted_sub_id': int(sub_id),
            'main_id': main_id,
        })
    except Exception as e:
        logger.exception('Error deleting sub error type')
        return _json_error(f'Could not delete sub error type: {e}', status=500)


# ============================================================
# SUB — TOGGLE ACTIVE
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_POST
def error_type_sub_toggle(request):
    """
    Flip is_active on a Sub Error Type.
    POST params:
        id  (required)
    """
    sub_id = (request.POST.get('id') or '').strip()
    if not sub_id.isdigit():
        return _json_error('Invalid sub ID.')

    sub = get_object_or_404(ErrorTypeSub, pk=int(sub_id))
    old = sub.is_active
    sub.is_active = not old

    try:
        with transaction.atomic():
            sub.save(update_fields=['is_active'])
            log_settings_change(
                request, 'TOGGLE', 'ERROR_TYPE',
                f'Sub: {sub.main.name} / {sub.name}',
                old_value=f'Active: {old}',
                new_value=f'Active: {sub.is_active}',
                change_summary=f'Toggled sub error type "{sub.name}" to {"active" if sub.is_active else "inactive"}',
                ip_address=_client_ip(request),
            )
        return JsonResponse({
            'success': True,
            'message': f'"{sub.name}" is now {"active" if sub.is_active else "inactive"}.',
            'id': sub.id,
            'is_active': sub.is_active,
        })
    except Exception as e:
        logger.exception('Error toggling sub error type')
        return _json_error(f'Could not toggle sub error type: {e}', status=500)


# ============================================================
# SUBS FOR A MAIN — AJAX (used when switching mains on the page)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='login')
@require_GET
def error_type_subs_for_main(request, main_id):
    """
    Return all subs for a main (both active and inactive),
    ordered by display_order then name.
    """
    try:
        main = ErrorTypeMain.objects.get(pk=main_id)
    except ErrorTypeMain.DoesNotExist:
        return _json_error('Main error type not found.', status=404)

    subs = list(
        main.sub_types
        .all()
        .order_by('display_order', 'name')
        .values('id', 'name', 'display_order', 'is_active')
    )

    return JsonResponse({
        'success': True,
        'main': {
            'id': main.id,
            'name': main.name,
            'is_active': main.is_active,
        },
        'subs': subs,
    })