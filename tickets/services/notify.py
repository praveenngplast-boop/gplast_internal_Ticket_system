"""
Central notification service for GPLAST Ticket System.

Every part of the app that needs to notify a user calls notify().
This module decides who receives a notification, writes the
Notification row, and (optionally) queues an email.

The browser polls /notifications/poll/ and turns new rows into
native Windows toasts.

Design for GPLAST:
- Admins and Unit Heads always have logins → they get toasts.
- Ticket assignees are names in EmployeeMaster, not Users →
  they get emails (not toasts) using the email on file.
- The ticket creator gets a toast when they have a real login.
"""

from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

from tickets.models import (
    Notification,
    Ticket,
    UnitHead,
    EmployeeMaster,
)


# ============================================================
# PUBLIC API
# ============================================================

def notify(
    recipients,
    event,
    title,
    body='',
    url='',
    ticket=None,
    actor=None,
    email=False,
    extra_emails=None,
):
    """
    Create a Notification for each recipient.

    Args:
        recipients    : iterable of User objects (or single User)
        event         : one of Notification.EVENT_CHOICES keys
        title         : main line shown in the Windows toast
        body          : secondary line shown in the Windows toast
        url           : where to navigate on click (relative or absolute)
        ticket        : Ticket instance (optional)
        actor         : User who triggered the event (optional)
        email         : if True, queue email for all recipient users
        extra_emails  : list of additional email addresses that should
                        receive the notification by email even though
                        they don't have a User account (e.g. assignee)

    Returns:
        list of Notification objects that were created.
    """
    if recipients is None:
        recipients = []

    if isinstance(recipients, User):
        recipients = [recipients]

    seen = set()
    cleaned = []
    for user in recipients:
        if user is None:
            continue
        if actor is not None and user.pk == actor.pk:
            continue
        if user.pk in seen:
            continue
        seen.add(user.pk)
        cleaned.append(user)

    created = []
    if cleaned:
        rows = [
            Notification(
                recipient=user,
                actor=actor,
                ticket=ticket,
                event=event,
                title=title[:200],
                body=body or '',
                url=url or '',
            )
            for user in cleaned
        ]
        created = Notification.objects.bulk_create(rows)

    # Email fallback — either for the recipients (if email=True) or
    # for extra_emails (assignee without login).
    emails_to_send = []
    if email:
        for n in created:
            if n.recipient.email:
                emails_to_send.append((n.recipient.email, n))
    if extra_emails:
        # Send a "virtual" notification payload to each extra email
        for addr in extra_emails:
            if addr:
                emails_to_send.append((addr, None))

    if emails_to_send:
        _queue_emails(emails_to_send, ticket, title, body, url)

    return created


# ============================================================
# RECIPIENT RESOLVERS
# ============================================================

def admins():
    """All active users with is_staff=True."""
    return list(User.objects.filter(is_active=True, is_staff=True))


def unit_head_users(unit):
    """User accounts linked to Unit Head profiles for this unit."""
    if unit is None:
        return []
    profiles = UnitHead.objects.filter(
        unit=unit, is_active=True
    ).select_related('user')
    return [p.user for p in profiles if p.user_id and p.user.is_active]


def ticket_creator(ticket):
    """
    The User who created the ticket.
    Returns None if creator is the shared dummy account GPLERPUSERS.
    """
    if ticket is None or not ticket.created_by_user_id:
        return None
    user = ticket.created_by_user
    if user is None:
        return None
    if user.username == 'GPLERPUSERS':
        return None
    return user


def ticket_assignee(ticket):
    """
    Best-effort lookup of the assigned person as a Django User.
    Returns None if nothing matches.
    """
    if ticket is None or not ticket.assigned_person:
        return None

    name = ticket.assigned_person.strip()
    if not name:
        return None

    user = (
        User.objects.filter(username__iexact=name).first()
        or User.objects.filter(email__iexact=name).first()
        or User.objects.filter(first_name__iexact=name).first()
        or User.objects.filter(last_name__iexact=name).first()
    )
    if user:
        return user

    try:
        emp = EmployeeMaster.objects.filter(
            employee_name__iexact=name,
            is_active=True,
        ).first()
        if emp:
            if emp.email:
                user = User.objects.filter(email__iexact=emp.email).first()
                if user:
                    return user
            user = User.objects.filter(username__iexact=emp.employee_id).first()
            if user:
                return user
    except Exception:
        pass

    return None


def ticket_assignee_email(ticket):
    """
    Resolve the assignee's email from EmployeeMaster by name.
    Returns None if no match or no email on file.
    """
    if ticket is None or not ticket.assigned_person:
        return None

    name = ticket.assigned_person.strip()
    if not name:
        return None

    try:
        emp = EmployeeMaster.objects.filter(
            employee_name__iexact=name,
            is_active=True,
        ).first()
        if emp and emp.email:
            return emp.email
    except Exception:
        pass

    return None


def _base_recipients(ticket):
    """
    The always-notify set for any ticket event:
    all admins + the unit head(s) of the ticket's unit.
    """
    recipients = admins()
    recipients += unit_head_users(ticket.unit)
    return recipients


# ============================================================
# HIGH-LEVEL EVENT HELPERS
# ============================================================

def notify_ticket_created(ticket, actor=None):
    """Ticket created → admins + unit head."""
    return notify(
        recipients=_base_recipients(ticket),
        event='created',
        title=f"New ticket #{ticket.ticket_number}",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
    )


def notify_ticket_assigned(ticket, assignee=None, actor=None):
    """
    Ticket assigned → admins + unit head + assignee (toast if User, email always).
    """
    recipients = _base_recipients(ticket)
    if assignee is not None:
        recipients.append(assignee)

    assignee_email = ticket_assignee_email(ticket)
    extra_emails = [assignee_email] if assignee_email else []

    assigned_name = ticket.assigned_person or 'someone'
    return notify(
        recipients=recipients,
        event='assigned',
        title=f"Ticket #{ticket.ticket_number} assigned to {assigned_name}",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
        extra_emails=extra_emails,
    )


def notify_ticket_replied(ticket, reply, actor=None):
    """
    New reply → admins + unit head + creator + assignee (email).
    """
    recipients = _base_recipients(ticket)

    creator = ticket_creator(ticket)
    if creator:
        recipients.append(creator)

    assignee_user = ticket_assignee(ticket)
    if assignee_user:
        recipients.append(assignee_user)

    assignee_email = ticket_assignee_email(ticket)
    extra_emails = [assignee_email] if assignee_email else []

    return notify(
        recipients=recipients,
        event='replied',
        title=f"New reply on #{ticket.ticket_number}",
        body=(reply.body or ticket.subject)[:120],
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
        extra_emails=extra_emails,
    )


def notify_status_changed(ticket, old_status, new_status, actor=None):
    """
    Status changed (Hold / Escalated / Closed / Reopened).
    → admins + unit head + creator + assignee (email).
    """
    recipients = _base_recipients(ticket)

    creator = ticket_creator(ticket)
    if creator:
        recipients.append(creator)

    assignee_user = ticket_assignee(ticket)
    if assignee_user:
        recipients.append(assignee_user)

    assignee_email = ticket_assignee_email(ticket)
    extra_emails = [assignee_email] if assignee_email else []

    return notify(
        recipients=recipients,
        event='status_changed',
        title=f"#{ticket.ticket_number} status: {old_status} \u2192 {new_status}",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
        extra_emails=extra_emails,
    )


def notify_priority_changed(ticket, old_priority, new_priority, actor=None):
    """
    Priority changed → admins + unit head + assignee (email).
    """
    recipients = _base_recipients(ticket)

    assignee_user = ticket_assignee(ticket)
    if assignee_user:
        recipients.append(assignee_user)

    assignee_email = ticket_assignee_email(ticket)
    extra_emails = [assignee_email] if assignee_email else []

    return notify(
        recipients=recipients,
        event='priority_changed',
        title=f"#{ticket.ticket_number} priority: {old_priority} \u2192 {new_priority}",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
        extra_emails=extra_emails,
    )


def notify_mentioned(ticket, mentioned_users, actor=None):
    """Someone was @mentioned → notify them."""
    return notify(
        recipients=mentioned_users,
        event='mentioned',
        title=f"You were mentioned on #{ticket.ticket_number}",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
    )


def notify_sla_risk(ticket, percent, actor=None):
    """SLA at risk → admins + unit head."""
    return notify(
        recipients=_base_recipients(ticket),
        event='sla_risk',
        title=f"#{ticket.ticket_number} SLA at {percent}%",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
    )


def notify_sla_breach(ticket, actor=None):
    """SLA breached → admins + unit head."""
    return notify(
        recipients=_base_recipients(ticket),
        event='sla_breach',
        title=f"#{ticket.ticket_number} SLA BREACHED",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
    )


def notify_escalated(ticket, level, actor=None):
    """Ticket escalated → admins + unit head."""
    return notify(
        recipients=_base_recipients(ticket),
        event='escalated',
        title=f"#{ticket.ticket_number} escalated (level {level})",
        body=ticket.subject,
        url=_ticket_url(ticket),
        ticket=ticket,
        actor=actor,
    )


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _ticket_url(ticket):
    """Best URL for the ticket."""
    if ticket is None:
        return ''
    for name in ('admin_ticket_detail', 'ticket_detail'):
        try:
            return reverse(name, args=[ticket.pk])
        except NoReverseMatch:
            continue
    return f"/custom-admin/ticket/{ticket.pk}/"


def _queue_emails(emails_to_send, ticket, title, body, url):
    """
    Send emails for the given list of (email_address, notification_or_None).
    Non-blocking failures — never raise.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        from tickets.email_utils import send_notification_email
    except Exception as e:
        logger.warning(f"email_utils not available: {e}")
        return

    for addr, notif in emails_to_send:
        try:
            send_notification_email(
                to_email=addr,
                title=title,
                body=body,
                ticket=ticket,
                url=url,
            )
            if notif is not None:
                notif.emailed_at = timezone.now()
        except Exception as e:
            logger.warning(f"send_notification_email to {addr} failed: {e}")

    # Bulk-stamp emailed_at for the ones we have
    stampable = [n for _, n in emails_to_send if n is not None]
    if stampable:
        Notification.objects.bulk_update(stampable, ['emailed_at'])