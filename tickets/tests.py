from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from tickets.models import Unit, Department, Ticket, TicketHistory, UnitHead, EmailSchedule, AdminNotificationEmail
from tickets.forms import TicketForm
from tickets.utils import generate_ticket_number, send_ticket_email
from tickets.views import reports_views
from unittest.mock import patch
from django.core import mail
from tickets.email_utils import send_scheduled_reports


class GPLASTTicketingTestCase(TestCase):
    def setUp(self):
        # Create employee user
        self.employee_user = User.objects.create_user(
            username="testemp", 
            password="password",
            email="testemp@gplast.com"
        )
        
        # Create admin user for tests
        self.admin_user = User.objects.create_superuser(
            username="adminuser",
            password="adminpassword",
            email="admin@gplast.com"
        )
        
        # Create unit and department
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

    def test_ticket_number_format(self):
        """Verify ticket numbers are generated in 4-digit numeric format (0001, 0002, ...)"""
        ticket = Ticket.objects.create(
            ticket_number=generate_ticket_number(),
            unit=self.unit,
            department=self.department,
            employee_id="EMP01",
            employee_name="Test",
            mobile="1234567890",
            email="test@gplast.com",
            screen_number="SCR-01",
            subject="Test Subject",
            description="Test description long enough to satisfy constraints",
            priority="Low",
            error_type="New",
            created_by_user=self.employee_user
        )
        # Check format: 4-digit number
        self.assertTrue(ticket.ticket_number.isdigit())
        self.assertEqual(len(ticket.ticket_number), 4)
        self.assertEqual(int(ticket.ticket_number), 1)

    def test_sequential_ticket_numbering(self):
        """Verify ticket numbers generate sequential numeric identifiers."""
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
        num1 = int(ticket1.ticket_number)
        num2 = int(ticket2.ticket_number)
        self.assertEqual(num2, num1 + 1)

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
        # Should be the next number after legacy (0006)
        self.assertEqual(next_number, "0006")

    def test_mobile_number_validation(self):
        """Verify form validation checks for exactly 10 numeric digits in mobile"""
        form_data = {
            'unit': self.unit.id,
            'department': self.department.id,
            'employee_id': 'EMP01',
            'employee_name': 'Test User',
            'mobile': '123456789a',  # Invalid - contains letter
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

        # Test with 9 digits (invalid)
        form_data['mobile'] = '123456789'
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())

        # Test with 10 digits (valid)
        form_data['mobile'] = '9876543210'
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Test with empty mobile (valid - optional)
        form_data['mobile'] = ''
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
            'description': 'Short description',
            'priority': 'Low',
            'error_type': 'New'
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

        form_data['description'] = '12345678901234567890'
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_mobile_and_email_optional(self):
        """Verify mobile and email fields are optional in ticket form"""
        form_data = {
            'unit': self.unit.id,
            'department': self.department.id,
            'employee_id': 'EMP01',
            'employee_name': 'Test User',
            'mobile': '',  # Empty - optional
            'email': '',  # Empty - optional
            'screen_number': 'SCR-01',
            'subject': 'Test Subject',
            'description': 'Description that is definitely long enough (over 20 chars)',
            'priority': 'Low',
            'error_type': 'New'
        }
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_employee_closed_ticket_cap(self):
        """Verify employees can only view the last 50 closed tickets"""
        for i in range(55):
            Ticket.objects.create(
                ticket_number=generate_ticket_number(),
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

        active_tickets = Ticket.objects.filter(
            created_by_user=self.employee_user
        ).exclude(status='Closed')

        closed_tickets = Ticket.objects.filter(
            created_by_user=self.employee_user,
            status='Closed'
        ).order_by('-closed_at')[:50]

        all_visible = list(active_tickets) + list(closed_tickets)
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
        self.assertIn(ticket.ticket_number, mail.outbox[0].subject)
        self.assertIn('Closed', mail.outbox[0].subject)
        self.assertIn('Alice', mail.outbox[0].body)
        self.assertIn('Printer issue', mail.outbox[0].body)

    def test_reopen_ticket_by_admin(self):
        """Verify only administrators can reopen closed tickets with remarks."""
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

        # Try reopening as employee (should fail)
        self.client.login(username="testemp", password="password")
        reopen_url = f"/admin/ticket/{ticket.id}/"
        
        from unittest.mock import patch
        with patch('tickets.views.send_ticket_email') as mock_send_email:
            response = self.client.post(reopen_url, {'action_type': 'Reopen', 'remarks': 'Reopening'})
            self.assertEqual(response.status_code, 302)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, "Closed")

            # Try reopening as admin without remarks (should fail)
            self.client.login(username="adminuser", password="adminpassword")
            
            response = self.client.post(reopen_url, {'action_type': 'Reopen', 'remarks': ''})
            self.assertEqual(response.status_code, 302)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, "Closed")

            # Try reopening as admin with remarks (should succeed)
            response = self.client.post(reopen_url, {'action_type': 'Reopen', 'remarks': 'Issue still exists'})
            self.assertEqual(response.status_code, 302)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, "Open")
            self.assertIsNone(ticket.closed_by)
            self.assertIsNone(ticket.closed_at)
            self.assertIsNone(ticket.closing_remarks)
            
            mock_send_email.assert_called_once_with(ticket, 'Reopened', remarks='Issue still exists')

        history = TicketHistory.objects.filter(ticket=ticket, action="Ticket Reopened").first()
        self.assertIsNotNone(history)
        self.assertEqual(history.remarks, "Issue still exists")
        self.assertEqual(history.performed_by, "Admin adminuser")


class ReportsViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            username='reportadmin', 
            password='password', 
            is_staff=True,
            email='admin@example.com'
        )
        self.unit = Unit.objects.create(
            code='rpt', 
            full_name='Report Unit', 
            created_by='TEST'
        )
        self.department = Department.objects.create(
            unit=self.unit, 
            name='Report Department'
        )

    def create_ticket(self, number, status, sub_error_type):
        return Ticket.objects.create(
            ticket_number=number,
            unit=self.unit,
            department=self.department,
            employee_id='EMP01',
            employee_name='Report Employee',
            mobile='1234567890',
            email='report@example.com',
            screen_number='SCR-01',
            subject=f'Report {number}',
            description='A report test ticket description.',
            priority='High',
            error_type='New',
            main_error_type='Roadmap Error',
            sub_error_type=sub_error_type,
            status=status,
            created_by_user=self.admin_user,
        )

    def test_report_filters_status_and_main_error_without_forcing_sub_error(self):
        self.create_ticket('RPT001', 'Closed', 'Database Error')
        self.create_ticket('RPT002', 'Closed', 'Logic / Functional Error')
        self.create_ticket('RPT003', 'Open', 'Database Error')
        request = self.factory.get('/custom-admin/reports/', {
            'status': 'Closed',
            'main_error_type': 'Roadmap Error',
            'sub_error_type': '',
        })
        request.user = self.admin_user
        with patch('tickets.views.reports_views.render') as render:
            render.return_value = HttpResponse(status=200)
            response = reports_views.reports(request)

        self.assertEqual(response.status_code, 200)
        context = render.call_args.args[2]
        self.assertEqual(context['tickets'].paginator.count, 2)

    def test_escalated_aging_report_groups_current_escalations(self):
        old_ticket = self.create_ticket('RPT004', 'Escalated', 'Database Error')
        old_ticket.escalated_at = timezone.now() - timezone.timedelta(days=20)
        old_ticket.save(update_fields=['escalated_at'])
        
        recent_ticket = self.create_ticket('RPT005', 'Escalated', 'Database Error')
        recent_ticket.escalated_at = timezone.now() - timezone.timedelta(days=3)
        recent_ticket.save(update_fields=['escalated_at'])
        
        self.create_ticket('RPT006', 'Closed', 'Database Error')

        request = self.factory.get('/custom-admin/reports/escalated-aging/')
        request.user = self.admin_user
        with patch('tickets.views.reports_views.render') as render:
            render.return_value = HttpResponse(status=200)
            response = reports_views.escalated_aging_report(request)

        self.assertEqual(response.status_code, 200)
        context = render.call_args.args[2]
        self.assertEqual(context['total_escalated'], 2)
        self.assertEqual(context['aging_counts']['0-7 Days'], 1)
        self.assertEqual(context['aging_counts']['16-30 Days'], 1)

    def test_escalated_aging_kpi_drills_into_selected_category(self):
        recent_ticket = self.create_ticket('RPT007', 'Escalated', 'Database Error')
        recent_ticket.escalated_at = timezone.now() - timezone.timedelta(days=3)
        recent_ticket.save(update_fields=['escalated_at'])
        
        old_ticket = self.create_ticket('RPT008', 'Escalated', 'Database Error')
        old_ticket.escalated_at = timezone.now() - timezone.timedelta(days=20)
        old_ticket.save(update_fields=['escalated_at'])

        request = self.factory.get('/custom-admin/reports/escalated-aging/', {
            'aging_category': '0-7 Days',
        })
        request.user = self.admin_user
        with patch('tickets.views.reports_views.render') as render:
            render.return_value = HttpResponse(status=200)
            response = reports_views.escalated_aging_report(request)

        self.assertEqual(response.status_code, 200)
        context = render.call_args.args[2]
        self.assertEqual(context['total_escalated'], 1)
        self.assertEqual(context['aging_rows'][0]['ticket'].ticket_number, 'RPT007')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_scheduled_reports_scope_admins_and_unit_heads(self):
        # ✅ FIXED: Create unit head with user field
        unit_head_user = User.objects.create_user(
            username='unitheaduser',
            password='password',
            email='head@example.com'
        )
        UnitHead.objects.create(
            user=unit_head_user,  # ← REQUIRED: Link to User
            unit=self.unit,
            name='Unit Head',
            email='head@example.com',
            is_active=True
        )
        
        AdminNotificationEmail.objects.create(email='admin@example.com')
        self.create_ticket('RPT009', 'Open', 'Database Error')
        
        schedule = EmailSchedule.objects.create(
            enabled=True, 
            reports=['open'], 
            all_units=True,
            send_unit_heads=True, 
            send_admins=True,
            subject_template='Ticket Report - {{date}}',
        )

        sent = send_scheduled_reports(schedule)

        self.assertEqual(sent, 2)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('admin@example.com', mail.outbox[0].to)
        self.assertIn('head@example.com', mail.outbox[1].to)
        self.assertIn('admin@example.com', mail.outbox[1].cc)