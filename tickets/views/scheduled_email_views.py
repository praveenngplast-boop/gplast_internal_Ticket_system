"""Admin views for scheduled ticket email reports."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from tickets.email_utils import parse_emails, send_scheduled_reports
from tickets.models import EmailSchedule, Unit, UnitHead
from .utils import is_admin


@login_required
@user_passes_test(is_admin, login_url='login')
def settings_email_reports(request):
    schedule, _ = EmailSchedule.objects.get_or_create(id=1)
    selected_frequencies = schedule.frequency if isinstance(schedule.frequency, list) else [schedule.frequency]
    if request.method == 'POST':
        previous_schedule = {
            'send_time': schedule.send_time,
            'reports': schedule.reports,
            'frequency': schedule.frequency,
        }
        action = request.POST.get('action', 'save')
        schedule.enabled = request.POST.get('enabled') == 'on'
        schedule.reports = request.POST.getlist('reports')
        schedule.frequency = request.POST.getlist('frequency') or ['daily']
        schedule.send_time = request.POST.get('send_time') or '08:00'
        schedule.send_unit_heads = request.POST.get('send_unit_heads') == 'on'
        schedule.send_admins = request.POST.get('send_admins') == 'on'
        additional_emails = request.POST.getlist('additional_emails')
        schedule.additional_emails = ','.join(
            email for value in additional_emails for email in parse_emails(value)
        )
        schedule.all_units = request.POST.get('all_units') == 'on'
        schedule.subject_template = request.POST.get(
            'subject_template', 'Ticket Report - {{date}}'
        )[:255]
        if (
            previous_schedule['send_time'] != schedule.send_time or
            previous_schedule['reports'] != schedule.reports or
            previous_schedule['frequency'] != schedule.frequency
        ):
            schedule.last_sent_at = None
        schedule.save()
        schedule.units.set(request.POST.getlist('units'))

        for unit in Unit.objects.filter(is_active=True):
            name = request.POST.get(f'head_name_{unit.id}', '').strip()
            email = request.POST.get(f'head_email_{unit.id}', '').strip()
            if name and email:
                UnitHead.objects.update_or_create(
                    unit=unit,
                    defaults={'name': name, 'email': email, 'is_active': True},
                )
            else:
                UnitHead.objects.filter(unit=unit).update(is_active=False)

        if action in ('test', 'send'):
            sent = send_scheduled_reports(schedule, force=True)
            messages.success(request, f'Email report sent to {sent} recipient group(s).')
        else:
            messages.success(request, 'Scheduled email report settings saved.')
        return redirect('settings_communication')

    context = {
        'schedule': schedule,
        'selected_frequencies': selected_frequencies,
        'units': Unit.objects.filter(is_active=True).order_by('code'),
        'unit_heads': UnitHead.objects.select_related('unit').order_by('unit__code'),
        'report_choices': EmailSchedule.REPORT_CHOICES,
        'frequency_choices': EmailSchedule.FREQUENCY_CHOICES,
        'additional_email_list': parse_emails(schedule.additional_emails),
    }
    return render(request, 'admin_panel/settings_email_reports.html', context)

