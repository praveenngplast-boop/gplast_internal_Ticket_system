# tickets/templatetags/notification_tags.py

"""
Template tags for notifications.

Two features are covered:

1. Admin in-page dropdown (old feature)
   - get_unviewed_count
   - get_unviewed_tickets
   These count and list tickets where is_viewed=False, for the admin header.

2. Desktop toast engine (new feature)
   - get_notification_count
   - get_recent_notifications
   These reflect rows in the Notification table for the logged-in user.
"""

from django import template

from tickets.models import Ticket, Notification

register = template.Library()


# ============================================================
# 1. ADMIN IN-PAGE DROPDOWN (existing feature)
# ============================================================

@register.simple_tag
def get_unviewed_count(user):
    """Count of unviewed tickets for admin users."""
    if user.is_authenticated and user.is_staff:
        return Ticket.objects.filter(is_viewed=False).count()
    return 0


@register.simple_tag
def get_unviewed_tickets(user):
    """List of unviewed tickets for admin users."""
    if user.is_authenticated and user.is_staff:
        return (
            Ticket.objects
            .filter(is_viewed=False)
            .select_related('unit', 'department')
            .order_by('-created_at')[:10]
        )
    return []


# ============================================================
# 2. DESKTOP TOAST ENGINE (new feature)
# ============================================================

@register.simple_tag
def get_notification_count(user):
    """
    Count of unread desktop notifications for this user.

    Useful for showing a small badge on a bell icon or header text
    without polling the API from the template.
    """
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(
        recipient=user,
        is_read=False,
    ).count()


@register.simple_tag
def get_recent_notifications(user, limit=10):
    """
    Return the most recent desktop notifications for this user.
    """
    if not user.is_authenticated:
        return []
    return (
        Notification.objects
        .filter(recipient=user)
        .order_by('-created_at')[:limit]
    )