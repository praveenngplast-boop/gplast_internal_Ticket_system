from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def aging(value):
    """
    Calculate exact aging from created_at timestamp.
    Returns human-readable exact time elapsed.
    
    Examples:
    - 30m (30 minutes)
    - 1h 30m (1 hour 30 minutes)
    - 3h 15m (3 hours 15 minutes)
    - 2d 4h (2 days 4 hours)
    - 15d 6h (15 days 6 hours)
    - 2mo 15d (2 months 15 days)
    """
    if not value:
        return "N/A"
    
    # Ensure value is timezone-aware
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    now = timezone.now()
    diff = now - value
    
    # If future date (shouldn't happen, but handle gracefully)
    if diff.total_seconds() < 0:
        return "Future"
    
    seconds = diff.total_seconds()
    
    # Less than 1 minute
    if seconds < 60:
        return "Just now"
    
    # Less than 1 hour - show minutes only
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}m"
    
    # Less than 24 hours - show hours + minutes
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}m"
    
    # Less than 7 days - show days + hours
    elif seconds < 604800:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        if hours == 0:
            return f"{days}d"
        return f"{days}d {hours}h"
    
    # Less than 30 days - show days + hours
    elif seconds < 2592000:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        if hours == 0:
            return f"{days}d"
        return f"{days}d {hours}h"
    
    # More than 30 days - show months + days
    else:
        months = int(seconds // 2592000)
        remaining_days = int((seconds % 2592000) // 86400)
        if remaining_days == 0:
            return f"{months}mo"
        return f"{months}mo {remaining_days}d"


@register.filter
def aging_short(value):
    """
    Shorter version of aging - just the main unit.
    Examples: 30m, 2h, 3d, 2mo
    """
    if not value:
        return "N/A"
    
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    now = timezone.now()
    diff = now - value
    
    if diff.total_seconds() < 0:
        return "Future"
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Now"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h"
    elif seconds < 604800:
        return f"{int(seconds // 86400)}d"
    elif seconds < 2592000:
        return f"{int(seconds // 86400)}d"
    else:
        return f"{int(seconds // 2592000)}mo"


@register.filter
def aging_color(value):
    """
    Return color class based on age for styling.
    """
    if not value:
        return "aging-unknown"
    
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    now = timezone.now()
    diff = now - value
    seconds = diff.total_seconds()
    
    # Fresh: Less than 1 hour
    if seconds < 3600:
        return "aging-fresh"
    # Medium: 1-24 hours
    elif seconds < 86400:
        return "aging-medium"
    # Old: 1-7 days
    elif seconds < 604800:
        return "aging-old"
    # Very Old: More than 7 days
    else:
        return "aging-very-old"


@register.filter
def aging_tooltip(value):
    """
    Return full datetime for tooltip.
    """
    if not value:
        return ""
    return value.strftime("%d-%m-%Y %H:%M:%S")


@register.filter
def aging_hours(value):
    """
    Return age in hours (decimal) for sorting.
    """
    if not value:
        return 0
    
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    
    now = timezone.now()
    diff = now - value
    return diff.total_seconds() / 3600
