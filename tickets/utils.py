# tickets/utils.py
import os
import re
import datetime
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
import logging

logger = logging.getLogger(__name__)

# ============================================
# FIX: Ticket Number Generator - Sequential
# Format: 0001, 0002, 0003, ...
# ============================================
def generate_ticket_number():
    """
    Generate sequential ticket numbers starting from 0001
    Format: 0001, 0002, 0003, ... up to 9999
    """
    from tickets.models import Ticket  # Lazy import to avoid circular dependency

    # Get the last ticket by ID (most recent)
    last_ticket = Ticket.objects.all().order_by('id').last()
    
    if last_ticket and last_ticket.ticket_number:
        # Extract the number part and increment
        try:
            # Try to convert the entire ticket_number to int
            # This works for pure numbers like "0001", "0002"
            last_number = int(last_ticket.ticket_number)
            new_number = last_number + 1
        except ValueError:
            # If ticket_number is not a pure number (e.g., old format GPLAST-20260701-0001)
            # Try to extract the last 4 digits
            try:
                # Extract the last 4 digits
                match = re.search(r'(\d{4})$', last_ticket.ticket_number)
                if match:
                    last_number = int(match.group(1))
                    new_number = last_number + 1
                else:
                    # Fallback: start from 1
                    new_number = 1
            except (ValueError, AttributeError):
                new_number = 1
    else:
        # No tickets exist, start from 1
        new_number = 1
    
    # Format as 4-digit with leading zeros (0001, 0002, ...)
    return f"{new_number:04d}"

# ============================================
# FILE VALIDATION
# ============================================
def validate_attachment(file):
    """Validate uploaded file"""
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

# ============================================
# EMAIL HELPER FUNCTIONS
# ============================================
def get_status_color(status):
    """Return color code for status"""
    colors = {
        'Open': '#22C55E',
        'Assigned': '#3B82F6',
        'Hold': '#F59E0B',
        'Escalated': '#EF4444',
        'Closed': '#6B7280',
        'In Progress': '#8B5CF6',
        'Resolved': '#10B981',
    }
    return colors.get(status, '#6B7280')

def get_priority_color(priority):
    """Return color for priority"""
    colors = {
        'Critical': '#DC2626',
        'High': '#F59E0B',
        'Medium': '#3B82F6',
        'Low': '#6B7280',
    }
    return colors.get(priority, '#6B7280')

def get_action_icon(action):
    """Return icon for action"""
    icons = {
        'Created': '✅',
        'Closed': '📌',
        'Reopened': '🔄',
        'Assigned': '👤',
        'Escalated': '⬆️',
        'Updated': '📝',
    }
    return icons.get(action, '📧')

# ============================================
# BUILD HTML EMAIL CONTENT - INLINE STYLES
# ============================================
def build_html_email(ticket, action, remarks, recipient_name, status_color, priority_color, action_icon):
    """Build HTML email content with inline styles"""
    
    # Get site URL
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    # Format dates
    created_at = ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else 'N/A'
    closed_at = ticket.closed_at.strftime('%Y-%m-%d %H:%M') if ticket.closed_at else None
    
    # Build the HTML
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket {ticket.ticket_number}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f4; line-height: 1.6;">

<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
    <tr>
        <td align="center">
            <!-- Main Container -->
            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; max-width: 600px; width: 100%;">
                
                <!-- HEADER -->
                <tr>
                    <td style="background: linear-gradient(135deg, #e94560, #c0392b); padding: 30px 25px; text-align: center;">
                        <h1 style="color: #ffffff; font-size: 24px; margin: 0; font-weight: 700;">{action_icon} Ticket {action}</h1>
                        <div style="color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 5px;">GPLAST Support System</div>
                        <div style="display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 16px; border-radius: 50px; color: #ffffff; font-size: 14px; font-weight: 600; margin-top: 10px;">#{ticket.ticket_number}</div>
                    </td>
                </tr>
                
                <!-- CONTENT -->
                <tr>
                    <td style="padding: 30px 25px;">
                        
                        <!-- Greeting -->
                        <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                            Hello <strong style="color: #1a202c;">{recipient_name}</strong>,
                        </p>
                        
                        <p style="color: #4a5568; margin: 0 0 20px 0;">
                            This is to inform you that ticket <strong style="color: #1a202c;">#{ticket.ticket_number}</strong> 
                            has been <strong style="color: {status_color};">{action.lower()}</strong> successfully.
                        </p>
                        
                        <!-- Status Badges -->
                        <div style="margin: 15px 0; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                            <span style="display: inline-block; padding: 6px 16px; border-radius: 50px; font-size: 13px; font-weight: 600; color: #ffffff; background-color: {status_color};">
                                {ticket.status}
                            </span>
                            <span style="display: inline-block; padding: 4px 14px; border-radius: 50px; font-size: 12px; font-weight: 600; color: #ffffff; background-color: {priority_color};">
                                {ticket.priority} Priority
                            </span>
                        </div>
                        
                        <!-- Ticket Details Table -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f7fafc; border-radius: 8px; overflow: hidden; margin: 20px 0; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7; width: 120px;">Ticket Number</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;"><strong>#{ticket.ticket_number}</strong></td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Subject</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.subject}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Status</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.status}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Priority</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.priority}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Unit</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.unit.full_name if ticket.unit else 'N/A'} ({ticket.unit.code if ticket.unit else 'N/A'})</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Department</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.department.name if ticket.department else 'N/A'}</td>
                            </tr>
                            {f'''
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Assigned To</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.assigned_person}</td>
                            </tr>
                            ''' if ticket.assigned_person else ''}
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Created By</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.employee_name or 'N/A'} ({ticket.employee_id or 'N/A'})</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Contact</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{ticket.email or 'N/A'} {f'| {ticket.mobile}' if ticket.mobile else ''}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Created</td>
                                <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #1a202c;">{created_at}</td>
                            </tr>
                            {f'''
                            <tr>
                                <td style="padding: 10px 16px; font-weight: 600; color: #4a5568; background-color: #edf2f7;">Closed</td>
                                <td style="padding: 10px 16px; color: #1a202c;">{closed_at}</td>
                            </tr>
                            ''' if closed_at else ''}
                        </table>
                        
                        <!-- Description -->
                        <h3 style="color: #1a202c; margin: 20px 0 10px; font-size: 16px;">📝 Description</h3>
                        <div style="background: #f7fafc; border-radius: 8px; padding: 16px 20px; margin: 0 0 15px 0; border-left: 4px solid #e94560;">
                            <p style="margin: 0; color: #2d3748; font-size: 14px;">{ticket.description or 'No description provided.'}</p>
                        </div>
                        
                        <!-- Remarks -->
                        {f'''
                        <h3 style="color: #1a202c; margin: 20px 0 10px; font-size: 16px;">📌 Remarks</h3>
                        <div style="background: #fffbeb; border-radius: 8px; padding: 16px 20px; margin: 0 0 15px 0; border-left: 4px solid #F59E0B;">
                            <p style="margin: 0; color: #78350f; font-size: 14px;">{remarks}</p>
                        </div>
                        ''' if remarks else ''}
                        
                        <!-- View Ticket Button -->
                        <div style="text-align: center; margin: 25px 0 10px;">
                            <a href="{site_url}/ticket/{ticket.id}/" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #e94560, #c0392b); color: #ffffff; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 15px;">
                                🔍 View Ticket Details
                            </a>
                        </div>
                        
                        <p style="color: #718096; font-size: 13px; text-align: center; margin-top: 15px;">
                            Or copy and paste this link:<br>
                            <span style="color: #e94560; word-break: break-all;">{site_url}/ticket/{ticket.id}/</span>
                        </p>
                    </td>
                </tr>
                
                <!-- FOOTER -->
                <tr>
                    <td style="padding: 20px 25px; background: #f7fafc; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0;">
                        <p style="margin: 0;">
                            This is an automated notification from <strong>GPLAST ERP System</strong>.<br>
                            For support, please contact: <a href="mailto:{settings.DEFAULT_FROM_EMAIL}" style="color: #e94560; text-decoration: none;">{settings.DEFAULT_FROM_EMAIL}</a>
                        </p>
                        <p style="margin: 5px 0 0; font-size: 11px; color: #a0aec0;">
                            &copy; {timezone.now().year} GPLAST. All rights reserved.
                        </p>
                    </td>
                </tr>
                
            </table>
        </td>
    </tr>
</table>

</body>
</html>
'''
    return html

# ============================================
# BUILD PLAIN TEXT EMAIL
# ============================================
def build_plain_text_email(ticket, action, remarks, recipient_name):
    """Build plain text email as fallback"""
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    text = f"""
{'-' * 60}
GPLAST ERP Support - Ticket Notification
{'-' * 60}

Hello {recipient_name},

This is to inform you that ticket {ticket.ticket_number} has been {action.lower()} successfully.

📋 TICKET DETAILS:
───────────────────────────────────────────────────
  Ticket Number: {ticket.ticket_number}
  Subject:       {ticket.subject}
  Status:        {ticket.status}
  Priority:      {ticket.priority}
  Unit:          {ticket.unit.full_name if ticket.unit else 'N/A'}
  Department:    {ticket.department.name if ticket.department else 'N/A'}
  Assigned To:   {ticket.assigned_person or 'Not assigned'}
  Created:       {ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else 'N/A'}
  Employee ID:   {ticket.employee_id or 'N/A'}
  Employee Name: {ticket.employee_name or 'N/A'}
  Mobile:        {ticket.mobile or 'N/A'}
  Email:         {ticket.email or 'N/A'}
───────────────────────────────────────────────────

📝 DESCRIPTION:
{ticket.description or 'No description provided.'}

{'📌 REMARKS:' if remarks else ''}
{remarks or ''}

🔗 VIEW TICKET:
{site_url}/ticket/{ticket.id}/

{'-' * 60}
This is an automated notification from GPLAST ERP System.
For support, please contact: {settings.DEFAULT_FROM_EMAIL}
© {timezone.now().year} GPLAST. All rights reserved.
{'-' * 60}
"""
    return text

# ============================================
# MAIN EMAIL SENDING FUNCTION
# ============================================
def send_ticket_email(ticket, action, remarks=None):
    """
    Send ticket notification email with proper HTML formatting
    """
    from tickets.models import AdminNotificationEmail

    # Get admin emails for BCC
    admin_emails = list(AdminNotificationEmail.objects.filter(is_active=True).values_list('email', flat=True))
    
    # Fallback to default sender if no admin emails configured
    if not admin_emails:
        admin_emails = [settings.EMAIL_HOST_USER] if settings.EMAIL_HOST_USER else []
    
    # Get recipient email
    recipient_name = ticket.employee_name or "User"
    user_recipient = [ticket.email] if ticket.email else []
    
    # If no recipients, log and return
    if not user_recipient and not admin_emails:
        logger.warning(f"Email not sent for ticket {ticket.ticket_number}. No recipients.")
        return False
    
    # Get colors and icons
    status_color = get_status_color(ticket.status)
    priority_color = get_priority_color(ticket.priority)
    action_icon = get_action_icon(action)
    
    # Build email content
    html_message = build_html_email(ticket, action, remarks, recipient_name, status_color, priority_color, action_icon)
    plain_message = build_plain_text_email(ticket, action, remarks, recipient_name)
    
    # Subject
    subject = f"{action_icon} [GPLAST] Ticket {ticket.ticket_number} - {action}"
    
    try:
        # Create email with HTML and plain text
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=user_recipient,
            bcc=admin_emails,
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        
        # Attach HTML version
        email.attach_alternative(html_message, "text/html")
        
        # Add headers
        email.extra_headers['X-Priority'] = '3'
        email.extra_headers['X-Mailer'] = 'GPLAST ERP System'
        email.extra_headers['X-Auto-Response-Suppress'] = 'OOF, AutoReply'
        
        # Send email
        email.send(fail_silently=False)
        
        # Log success
        log_message = f"✅ Email sent for ticket {ticket.ticket_number} ({action})"
        if user_recipient:
            log_message += f" To: {user_recipient}"
        if admin_emails:
            log_message += f" Bcc: {admin_emails}"
        logger.info(log_message)
        print(log_message)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email for ticket {ticket.ticket_number}: {str(e)}")
        print(f"❌ Failed to send email: {str(e)}")
        return False

# ============================================
# TEST EMAIL FUNCTION
# ============================================
def send_test_email(recipient_email=None):
    """
    Send a test email to verify configuration
    """
    if not recipient_email:
        recipient_email = settings.EMAIL_HOST_USER
    
    if not recipient_email:
        logger.error("❌ No recipient email provided for test")
        print("❌ No recipient email provided for test")
        return False
    
    # Build test HTML
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Email - GPLAST</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background: linear-gradient(135deg, #e94560, #c0392b); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">🧪 Test Email</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">GPLAST ERP System</p>
        </div>
        <div style="padding: 30px;">
            <h2 style="color: #22C55E;">✅ Email Configuration is Working!</h2>
            <p>This is a test email to confirm that the email system is properly configured.</p>
            <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p><strong>📧 From:</strong> {settings.DEFAULT_FROM_EMAIL}</p>
                <p><strong>📅 Sent:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>🏢 System:</strong> GPLAST ERP</p>
                <p><strong>📡 Host:</strong> {settings.EMAIL_HOST}:{settings.EMAIL_PORT}</p>
            </div>
            <p style="color: #22C55E; font-weight: bold;">✅ If you received this email, your email configuration is working correctly!</p>
            <hr>
            <p style="text-align: center; color: #666;">
                <a href="{getattr(settings, 'SITE_URL', 'http://localhost:8000')}" style="color: #e94560;">Visit GPLAST Portal</a>
            </p>
        </div>
        <div style="background: #f7fafc; padding: 20px; text-align: center; font-size: 12px; color: #718096;">
            <p>© {timezone.now().year} GPLAST. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    
    plain_message = f"""
Test Email from GPLAST ERP System
{'=' * 50}

This is a test email to confirm that the email configuration is working correctly.

Configuration:
- Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
- User: {settings.EMAIL_HOST_USER}
- TLS: {settings.EMAIL_USE_TLS}
- SSL: {settings.EMAIL_USE_SSL}
- From: {settings.DEFAULT_FROM_EMAIL}

✅ If you received this email, your email configuration is working!

{'=' * 50}
GPLAST ERP Support
© {timezone.now().year} GPLAST. All rights reserved.
"""
    
    subject = "🧪 [GPLAST] Test Email - Configuration Working!"
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        email.attach_alternative(html_message, "text/html")
        email.extra_headers['X-Priority'] = '3'
        email.extra_headers['X-Mailer'] = 'GPLAST ERP System'
        email.send(fail_silently=False)
        
        logger.info(f"✅ Test email sent successfully to {recipient_email}")
        print(f"✅ Test email sent successfully to {recipient_email}")
        print(f"📧 From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"📧 Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test email failed: {str(e)}")
        print(f"❌ Test email failed: {str(e)}")
        print(f"📧 Configuration: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print(f"📧 User: {settings.EMAIL_HOST_USER}")
        return False