# tickets/middleware.py
import re
from django.http import HttpResponseForbidden


class AuditorWriteGuardMiddleware:
    """
    Blocks POST/PUT/PATCH/DELETE for Auditor users except on whitelisted paths.
    """

    ALLOWED_WRITE_PATTERNS = (
        r'^/admin_view/tickets/\d+/comment/?$',
        r'^/admin_view/tickets/\d+/priority/?$',
        r'^/admin_view/reports/export/',
        r'^/password/change/?',
        r'^/logout/?',
        r'^/login/?',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and user.groups.filter(name='Auditor').exists()
            and request.method in ('POST', 'PUT', 'PATCH', 'DELETE')
        ):
            allowed = any(
                re.match(p, request.path) for p in self.ALLOWED_WRITE_PATTERNS
            )
            if not allowed:
                return HttpResponseForbidden('Read-only oversight access.')
        return self.get_response(request)