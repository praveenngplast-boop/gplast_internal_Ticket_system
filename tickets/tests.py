from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from tickets.models import Unit, Department, Ticket, TicketHistory
from tickets.forms import TicketForm
from tickets.utils import generate_ticket_number, send_ticket_email

class GPLASTTicketingTestCase(TestCase):
    def setUp(self):
        # Create users
        self.employee_user = User.objects.create_user(username="testemp", password="password")
        
        # Create active unit & department
        self.unit = Unit.objects.create(
            code="imd",
            full_name="injection moulding",
            is_active=True,
            created_by="TEST"
        )
        self.department = Department.objects.create(
            unit=self.unit,
            name="production",
            is_active=True
        )

    def test_capitalization_enforcement(self):
        """Verify unit codes/names and department names are saved in UPPERCASE"""
        self.assertEqual(self.unit.code, "IMD")
        self.assertEqual(self.unit.full_name, "INJECTION MOULDING")
        self.assertEqual(self.department.name, "PRODUCTION")

    def test_sequential_ticket_numbering(self):
        """Verify ticket numbers generate sequential numeric identifiers."""

        # Create first ticket
        ticket1 = Ticket.objects.create(
            ticket_number=generate_ticket_number(),
            unit=self.unit,
            department=self.department,
            employee_id="EMP01",
            employee_name="Test",
            mobile="1234567890",
            email="test@gplast.com",
            screen_number="SCR-01",
            subject="Test Subject 1",
            description="Test description long enough to satisfy constraints",
            priority="Low",
            error_type="New",
            created_by_user=self.employee_user
        )
        self.assertEqual(ticket1.ticket_number, "0001")

        # Create second ticket
        ticket2 = Ticket.objects.create(
            ticket_number=generate_ticket_number(),
            unit=self.unit,
            department=self.department,
            employee_id="EMP01",
            employee_name="Test",
            mobile="1234567890",
            email="test@gplast.com",
            screen_number="SCR-01",
            subject="Test Subject 2",
            description="Test description long enough to satisfy constraints",
            priority="Low",
            error_type="New",
            created_by_user=self.employee_user
        )
        self.assertEqual(ticket2.ticket_number, "0002")

    def test_generate_ticket_number_continues_after_old_prefix_format(self):
        """Verify new numeric tickets continue after legacy prefixed ticket numbers."""
        Ticket.objects.create(
            ticket_number="GPLAST-20260628-0005",
            unit=self.unit,
            department=self.department,
            employee_id="EMP01",
            employee_name="Test",
            mobile="1234567890",
            email="test@gplast.com",
            screen_number="SCR-01",
            subject="Legacy Ticket",
            description="Legacy format description.",
            priority="Low",
            error_type="New",
            created_by_user=self.employee_user
        )

        next_number = generate_ticket_number()
        self.assertEqual(next_number, "0006")

    def test_mobile_number_validation(self):
        """Verify form validation checks for exactly 10 numeric digits in mobile"""
        # Non-digits
        form_data = {
            'unit': self.unit.id,
            'department': self.department.id,
            'employee_id': 'EMP01',
            'employee_name': 'Test User',
            'mobile': '123456789a',  # alphanumeric
            'email': 'test@gplast.com',
            'screen_number': 'SCR-01',
            'subject': 'Short subject',
            'description': 'Description that is definitely long enough (over 20 chars)',
            'priority': 'Low',
            'error_type': 'New'
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mobile', form.errors)

        # Less than 10 digits
        form_data['mobile'] = '123456789'
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())

        # Correct 10 digits
        form_data['mobile'] = '9876543210'
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_description_length_validation(self):
        """Verify description has a minimum requirement of 20 characters"""
        form_data = {
            'unit': self.unit.id,
            'department': self.department.id,
            'employee_id': 'EMP01',
            'employee_name': 'Test User',
            'mobile': '9876543210',
            'email': 'test@gplast.com',
            'screen_number': 'SCR-01',
            'subject': 'Short subject',
            'description': 'Short description',  # 17 chars
            'priority': 'Low',
            'error_type': 'New'
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

        # Exactly 20 chars
        form_data['description'] = '12345678901234567890'
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_employee_closed_ticket_cap(self):
        """Verify employees can only view the last 50 closed tickets"""
        # Create 55 closed tickets
        for i in range(55):
            Ticket.objects.create(
                ticket_number=f"GPLAST-20260628-{i:04d}",
                unit=self.unit,
                department=self.department,
                employee_id="EMP01",
                employee_name="Test",
                mobile="1234567890",
                email="test@gplast.com",
                screen_number="SCR-01",
                subject=f"Closed issue {i}",
                description="Closed description long enough to satisfy constraints",
                priority="Low",
                error_type="New",
                status="Closed",
                created_by_user=self.employee_user,
                closed_at=timezone.now() - timezone.timedelta(minutes=i)
            )

        # Simulate employee queryset
        active_tickets = Ticket.objects.filter(
            created_by_user=self.employee_user
        ).exclude(status='Closed')

        closed_tickets = Ticket.objects.filter(
            created_by_user=self.employee_user,
            status='Closed'
        ).order_by('-closed_at')[:50]

        all_visible = list(active_tickets) + list(closed_tickets)

        # Count visible closed tickets
        visible_closed = [t for t in all_visible if t.status == 'Closed']
        self.assertEqual(len(visible_closed), 50)

    def test_send_ticket_email_uses_html_template(self):
        """Verify ticket emails render the HTML notification template with ticket details."""
        ticket = Ticket.objects.create(
            ticket_number=generate_ticket_number(),
            unit=self.unit,
            department=self.department,
            employee_id="EMP01",
            employee_name="Alice",
            mobile="9876543210",
            email="alice@gplast.com",
            screen_number="SCR-02",
            subject="Printer issue",
            description="Printer is not working at the workstation.",
            priority="High",
            error_type="New",
            created_by_user=self.employee_user
        )

        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            send_ticket_email(ticket, 'Closed', remarks='Issue resolved.')

        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('ERP Ticket Closed', mail.outbox[0].subject)
        self.assertIn('Alice', mail.outbox[0].body)
        self.assertIn('Printer issue', mail.outbox[0].body)

    def test_reopen_ticket_by_admin(self):
        """Verify only administrators can reopen closed tickets with remarks."""
        # Create admin user
        admin_user = User.objects.create_superuser(username="adminuser", password="adminpassword", email="admin@gplast.com")
        
        # Create a closed ticket
        ticket = Ticket.objects.create(
            ticket_number=generate_ticket_number(),
            unit=self.unit,
            department=self.department,
            employee_id="EMP01",
            employee_name="Alice",
            mobile="9876543210",
            email="alice@gplast.com",
            screen_number="SCR-02",
            subject="Printer issue",
            description="Printer is not working at the workstation.",
            priority="High",
            error_type="New",
            status="Closed",
            closed_by="adminuser",
            closed_at=timezone.now(),
            closing_remarks="Closed resolution notes",
            created_by_user=self.employee_user
        )

        # Login as non-admin employee and try to reopen (should fail permission check)
        self.client.login(username="testemp", password="password")
        reopen_url = f"/admin/ticket/{ticket.id}/"
        
        from unittest.mock import patch
        with patch('tickets.views.send_ticket_email') as mock_send_email:
            response = self.client.post(reopen_url, {'action_type': 'Reopen', 'remarks': 'Reopening'})
            self.assertEqual(response.status_code, 302)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, "Closed") # Still closed

            # Login as admin and reopen
            self.client.login(username="adminuser", password="adminpassword")
            
            # Test validation: remarks are mandatory
            response = self.client.post(reopen_url, {'action_type': 'Reopen', 'remarks': ''})
            self.assertEqual(response.status_code, 302)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, "Closed") # Still closed

            # Successful reopen
            response = self.client.post(reopen_url, {'action_type': 'Reopen', 'remarks': 'Issue still exists'})
            self.assertEqual(response.status_code, 302)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, "Open")
            self.assertIsNone(ticket.closed_by)
            self.assertIsNone(ticket.closed_at)
            self.assertIsNone(ticket.closing_remarks)
            
            # Verify email was attempted
            mock_send_email.assert_called_once_with(ticket, 'Reopened', remarks='Issue still exists')

        # Verify TicketHistory contains the reopen action
        history = TicketHistory.objects.filter(ticket=ticket, action="Ticket Reopened").first()
        self.assertIsNotNone(history)
        self.assertEqual(history.remarks, "Issue still exists")
        self.assertEqual(history.performed_by, "Admin adminuser")
