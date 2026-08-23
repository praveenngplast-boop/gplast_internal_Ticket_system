from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from zoneinfo import ZoneInfo

from tickets.email_utils import send_scheduled_reports
from tickets.models import EmailSchedule


class Command(BaseCommand):
    help = 'Send scheduled ticket reports when the configured Chennai-time schedule is due.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Send immediately even if disabled or not due.')

    def handle(self, *args, **options):
        schedule = EmailSchedule.objects.filter(id=1).first()
        if not schedule:
            self.stdout.write('No scheduled email report configuration found.')
            return
        if not schedule.enabled and not options['force']:
            self.stdout.write('Scheduled email reports are disabled.')
            return

        schedule_timezone = ZoneInfo(getattr(settings, 'TIME_ZONE', 'Asia/Kolkata'))
        now = timezone.localtime(timezone.now(), schedule_timezone)
        last_sent_local_date = (
            timezone.localtime(schedule.last_sent_at, schedule_timezone).date()
            if schedule.last_sent_at else None
        )
        frequencies = schedule.frequency if isinstance(schedule.frequency, list) else [schedule.frequency]
        frequency_due = (
            'daily' in frequencies or
            ('weekly' in frequencies and now.weekday() == 0) or
            ('monthly' in frequencies and now.day == 1)
        )
        due = options['force'] or (
            now.time() >= schedule.send_time and
            (last_sent_local_date is None or last_sent_local_date < now.date()) and
            frequency_due
        )
        if not due:
            self.stdout.write('Scheduled email reports are not due.')
            return

        sent = send_scheduled_reports(schedule, force=True)
        if sent:
            schedule.last_sent_at = timezone.now()
            schedule.save(update_fields=['last_sent_at', 'updated_at'])
        else:
            self.stdout.write(self.style.WARNING('No scheduled report emails were sent; will retry when checked again.'))
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} scheduled report email group(s).'))
