# tickets/templatetags/notification_tags.py

from django import template
from tickets.models import Ticket

register = template.Library()

@register.simple_tag
def get_unviewed_count(user):
    """Get count of unviewed tickets for admin users"""
    if user.is_authenticated and user.is_staff:
        return Ticket.objects.filter(is_viewed=False).count()
    return 0

@register.simple_tag
def get_unviewed_tickets(user):
    """Get list of unviewed tickets for admin users"""
    if user.is_authenticated and user.is_staff:
        return Ticket.objects.filter(is_viewed=False).order_by('-created_at')[:10]
    return []