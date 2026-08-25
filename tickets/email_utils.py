from datetime import timedelta
from email.utils import parseaddr
from html import escape
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.utils import timezone

from .models import AdminNotificationEmail, EmailSchedule, Ticket, Unit, UnitHead

REPORT_LABELS = dict(EmailSchedule.REPORT_CHOICES)
STATUS_BY_REPORT = {
    'open': 'Open',
    'escalated': 'Escalated',
    'hold': 'Hold',
    'assigned': 'Assigned',
}


def parse_emails(value):
    return [email.strip() for email in value.replace(';', ',').split(',') if email.strip()]


def email_key(address):
    return (parseaddr(address)[1] or address).strip().lower()


def cc_recipients(notification_emails, extra_emails, to_emails):
    to_keys = {email_key(email) for email in to_emails}
    return [
        email for email in dict.fromkeys(notification_emails + extra_emails)
        if email_key(email) not in to_keys
    ]


def selected_units(schedule):
    if schedule.all_units:
        return Unit.objects.filter(is_active=True)
    return schedule.units.filter(is_active=True)


def tickets_for_report(report, unit=None):
    queryset = Ticket.objects.select_related('department', 'unit')
    if unit:
        queryset = queryset.filter(unit=unit)
    if report == 'escalated_aging':
        return queryset.filter(status='Escalated', escalated_at__isnull=False).order_by('escalated_at')
    return queryset.filter(status=STATUS_BY_REPORT[report]).order_by('-created_at')


def aging_category(days):
    if days <= 7:
        return '0-7 Days'
    if days <= 15:
        return '8-15 Days'
    if days <= 30:
        return '16-30 Days'
    if days <= 60:
        return '31-60 Days'
    return '>60 Days'


def report_html(report, queryset):
    now = timezone.now()
    rows = []
    aging_counts = {label: 0 for label in ('0-7 Days', '8-15 Days', '16-30 Days', '31-60 Days', '>60 Days')}
    aging_over_seven = 0
    priority_counts = {'Critical': 0, 'High': 0}
    for ticket in queryset:
        if report == 'escalated_aging':
            days = max(0, (now - ticket.escalated_at).days)
            category = aging_category(days)
            aging_counts[category] += 1
            if days > 7:
                aging_over_seven += 1
            details = f'{days} days'
            date_value = timezone.localtime(ticket.escalated_at).strftime('%d-%b-%Y %I:%M %p')
        else:
            details = ticket.priority
            date_value = timezone.localtime(ticket.created_at).strftime('%d-%b-%Y %I:%M %p')
        if ticket.priority in priority_counts:
            priority_counts[ticket.priority] += 1
        rows.append(
            '<tr>'
            f'<td style="padding:10px;border-bottom:1px solid #E8EDF5;color:#1A2A6C;font-weight:700;">{escape(ticket.ticket_number)}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #E8EDF5;color:#1A2A6C;">{escape(ticket.subject)}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #E8EDF5;color:#1A2A6C;">{escape(ticket.department.name)}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #E8EDF5;color:#1A2A6C;">{escape(str(details))}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #E8EDF5;color:#1A2A6C;">{escape(date_value)}</td>'
            '</tr>'
        )
    total_tickets = len(rows)
    title = REPORT_LABELS[report]
    if not rows:
        rows.append('<tr><td colspan="5" style="padding:14px;text-align:center;color:#8A9AB8;">No tickets found.</td></tr>')
    summary = ''
    if report == 'escalated_aging':
        summary_cards = (
            ('Total Tickets', total_tickets, '#FF6B00'),
            ('Aging >07 Days', aging_over_seven, '#EF4444'),
            ('Critical Priority', priority_counts['Critical'], '#EF4444'),
            ('High Priority', priority_counts['High'], '#F59E0B'),
        )
        cards = ''.join(
            f'<td style="width:25%;padding:6px;vertical-align:top;"><div style="background:#F8FAFF;border:1px solid #E8EDF5;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:22px;font-weight:800;color:{color};">{count}</div><div style="font-size:11px;color:#4A5A7A;font-weight:600;">{label}</div></div></td>'
            for label, count, color in summary_cards
        )
        aging_items = ''.join(
            f'<td style="padding:4px 8px;color:#4A5A7A;font-size:12px;">{label}: <strong>{count}</strong></td>'
            for label, count in aging_counts.items()
        )
        summary = (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr>{cards}</tr></table>'
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:10px 0 20px;"><tr>{aging_items}</tr></table>'
        )
    return (
        f'<h2 style="font-size:18px;color:#1A2A6C;margin:24px 0 10px;">{escape(title)}</h2>{summary}'
        '<table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-size:13px;">'
        '<tr style="background:#F8FAFF;color:#4A5A7A;font-size:11px;text-transform:uppercase;">'
        '<th align="left" style="padding:9px 10px;border-bottom:2px solid #E8EDF5;">Ticket</th>'
        '<th align="left" style="padding:9px 10px;border-bottom:2px solid #E8EDF5;">Subject</th>'
        '<th align="left" style="padding:9px 10px;border-bottom:2px solid #E8EDF5;">Department</th>'
        '<th align="left" style="padding:9px 10px;border-bottom:2px solid #E8EDF5;">Priority / Aging</th>'
        '<th align="left" style="padding:9px 10px;border-bottom:2px solid #E8EDF5;">Date</th></tr>'
        + ''.join(rows) + '</table>'
    )


def build_report_email(report_names, unit=None, recipient_name=None):
    sections = [report_html(report, tickets_for_report(report, unit)) for report in report_names]
    scope = f' - {unit.code}' if unit else ' - All Units'
    greeting_name = recipient_name or ('Admin Team' if unit is None else f'{unit.code} Unit Head')
    unit_name = f'{unit.code} ({unit.full_name})' if unit else 'all units'
    app_url = escape(settings.APP_URL, quote=True)
    return (
        '<html><body style="margin:0;padding:20px;background:#F5F7FA;font-family:Segoe UI,Arial,sans-serif;color:#1A2A6C;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center">'
        '<table role="presentation" width="700" cellspacing="0" cellpadding="0" style="max-width:700px;background:#FFFFFF;border-radius:12px;padding:28px;">'
        f'<tr><td style="border-bottom:3px solid #FF6B00;padding-bottom:14px;"><h1 style="font-size:22px;margin:0;color:#1A2A6C;">GPLAST ERP Support Report</h1><div style="color:#4A5A7A;font-size:13px;margin-top:4px;">Automated Report{escape(scope)}</div></td></tr>'
        f'<tr><td style="padding-top:20px;font-size:15px;line-height:1.6;"><strong>Dear {escape(greeting_name)},</strong><br>This is an automated report for your <strong>{escape(unit_name)}</strong>.<br><span style="color:#4A5A7A;font-size:13px;">Unit Head: <strong>{escape(greeting_name)}</strong></span></td></tr>'
        f'<tr><td style="padding-top:4px;">{"".join(sections)}</td></tr>'
        f'<tr><td align="center" style="padding:24px 0 8px;"><a href="{app_url}" style="display:inline-block;background:#FF6B00;color:#FFFFFF;text-decoration:none;font-weight:700;font-size:14px;padding:12px 24px;border-radius:6px;">Navigate to App</a></td></tr>'
        '<tr><td style="border-top:1px solid #E8EDF5;padding-top:14px;margin-top:20px;text-align:center;color:#8A9AB8;font-size:12px;">This is an automated message. Please do not reply to this email.</td></tr>'
        '</table></td></tr></table></body></html>'
    )


def send_scheduled_reports(schedule, *, force=False):
    if not schedule.enabled and not force:
        return 0
    report_names = [report for report in schedule.reports if report in REPORT_LABELS]
    if not report_names:
        return 0
    sent = 0
    subject = schedule.subject_template.replace('{{date}}', timezone.localdate().strftime('%d-%b-%Y'))
    from_email = settings.DEFAULT_FROM_EMAIL
    extra = parse_emails(schedule.additional_emails)
    notification_emails = list(AdminNotificationEmail.objects.values_list('email', flat=True))
    admin_emails = list(User.objects.filter(is_staff=True, is_active=True).exclude(email='').values_list('email', flat=True))
    units = list(selected_units(schedule))

    if schedule.send_admins:
        recipients = list(dict.fromkeys(admin_emails))
        if recipients:
            cc = cc_recipients(notification_emails + extra, recipients, recipients)
            message = EmailMultiAlternatives(subject, 'Your scheduled GPLAST ticket report.', from_email, recipients, cc=cc)
            message.attach_alternative(build_report_email(report_names), 'text/html')
            sent += message.send()

    if schedule.send_unit_heads:
        for unit in units:
            head = UnitHead.objects.filter(unit=unit, is_active=True).first()
            if head and head.email:
                recipients = [head.email]
                cc = cc_recipients(notification_emails + extra, recipients, recipients)
                message = EmailMultiAlternatives(subject, 'Your scheduled GPLAST unit ticket report.', from_email, recipients, cc=cc)
                message.attach_alternative(build_report_email(report_names, unit, head.name), 'text/html')
                sent += message.send()
    return sent
