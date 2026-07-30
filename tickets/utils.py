import logging
import os
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.exceptions import ValidationError
from tickets.models import AdminNotificationEmail

logger = logging.getLogger(__name__)


# =========================================================================
# EMAIL FUNCTIONS
# =========================================================================

def send_ticket_email(ticket, action, remarks=None, request=None):
    """
    Send email notification for ticket actions.
    
    TO: The employee who created the ticket (from email input box)
    CC: All Notification Emails configured in Settings
    """
    # Get ALL notification emails from Settings (for CC)
    notification_emails = list(AdminNotificationEmail.objects.values_list('email', flat=True))
    
    # Get the employee's email from the ticket
    employee_email = ticket.email
    
    # Build recipient list
    to_emails = []
    cc_emails = list(notification_emails)
    
    # Add employee email to TO if it exists
    if employee_email:
        to_emails.append(employee_email)
    
    # If no employee email but notification emails exist, use notification emails as TO
    if not to_emails and notification_emails:
        to_emails = notification_emails
        cc_emails = []
    
    # If no recipients at all, skip
    if not to_emails and not cc_emails:
        logger.warning("No recipients found. Skipping email send.")
        return
    
    # Prepare email subject
    subject = f"[GPLAST] Ticket {ticket.ticket_number} - {action}"
    
    # Build ticket URL
    ticket_url = request.build_absolute_uri(f'/ticket/{ticket.id}/') if request else f'/ticket/{ticket.id}/'
    
    # Build remarks text
    remarks_text = ""
    if remarks:
        remarks_text = f"""
        <tr>
            <td style="padding: 10px 15px; background-color: #f8f9fc; border-left: 4px solid #FF6B00; font-size: 14px; color: #333333;">
                <strong>📝 Remarks:</strong><br>
                {remarks}
            </td>
        </tr>
        """
    
    # ✅ OUTLOOK-COMPATIBLE HTML - Using tables and inline styles only
    html_content = f"""
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f7fb;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border-collapse: collapse;">
            <!-- HEADER -->
            <tr>
                <td style="background: linear-gradient(135deg, #FF6B00 0%, #FFB800 100%); padding: 25px 30px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff;">🎫 GPLAST Ticket Notification</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #ffffff; opacity: 0.9;">Ticket #{ticket.ticket_number} - {action}</p>
                </td>
            </tr>
            
            <!-- BODY -->
            <tr>
                <td style="padding: 25px 30px;">
                    <h2 style="color: #1A2A6C; font-size: 18px; margin-top: 0; border-bottom: 2px solid #FF6B00; padding-bottom: 10px;">Ticket Details</h2>
                    
                    <!-- Ticket Info -->
                    <table width="100%" cellpadding="5" cellspacing="0" border="0" style="margin-bottom: 20px; border-collapse: collapse;">
                        <tr>
                            <td width="140" style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Ticket Number</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;"><strong>{ticket.ticket_number}</strong></td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Status</td>
                            <td style="padding: 6px 0;">
                                <span style="display: inline-block; padding: 3px 12px; border-radius: 50px; font-size: 12px; font-weight: 600; background-color: {get_status_color(ticket.status)}; color: #ffffff;">{ticket.status}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Priority</td>
                            <td style="padding: 6px 0;">
                                <span style="display: inline-block; padding: 3px 12px; border-radius: 50px; font-size: 12px; font-weight: 600; background-color: {get_priority_color(ticket.priority)}; color: #ffffff;">{ticket.priority}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Subject</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.subject}</td>
                        </tr>
                    </table>
                    
                    <!-- Employee Details -->
                    <h3 style="color: #FF6B00; font-size: 14px; margin: 20px 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">👤 Employee Details</h3>
                    <table width="100%" cellpadding="5" cellspacing="0" border="0" style="margin-bottom: 20px; border-collapse: collapse;">
                        <tr>
                            <td width="140" style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Employee ID</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.employee_id or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Name</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.employee_name or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Mobile</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.mobile or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Email</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.email or 'N/A'}</td>
                        </tr>
                    </table>
                    
                    <!-- Department Details -->
                    <h3 style="color: #FF6B00; font-size: 14px; margin: 20px 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">🏢 Department Details</h3>
                    <table width="100%" cellpadding="5" cellspacing="0" border="0" style="margin-bottom: 20px; border-collapse: collapse;">
                        <tr>
                            <td width="140" style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Unit</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.unit.code if ticket.unit else 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Department</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.department.name if ticket.department else 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Created</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.created_at.strftime('%d-%m-%Y %I:%M %p') if ticket.created_at else 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: 600; color: #6B7A9E; font-size: 13px; padding: 6px 0;">Description</td>
                            <td style="color: #1A2A6C; font-size: 13px; padding: 6px 0;">{ticket.description[:200] + '...' if ticket.description and len(ticket.description) > 200 else ticket.description or 'N/A'}</td>
                        </tr>
                    </table>
                    
                    <!-- Remarks -->
                    {remarks_text}
                    
                    <!-- CC Note -->
                    <table width="100%" cellpadding="10" cellspacing="0" border="0" style="margin-top: 15px; border-collapse: collapse;">
                        <tr>
                            <td style="background-color: #f0f4ff; border-left: 4px solid #3B82F6; padding: 10px 15px; font-size: 12px; color: #1A2A6C;">
                                <strong>📧 This notification was sent to:</strong><br>
                                <strong>TO:</strong> {ticket.email or 'No employee email provided'}<br>
                                <strong>CC:</strong> {', '.join(notification_emails) if notification_emails else 'No notification emails configured'}
                            </td>
                        </tr>
                    </table>
                    
                    <!-- View Ticket Button -->
                    <table width="100%" cellpadding="10" cellspacing="0" border="0" style="margin-top: 25px;">
                        <tr>
                            <td align="center">
                                <a href="{ticket_url}" style="display: inline-block; background: linear-gradient(135deg, #FF6B00 0%, #FFB800 100%); color: #ffffff; padding: 10px 25px; border-radius: 50px; text-decoration: none; font-weight: 600; font-size: 14px;">🔍 View Ticket</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            
            <!-- FOOTER -->
            <tr>
                <td style="background-color: #f8f9fc; padding: 15px 30px; text-align: center; font-size: 12px; color: #94A3B8; border-top: 1px solid #eef2f7; border-radius: 0 0 12px 12px;">
                    This is an automated notification from <strong>GPLAST Ticketing System</strong>.<br>
                    Please do not reply to this email.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Plain text version (for email clients that don't support HTML)
    text_content = f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    GPLAST TICKET NOTIFICATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Ticket Number: {ticket.ticket_number}
    Status: {ticket.status}
    Priority: {ticket.priority}
    Subject: {ticket.subject}
    Action: {action}
    
    ───────────────────────────────────────────
    Employee Details:
    • Employee ID: {ticket.employee_id or 'N/A'}
    • Employee Name: {ticket.employee_name or 'N/A'}
    • Mobile: {ticket.mobile or 'N/A'}
    • Email: {ticket.email or 'N/A'}
    
    ───────────────────────────────────────────
    Ticket Details:
    • Unit: {ticket.unit.code if ticket.unit else 'N/A'}
    • Department: {ticket.department.name if ticket.department else 'N/A'}
    • Created: {ticket.created_at.strftime('%d-%m-%Y %I:%M %p') if ticket.created_at else 'N/A'}
    • Description: {ticket.description[:200] + '...' if ticket.description and len(ticket.description) > 200 else ticket.description or 'N/A'}
    
    {f'Remarks: {remarks}' if remarks else ''}
    
    ───────────────────────────────────────────
    This notification was sent to:
    • TO: {ticket.email or 'No employee email provided'}
    • CC: {', '.join(notification_emails) if notification_emails else 'No notification emails configured'}
    
    ───────────────────────────────────────────
    View Ticket: {ticket_url}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    This is an automated notification from GPLAST Ticketing System.
    Please do not reply to this email.
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    # Send email
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_emails,
            cc=cc_emails,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"✅ Email sent for ticket {ticket.ticket_number} - Action: {action}")
        logger.info(f"📧 TO: {to_emails}")
        logger.info(f"📧 CC: {cc_emails}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send email for ticket {ticket.ticket_number}: {str(e)}")


# =========================================================================
# HELPER FUNCTIONS FOR EMAIL COLORS
# =========================================================================

def get_status_color(status):
    """Get color for status badge"""
    colors = {
        'Open': '#22C55E',
        'Assigned': '#3B82F6',
        'Hold': '#F59E0B',
        'Escalated': '#8B5CF6',
        'Closed': '#94A3B8',
    }
    return colors.get(status, '#6B7280')


def get_priority_color(priority):
    """Get color for priority badge"""
    colors = {
        'Critical': '#EF4444',
        'High': '#F59E0B',
        'Medium': '#3B82F6',
        'Low': '#94A3B8',
    }
    return colors.get(priority, '#6B7280')


# =========================================================================
# FILE VALIDATION FUNCTIONS
# =========================================================================

def validate_attachment(file):
    """
    Validate file attachment for tickets.
    Checks file size, extension, and type.
    """
    # Max file size: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
        '.txt', '.csv', '.jpg', '.jpeg', '.png', 
        '.gif', '.bmp', '.zip', '.rar', '.7z'
    ]
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds 5MB limit. Current size: {file.size / (1024 * 1024):.2f}MB")
    
    # Check file extension
    file_name = file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type '{file_extension}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    return True


def get_file_size_display(file):
    """
    Get human-readable file size.
    """
    if hasattr(file, 'size'):
        size = file.size
    elif hasattr(file, 'file') and hasattr(file.file, 'size'):
        size = file.file.size
    else:
        return "Unknown"
    
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


# =========================================================================
# TICKET NUMBER GENERATOR
# =========================================================================

def generate_ticket_number():
    """
    Generate a unique ticket number.
    Format: TKT-YYYYMMDD-XXXX
    """
    from django.utils import timezone
    from tickets.models import Ticket
    
    now = timezone.now()
    date_str = now.strftime('%Y%m%d')
    
    # Get count of tickets created today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = Ticket.objects.filter(created_at__gte=today_start).count() + 1
    
    return f"TKT-{date_str}-{today_count:04d}"