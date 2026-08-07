import logging
import os
import base64
from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static
from django.apps import apps

logger = logging.getLogger(__name__)


def get_logo_html():
    """
    Get logo HTML with proper base64 encoding or fallback
    """
    logo_base64 = None
    
    # Try multiple paths to find the logo
    logo_paths = [
        'images/gplast-logo.png',
        'img/gplast-logo.png',
        'logo.png',
        'images/logo.png',
        'img/logo.png',
        'gplast-logo.png',
    ]
    
    for path in logo_paths:
        logo_path = finders.find(path)
        if logo_path:
            break
    
    # If not found in static, try the static files storage
    if not logo_path:
        try:
            # Try to get from static files storage
            if staticfiles_storage.exists('images/gplast-logo.png'):
                logo_path = staticfiles_storage.path('images/gplast-logo.png')
        except:
            pass
    
    if logo_path:
        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                return f"""
                <div style="text-align: center; margin-bottom: 10px;">
                    <img src="data:image/png;base64,{logo_base64}" 
                         alt="GPLAST Logo" 
                         style="max-height: 60px; width: auto; display: inline-block;"
                         border="0">
                </div>
                """
        except Exception as e:
            logger.warning(f"Could not load logo from static: {e}")
    
    # Try using the static URL as fallback (works if logo is served via web server)
    try:
        logo_url = static('images/gplast-logo.png')
        if logo_url:
            return f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="{logo_url}" 
                     alt="GPLAST Logo" 
                     style="max-height: 60px; width: auto; display: inline-block;"
                     border="0">
            </div>
            """
    except:
        pass
    
    # Final fallback: Use company name with styling
    return """
    <div style="text-align: center; margin-bottom: 10px;">
        <div style="display: inline-block; background: linear-gradient(135deg, #FF6B00, #FF8C38); 
                    padding: 8px 25px; border-radius: 8px; color: #ffffff; 
                    font-size: 24px; font-weight: 700; font-family: Arial, sans-serif;">
            GPLAST
        </div>
    </div>
    """


def get_footer_logo_html():
    """
    Get footer logo or fallback
    """
    logo_base64 = None
    
    # Try multiple paths to find the logo
    logo_paths = [
        '../static/images/logo.png',
        'img/gplast-logo.png',
        'logo.png',
        'images/logo.png',
        'img/logo.png',
        'gplast-logo.png',
    ]
    
    for path in logo_paths:
        logo_path = finders.find(path)
        if logo_path:
            break
    
    if not logo_path:
        try:
            if staticfiles_storage.exists('images/gplast-logo.png'):
                logo_path = staticfiles_storage.path('images/gplast-logo.png')
        except:
            pass
    
    if logo_path:
        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                return f"""
                <div style="margin-bottom: 8px;">
                    <img src="data:image/png;base64,{logo_base64}" 
                         alt="GPLAST" 
                         style="max-height: 30px; width: auto; display: inline-block; opacity: 0.7;"
                         border="0">
                </div>
                """
        except Exception as e:
            logger.warning(f"Could not load footer logo: {e}")
    
    # Try using the static URL as fallback
    try:
        logo_url = static('images/gplast-logo.png')
        if logo_url:
            return f"""
            <div style="margin-bottom: 8px;">
                <img src="{logo_url}" 
                     alt="GPLAST" 
                     style="max-height: 30px; width: auto; display: inline-block; opacity: 0.7;"
                     border="0">
            </div>
            """
    except:
        pass
    
    return """
    <div style="margin-bottom: 8px;">
        <span style="font-size: 18px; font-weight: 700; color: #FF6B00; opacity: 0.7;">
            GPLAST
        </span>
    </div>
    """


def send_ticket_email(ticket, action, remarks=None, request=None):
    """
    Send email notification for ticket actions.
    
    TO: The employee who created the ticket (from email input box)
    CC: All Notification Emails configured in Settings
    """
    # Import here to avoid circular import
    from tickets.models import AdminNotificationEmail
    
    # Get notification emails from database
    notification_emails = list(AdminNotificationEmail.objects.filter(is_active=True).values_list('email', flat=True))
    employee_email = ticket.email
    
    to_emails = []
    cc_emails = list(notification_emails)
    
    # Always add the employee who created the ticket
    if employee_email:
        to_emails.append(employee_email)
    
    # If no notification emails exist, use a default from settings
    if not notification_emails:
        # Use DEFAULT_FROM_EMAIL as fallback
        default_email = settings.DEFAULT_FROM_EMAIL
        if default_email and 'erpimd@gplast.com' in default_email:
            # Add to cc if employee exists, else add to to
            if to_emails:
                cc_emails.append(default_email)
            else:
                to_emails.append(default_email)
        
        logger.warning(f"No AdminNotificationEmail records found. Using DEFAULT_FROM_EMAIL: {default_email}")
    
    # If we have to_emails but no cc, we're fine
    if not to_emails and notification_emails:
        to_emails = notification_emails
        cc_emails = []
    
    # If still no recipients, log and return
    if not to_emails and not cc_emails:
        logger.error("No recipients found. Cannot send email. Please configure AdminNotificationEmail or check DEFAULT_FROM_EMAIL.")
        return
    
    # Log what we're doing
    logger.info(f"Preparing to send email for ticket {ticket.ticket_number}")
    logger.info(f"TO: {to_emails}")
    logger.info(f"CC: {cc_emails}")
    
    subject = f"[GPLAST] Ticket {ticket.ticket_number} - {action}"
    
    if request:
        ticket_url = request.build_absolute_uri(f'/ticket/{ticket.id}/')
    else:
        try:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            ticket_url = f"http://{site.domain}/ticket/{ticket.id}/"
        except:
            ticket_url = f"/ticket/{ticket.id}/"
    
    # Get logos
    logo_html = get_logo_html()
    footer_logo_html = get_footer_logo_html()
    
    # Status badge colors
    status_colors = {
        'Open': '#22C55E',
        'Assigned': '#3B82F6',
        'Hold': '#F59E0B',
        'Escalated': '#EF4444',
        'Closed': '#6B7280',
    }
    status_color = status_colors.get(ticket.status, '#6B7280')
    
    # Priority badge colors
    priority_colors = {
        'Critical': '#EF4444',
        'High': '#F59E0B',
        'Medium': '#3B82F6',
        'Low': '#6B7280',
    }
    priority_color = priority_colors.get(ticket.priority, '#6B7280')
    
    # Status text color
    status_text_color = '#1a202c' if ticket.status == 'Hold' else '#ffffff'
    priority_text_color = '#1a202c' if ticket.priority == 'High' else '#ffffff'
    
    # Format dates for display
    created_at_str = ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else 'N/A'
    closed_at_str = ticket.closed_at.strftime('%Y-%m-%d %H:%M') if ticket.closed_at else ''
    unit_name = ticket.unit.full_name if ticket.unit else 'N/A'
    dept_name = ticket.department.name if ticket.department else 'N/A'
    
    # Build remarks HTML
    remarks_html = ""
    if remarks:
        remarks_html = f"""
        <h3 style="color: #1a202c; margin: 15px 0 8px 0; font-size: 15px;">Remarks</h3>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 0 0 10px 0;">
            <tr>
                <td style="background: #fffbeb; padding: 14px 16px; border-left: 4px solid #F59E0B; border-radius: 4px;">
                    <p style="margin: 0; color: #78350f; font-size: 13px; line-height: 1.6;">{remarks}</p>
                </td>
            </tr>
        </table>
        """
    
    # Build assigned person HTML
    assigned_html = ""
    if ticket.assigned_person:
        assigned_html = f"""
        <tr>
            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Assigned To</td>
            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{ticket.assigned_person}</td>
        </tr>
        """
    
    # Build closed at HTML
    closed_html = ""
    if ticket.closed_at:
        closed_html = f"""
        <tr>
            <td style="padding: 8px 14px; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7; border-radius: 0 0 0 8px;">Closed</td>
            <td style="padding: 8px 14px; font-size: 13px; color: #1a202c; border-radius: 0 0 8px 0;">{closed_at_str}</td>
        </tr>
        """
    
    # HTML Email Content
    html_content = f"""
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ticket {ticket.ticket_number} - {action}</title>
    </head>
    <body style="margin: 0; padding: 20px; font-family: Arial, Helvetica, sans-serif; background-color: #f7fafc;">
    
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border-collapse: collapse; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            
            <!-- HEADER WITH LOGO -->
            <tr>
                <td style="background: linear-gradient(135deg, #e94560, #c0392b); padding: 20px 20px 15px 20px; border-radius: 12px 12px 0 0; text-align: center;">
                    <!-- Logo -->
                    {logo_html}
                    <h1 style="margin: 5px 0 0 0; font-size: 22px; font-weight: 700; color: #ffffff;">Ticket {action}</h1>
                    <p style="margin: 5px 0 0 0; font-size: 13px; color: rgba(255,255,255,0.9);">GPLAST Support System</p>
                    <span style="display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 16px; border-radius: 50px; color: #ffffff; font-size: 14px; font-weight: 600; margin-top: 8px;">#{ticket.ticket_number}</span>
                </td>
            </tr>
            
            <!-- BODY -->
            <tr>
                <td style="padding: 25px 20px;">
                    
                    <!-- Greeting -->
                    <p style="font-size: 15px; color: #4a5568; margin-bottom: 15px;">Hello <strong style="color: #1a202c;">{ticket.employee_name or 'User'}</strong>,</p>
                    
                    <p style="color: #4a5568; margin-bottom: 20px; font-size: 14px;">
                        This is to inform you that ticket <strong>#{ticket.ticket_number}</strong> 
                        has been <strong>{action.lower()}</strong> successfully.
                    </p>
                    
                    <!-- Status and Priority Badges -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 15px 0;">
                        <tr>
                            <td style="padding: 0 10px 5px 0; width: auto;">
                                <table cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="padding: 6px 16px; border-radius: 50px; font-size: 13px; font-weight: 600; background: {status_color}; color: {status_text_color};">
                                            {ticket.status}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                            <td style="padding: 0 0 5px 0; width: auto;">
                                <table cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="padding: 4px 14px; border-radius: 50px; font-size: 12px; font-weight: 600; background: {priority_color}; color: {priority_text_color};">
                                            {ticket.priority} Priority
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Ticket Details -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 15px 0; background: #f7fafc; border-radius: 8px; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; width: 120px; background: #edf2f7;">Ticket Number</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;"><strong>#{ticket.ticket_number}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Subject</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{ticket.subject}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Status</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{ticket.status}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Priority</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{ticket.priority}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Unit</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{unit_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Department</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{dept_name}</td>
                        </tr>
                        {assigned_html}
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Created By</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{ticket.employee_name or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7;">Contact</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c;">{ticket.email or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #4a5568; background: #edf2f7; border-radius: 0 0 0 8px;">Created</td>
                            <td style="padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #1a202c; border-radius: 0 0 8px 0;">{created_at_str}</td>
                        </tr>
                        {closed_html}
                    </table>
                    
                    <!-- Description -->
                    <h3 style="color: #1a202c; margin: 20px 0 8px 0; font-size: 15px;">Description</h3>
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 0 0 10px 0;">
                        <tr>
                            <td style="background: #f7fafc; padding: 14px 16px; border-left: 4px solid #e94560; border-radius: 4px;">
                                <p style="margin: 0; color: #2d3748; font-size: 13px; line-height: 1.6;">{ticket.description or 'No description provided.'}</p>
                            </td>
                        </tr>
                    </table>
                    
                    {remarks_html}
                    
                    <!-- View Ticket Button -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <table cellpadding="0" cellspacing="0" border="0" style="border-radius: 50px; background: #e94560;">
                                    <tr>
                                        <td style="padding: 12px 28px; text-align: center; border-radius: 50px;">
                                            <a href="{ticket_url}" style="display: inline-block; color: #ffffff; font-size: 14px; font-weight: 600; text-decoration: none; font-family: Arial, sans-serif;">View Ticket Details</a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Fallback URL -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 12px;">
                        <tr>
                            <td align="center" style="font-size: 11px; color: #718096;">
                                Or copy this link into your browser:<br>
                                <a href="{ticket_url}" style="color: #e94560; word-break: break-all; text-decoration: underline;">{ticket_url}</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            
            <!-- FOOTER -->
            <tr>
                <td style="background: #f7fafc; padding: 15px 20px; text-align: center; font-size: 11px; color: #718096; border-top: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                    <!-- Footer Logo -->
                    {footer_logo_html}
                    <p style="margin: 0 0 3px 0;">
                        This is an automated notification from <strong>GPLAST ERP System</strong>.<br>
                        For support, contact: <a href="mailto:erpimd@gplast.com" style="color: #e94560; text-decoration: none;">erpimd@gplast.com</a>
                    </p>
                    <p style="margin: 3px 0 0 0; font-size: 10px; color: #a0aec0;">
                        &copy; {timezone.now().year} GPLAST. All rights reserved.
                    </p>
                </td>
            </tr>
        </table>
        
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    GPLAST TICKET NOTIFICATION
    ========================================
    
    Ticket Number: {ticket.ticket_number}
    Status: {ticket.status}
    Priority: {ticket.priority}
    Subject: {ticket.subject}
    Action: {action}
    
    ----------------------------------------
    Employee Details:
    * Employee ID: {ticket.employee_id or 'N/A'}
    * Employee Name: {ticket.employee_name or 'N/A'}
    * Mobile: {ticket.mobile or 'N/A'}
    * Email: {ticket.email or 'N/A'}
    
    ----------------------------------------
    Ticket Details:
    * Unit: {ticket.unit.code if ticket.unit else 'N/A'}
    * Department: {ticket.department.name if ticket.department else 'N/A'}
    * Created: {ticket.created_at.strftime('%d-%m-%Y %I:%M %p') if ticket.created_at else 'N/A'}
    * Description: {ticket.description[:200] + '...' if ticket.description and len(ticket.description) > 200 else ticket.description or 'N/A'}
    
    {f'Remarks: {remarks}' if remarks else ''}
    
    ----------------------------------------
    View Ticket: {ticket_url}
    ========================================
    This is an automated notification from GPLAST Ticketing System.
    Please do not reply to this email.
    ========================================
    """
    
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
        
        logger.info(f"Email sent for ticket {ticket.ticket_number} - Action: {action}")
        logger.info(f"TO: {to_emails}")
        logger.info(f"CC: {cc_emails}")
        
    except Exception as e:
        logger.error(f"Failed to send email for ticket {ticket.ticket_number}: {str(e)}")


def get_status_color(status):
    colors = {
        'Open': '#22C55E',
        'Assigned': '#3B82F6',
        'Hold': '#F59E0B',
        'Escalated': '#8B5CF6',
        'Closed': '#94A3B8',
    }
    return colors.get(status, '#6B7280')


def get_priority_color(priority):
    colors = {
        'Critical': '#EF4444',
        'High': '#F59E0B',
        'Medium': '#3B82F6',
        'Low': '#94A3B8',
    }
    return colors.get(priority, '#6B7280')


def validate_attachment(file):
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
        '.txt', '.csv', '.jpg', '.jpeg', '.png', 
        '.gif', '.bmp', '.zip', '.rar', '.7z'
    ]
    
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds 5MB limit. Current size: {file.size / (1024 * 1024):.2f}MB")
    
    file_name = file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type '{file_extension}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    return True


def get_file_size_display(file):
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


def generate_ticket_number():
    """Generate a unique ticket number using apps.get_model to avoid circular import"""
    Ticket = apps.get_model('tickets', 'Ticket')
    
    all_tickets = Ticket.objects.all()
    highest_num = 0
    
    for ticket in all_tickets:
        ticket_num = ticket.ticket_number
        try:
            if ticket_num.startswith('TKT-') or ticket_num.startswith('GPLAST-'):
                parts = ticket_num.split('-')
                if len(parts) >= 3:
                    num = int(parts[-1])
                    if num > highest_num:
                        highest_num = num
            elif ticket_num.isdigit():
                num = int(ticket_num)
                if num > highest_num:
                    highest_num = num
        except (ValueError, IndexError):
            continue
    
    next_num = highest_num + 1
    return f"{next_num:04d}"