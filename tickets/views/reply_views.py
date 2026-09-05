from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from tickets.forms import TicketReplyForm
from tickets.models import Ticket, TicketReply, UnitHead
from .employee_views import _employee_ticket_scope


def _reply_context(user, ticket):
    if user.is_staff:
        return True, 'Admin', f'Admin {user.username}'

    unit_head = UnitHead.objects.filter(
        user=user,
        is_active=True,
    ).select_related('unit').first()
    if unit_head:
        return ticket.unit_id == unit_head.unit_id, 'Unit Head', unit_head.name

    return _employee_ticket_scope(user).filter(pk=ticket.pk).exists(), 'Employee', user.get_full_name() or user.username


def _reply_redirect(user, ticket):
    if user.is_staff:
        return redirect('admin_ticket_detail', pk=ticket.pk)
    if UnitHead.objects.filter(user=user, is_active=True).exists():
        return redirect('unit_head_ticket_detail', ticket_id=ticket.pk)
    return redirect('ticket_detail', ticket_id=ticket.pk)


@login_required
def ticket_reply(request, ticket_id):
    if request.method != 'POST':
        return _reply_redirect(request.user, get_object_or_404(Ticket, pk=ticket_id))

    ticket = get_object_or_404(Ticket, pk=ticket_id)
    can_reply, role, author_name = _reply_context(request.user, ticket)
    if not can_reply:
        messages.error(request, 'You do not have permission to reply to this ticket.')
        return _reply_redirect(request.user, ticket)

    form = TicketReplyForm(request.POST, request.FILES)
    if not form.is_valid():
        for error in form.errors.values():
            messages.error(request, error.as_text().replace('* ', '').strip())
        return _reply_redirect(request.user, ticket)

    reply = form.save(commit=False)
    reply.ticket = ticket
    reply.author = request.user
    reply.author_name = author_name
    reply.author_role = role
    reply.save()
    messages.success(request, 'Your reply was added to the ticket.')
    return _reply_redirect(request.user, ticket)
