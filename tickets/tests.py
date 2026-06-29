from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from tickets.models import Unit, Department, Ticket, TicketHistory
from tickets.forms import TicketForm
from tickets.utils import generate_ticket_number

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
        """Verify ticket numbers generate sequentially per day"""
        date_str = timezone.now().astimezone(timezone.get_current_timezone()).strftime('%Y%m%d')
        
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
        self.assertEqual(ticket1.ticket_number, f"GPLAST-{date_str}-0001")

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
        self.assertEqual(ticket2.ticket_number, f"GPLAST-{date_str}-0002")

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
