# tickets/views/admin_view/decorators.py

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def auditor_required(view_func):
    """Only users in 'Auditor' group (or superuser) can access."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.groups.filter(name='Auditor').exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied('Oversight access only.')
    return wrapper


def auditor_can(perm):
    """Check specific permission. Usage: @auditor_can('tickets.add_comment')"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied(f'Missing permission: {perm}')
        return wrapper
    return decorator