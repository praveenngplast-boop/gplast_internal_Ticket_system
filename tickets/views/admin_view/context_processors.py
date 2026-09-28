# tickets/views/admin_view/context_processors.py

def oversight_context(request):
    user = request.user
    if not user.is_authenticated:
        return {}

    is_auditor = user.groups.filter(name='Auditor').exists()

    return {
        'is_auditor': is_auditor,
        'can_comment': user.has_perm('tickets.add_comment'),
        'can_change_priority': user.has_perm('tickets.change_ticket_priority'),
        'can_export_reports': user.has_perm('tickets.export_ticket_reports'),
        'can_assign': user.has_perm('tickets.assign_ticket'),
        'can_close': user.has_perm('tickets.close_ticket'),
        'can_delete': user.has_perm('tickets.delete_ticket'),
    }