# tickets/context_processors.py

from tickets.models import Ticket

def notification_count(request):
    """
    Add unviewed ticket count to all templates for admin users.
    """
    context = {
        'unviewed_count': 0,
        'unviewed_tickets': [],
    }
    
    # Only show notifications for admin users
    if request.user.is_authenticated and request.user.is_staff:
        try:
            unviewed_count = Ticket.objects.filter(is_viewed=False).count()
            unviewed_tickets = Ticket.objects.filter(is_viewed=False).order_by('-created_at')[:10]
            
            context = {
                'unviewed_count': unviewed_count,
                'unviewed_tickets': unviewed_tickets,
            }
        except Exception:
            pass
    
    return context