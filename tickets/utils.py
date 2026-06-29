import os
import datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.conf import settings
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
    
    subject = f"GPLAST Ticket {action}: {ticket.ticket_number} - {ticket.subject}"
    remarks_section = f"\nRemarks/Reason: {remarks}" if remarks else ""
    
    message = f"""Hello,

This is to notify you that the support ticket {ticket.ticket_number} has been {action.lower()}.

Details:
- Ticket Number: {ticket.ticket_number}
- Subject: {ticket.subject}
- Status: {ticket.status}
- Unit: {ticket.unit.full_name}
- Department: {ticket.department.name}
- Priority: {ticket.priority}
- Raised By: {ticket.employee_name} ({ticket.employee_id})
{remarks_section}

To view details, log in to the GPLAST Ticketing System portal.

Regards,
GPLAST IT Support Team
"""
    # Recipients list
    recipients = []
    
    # Add employee email
    if ticket.email:
        recipients.append(ticket.email)
        
    # Fetch active admin notification emails
    admin_emails = list(AdminNotificationEmail.objects.filter(is_active=True).values_list('email', flat=True))
    recipients.extend(admin_emails)
    
    # Unique recipients, filter empty
    recipients = list(set([r for r in recipients if r]))
    
    if not recipients:
        return
        
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        logger.info(f"Successfully sent email notification for ticket {ticket.ticket_number} ({action}) to {recipients}")
    except Exception as e:
        logger.error(f"Failed to send email notification for ticket {ticket.ticket_number}: {e}")
