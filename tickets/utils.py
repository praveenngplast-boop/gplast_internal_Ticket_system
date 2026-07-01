import os
import datetime
from django.utils import timezone
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
import logging

logger = logging.getLogger(__name__)

# Ticket number generator
def generate_ticket_number():
    from tickets.models import Ticket  # Lazy import to avoid circular dependency
    # Get current local date in Asia/Kolkata
    local_tz = timezone.get_current_timezone()
    now_local = timezone.now().astimezone(local_tz)
    date_str = now_local.strftime('%Y%m%d')  # YYYYMMDD
    prefix = f"GPLAST-{date_str}"
    
    # Query database for tickets starting with this prefix
    last_ticket = Ticket.objects.filter(ticket_number__startswith=prefix).order_by('-ticket_number').first()
    
    if last_ticket:
        # Extract sequence number
        last_num = last_ticket.ticket_number.split('-')[-1]
        try:
            next_seq = int(last_num) + 1
        except ValueError:
            next_seq = 1
    else:
        next_seq = 1
        
    return f"{prefix}-{next_seq:04d}"

# Server-side attachment validator
def validate_attachment(file):
    if not file:
        return
        
    # Size check (max 3MB = 3 * 1024 * 1024 bytes)
    max_size = 3 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("File size must not exceed 3MB.")
        
    # Extension check
    ext = os.path.splitext(file.name)[1].lower()
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg']
    if ext not in allowed_extensions:
        allowed_str = ", ".join(allowed_extensions)
        raise ValidationError(f"Unsupported file format '{ext}'. Allowed: {allowed_str}")

# Email notifications
def send_ticket_email(ticket, action, remarks=None):
    from tickets.models import AdminNotificationEmail  # Lazy import to avoid circular dependency

    subject = f"ERP Ticket {action}: {ticket.ticket_number} - {ticket.subject}"
    action_label = action if action else 'Updated'
    recipient_name = ticket.employee_name or ticket.full_name if hasattr(ticket, 'full_name') else ticket.employee_name

    try:
        domain = get_current_site(None).domain if hasattr(get_current_site(None), 'domain') else 'http://localhost:8000'
    except Exception:
        domain = 'http://localhost:8000'

    html_message = render_to_string(
        'emails/ticket_notification.html',
        {
            'ticket': ticket,
            'action_label': action_label,
            'recipient_name': recipient_name,
            'remarks': remarks,
            'domain': domain,
        }
    )

    plain_message = (
        f"Hello {recipient_name},\n\n"
        f"This is to inform you that ticket {ticket.ticket_number} has been {action_label.lower()} successfully.\n\n"
        f"Ticket Number: {ticket.ticket_number}\n"
        f"Subject: {ticket.subject}\n"
        f"Status: {ticket.status}\n"
        f"Raised By: {ticket.employee_name} ({ticket.employee_id})\n"
        f"Unit: {ticket.unit.full_name}\n"
        f"Department: {ticket.department.name}\n"
        f"Priority: {ticket.priority}\n"
        f"Contact Email: {ticket.email}\n"
        f"Mobile: {ticket.mobile}\n"
        + (f"\nRemarks / Closing Notes: {remarks}\n" if remarks else "")
        + "\nPlease log in to the GPLAST Ticketing System portal to view the update.\n\nRegards,\nGPLAST IT Support Team"
    )

    # Define user and admin recipients
    user_recipient = [ticket.email] if ticket.email else []
    admin_recipients_bcc = list(AdminNotificationEmail.objects.filter(is_active=True).values_list('email', flat=True))

    # Do not send if there are no recipients at all.
    if not user_recipient and not admin_recipients_bcc:
        logger.warning(f"Email not sent for ticket {ticket.ticket_number}. No recipients configured or provided.")
        return

    try:
        # Use EmailMessage to support BCC and HTML content
        email = EmailMessage(
            subject,
            plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=user_recipient,
            bcc=admin_recipients_bcc,
        )
        email.content_subtype = 'html'
        email.extra_headers['X-Priority'] = '3'
        email.body = html_message
        email.send(fail_silently=False)

        log_message = f"Successfully sent email notification for ticket {ticket.ticket_number} ({action})."
        if user_recipient:
            log_message += f" To: {user_recipient}"
        if admin_recipients_bcc:
            log_message += f" Bcc: {admin_recipients_bcc}"

        logger.info(log_message)

    except Exception as e:
        logger.error(f"Failed to send email notification for ticket {ticket.ticket_number}: {e}")
