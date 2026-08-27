# tickets/context_processors.py

from tickets.models import Ticket, UnitHead


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


# ============================================================
# UNIT HEAD CONTEXT PROCESSOR - NEW
# ============================================================
def unit_head_context(request):
    """
    Add Unit Head information to all templates.
    Makes the following variables available in all templates:
        - is_unit_head: Boolean (True if user is a Unit Head)
        - unit_head_data: UnitHead object (contains unit info)
        - unit_head_unit: Unit object for this Unit Head
        - unit_head_unit_code: Unit code (e.g., 'IMD')
        - unit_head_unit_name: Unit full name
    """
    context = {
        'is_unit_head': False,
        'unit_head_data': None,
        'unit_head_unit': None,
        'unit_head_unit_code': None,
        'unit_head_unit_name': None,
        'unit_head_name': None,
        'unit_head_email': None,
    }
    
    if request.user.is_authenticated:
        try:
            # Get Unit Head record for this user
            unit_head = UnitHead.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('unit').first()
            
            if unit_head:
                context['is_unit_head'] = True
                context['unit_head_data'] = unit_head
                context['unit_head_name'] = unit_head.name
                context['unit_head_email'] = unit_head.email
                
                if unit_head.unit:
                    context['unit_head_unit'] = unit_head.unit
                    context['unit_head_unit_code'] = unit_head.unit.code
                    context['unit_head_unit_name'] = unit_head.unit.full_name
                    
        except Exception:
            pass
    
    return context