import time
import logging

from django.core.management import BaseCommand, call_command


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Continuously check and send scheduled ticket reports for local development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Seconds between schedule checks (default: 30).',
        )

    def handle(self, *args, **options):
        interval = max(10, options['interval'])
        self.stdout.write(self.style.SUCCESS(
            f'Email scheduler started; checking every {interval} seconds.'
        ))
        try:
            while True:
                try:
                    call_command('send_emails')
                except Exception:
                    logger.exception('Email scheduler check failed; retrying on the next interval.')
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Email scheduler stopped.'))