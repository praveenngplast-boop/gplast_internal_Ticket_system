# tickets/views/notification_views.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from tickets.models import Ticket
import logging

logger = logging.getLogger(__name__)

@login_required
def get_notifications(request):
    """
    Get notifications for admin users
    Returns JSON with notification data
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        unviewed_tickets = Ticket.objects.filter(
            is_viewed=False
        ).select_related(
            'unit', 'department'
        ).order_by('-created_at')[:10]
        
        html = render_to_string(
            'includes/notification_dropdown.html',
            {'unviewed_tickets': unviewed_tickets},
            request=request
        )
        
        return JsonResponse({
            'success': True,
            'html': html,
            'count': unviewed_tickets.count(),
            'tickets': [
                {
                    'id': ticket.id,
                    'ticket_number': ticket.ticket_number,
                    'subject': ticket.subject,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'employee_name': ticket.employee_name,
                    'created_at': ticket.created_at.isoformat(),
                }
                for ticket in unviewed_tickets
            ]
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def refresh_notifications(request):
    """
    AJAX view to refresh notification dropdown content - Admin Only
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'html': '', 'count': 0, 'error': 'Unauthorized'}, status=403)
    
    try:
        unviewed_tickets = Ticket.objects.filter(
            is_viewed=False
        ).select_related(
            'unit', 'department'
        ).order_by('-created_at')[:10]
        
        html = render_to_string(
            'includes/notification_dropdown.html',
            {'unviewed_tickets': unviewed_tickets},
            request=request
        )
        
        return JsonResponse({
            'html': html,
            'count': unviewed_tickets.count()
        })
    except Exception as e:
        logger.error(f"Error refreshing notifications: {e}")
        return JsonResponse({'html': '', 'count': 0, 'error': str(e)})

@login_required
def mark_notification_read(request, ticket_id):
    """
    Mark a specific ticket notification as read
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id, is_viewed=False)
        ticket.is_viewed = True
        ticket.save()
        
        # Get updated count
        unviewed_count = Ticket.objects.filter(is_viewed=False).count()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read',
            'unviewed_count': unviewed_count
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket not found'}, status=404)
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def mark_all_notifications_read(request):
    """
    Mark all notifications as read for admin users
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        count = Ticket.objects.filter(is_viewed=False).update(is_viewed=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Marked {count} notifications as read',
            'marked_count': count
        })
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================================
# ✅ NEW: DESKTOP (WINDOWS TOAST) NOTIFICATION ENDPOINTS
# Used by static/js/shared/desktop_notifications.js
# ============================================================

from django.utils import timezone as _tz
from django.views.decorators.http import require_GET, require_POST
from tickets.models import Notification


@login_required
@require_GET
def poll_notifications(request):
    """Return new notifications for the logged-in user as JSON."""
    try:
        since = int(request.GET.get('since', 0))
    except (TypeError, ValueError):
        since = 0

    qs = Notification.objects.filter(recipient=request.user)

    if since > 0:
        qs = qs.filter(id__gt=since)
    else:
        cutoff = _tz.now() - _tz.timedelta(hours=24)
        qs = qs.filter(created_at__gte=cutoff)

    qs = qs.order_by('id')[:50]

    items = [
        {
            'id': n.id,
            'event': n.event,
            'title': n.title,
            'body': n.body,
            'url': n.url,
            'created_at': n.created_at.isoformat(),
        }
        for n in qs
    ]

    last_id = items[-1]['id'] if items else since

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return JsonResponse({
        'notifications': items,
        'last_id': last_id,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_read(request, notification_id):
    """Mark a single notification as read (only the recipient can)."""
    updated = Notification.objects.filter(
        id=notification_id,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True, read_at=_tz.now())

    return JsonResponse({'updated': updated})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all unread notifications for the logged-in user as read."""
    updated = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True, read_at=_tz.now())

    return JsonResponse({'updated': updated})
