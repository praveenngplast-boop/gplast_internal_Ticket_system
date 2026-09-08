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