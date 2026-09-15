"""
Auto-archive closed tickets older than N days.

Usage:
    python manage.py archive_old_tickets
    python manage.py archive_old_tickets --days 180
    python manage.py archive_old_tickets --days 90 --dry-run
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Ticket, TicketHistory


class Command(BaseCommand):
    help = "Auto-archive closed tickets older than N days."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=90,
            help='Archive tickets closed more than N days ago (default: 90)'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be archived without changing anything'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)

        qs = Ticket.objects.with_archived().filter(
            status='Closed',
            is_archived=False,
            closed_at__lt=cutoff,
        )

        count = qs.count()

        if count == 0:
            self.stdout.write(
                f"No tickets to archive (closed more than {days} days ago)."
            )
            return

        verb = "Would archive" if dry else "Archiving"
        self.stdout.write(
            f"{verb} {count} ticket(s) closed before {cutoff:%Y-%m-%d %H:%M}."
        )

        if dry:
            for t in qs.order_by('-closed_at')[:30]:
                self.stdout.write(
                    f"  #{t.ticket_number}  "
                    f"{t.closed_at:%Y-%m-%d}  "
                    f"{t.subject[:60]}"
                )
            return

        now = timezone.now()
        archived = 0
        for ticket in qs:
            ticket.is_archived = True
            ticket.archived_at = now
            ticket.archived_by = "System (auto)"
            ticket.save(update_fields=["is_archived", "archived_at", "archived_by"])

            TicketHistory.objects.create(
                ticket=ticket,
                action="Archived Ticket",
                remarks=f"Auto-archived (closed more than {days} days ago)",
                performed_by="System",
            )
            archived += 1

        self.stdout.write(self.style.SUCCESS(f"Archived {archived} ticket(s)."))