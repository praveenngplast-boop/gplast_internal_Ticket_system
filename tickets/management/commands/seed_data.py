from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tickets.models import Unit, Department, AdminContact, AdminNotificationEmail, Ticket, TicketHistory
from tickets.utils import generate_ticket_number
import random

class Command(BaseCommand):
    help = "Seeds database with default GPLAST configuration and sample data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # 1. Create Default Users
        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.set_password("Admin@1234")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.email = "admin@gplast.com"
            admin_user.save()
            self.stdout.write("Created Admin user: admin / Admin@1234")
        else:
            self.stdout.write("Admin user already exists")

        emp_user, created = User.objects.get_or_create(username="employee")
        if created:
            emp_user.set_password("Emp@1234")
            emp_user.is_staff = False
            emp_user.is_superuser = False
            emp_user.email = "employee@gplast.com"
            emp_user.save()
            self.stdout.write("Created Employee user: employee / Emp@1234")
        else:
            self.stdout.write("Employee user already exists")

        # 2. Seed default Units
        default_units = [
            ("IMD", "INJECTION MOULDING"),
            ("DCD", "DIE CASTING"),
            ("TRD", "TOOL ROOM"),
            ("HO", "HEAD OFFICE"),
        ]
        
        unit_objs = {}
        for code, full_name in default_units:
            unit, u_created = Unit.objects.get_or_create(
                code=code,
                defaults={"full_name": full_name, "is_active": True, "created_by": "SYSTEM"}
            )
            unit_objs[code] = unit
            if u_created:
                self.stdout.write(f"Seeded Unit: {code} -> {full_name}")

        # 3. Seed default Departments per Unit
        dept_data = {
            "IMD": ["PRODUCTION", "MAINTENANCE", "QUALITY CONTROL"],
            "DCD": ["PRODUCTION", "DIE MAINTENANCE", "QUALITY CONTROL"],
            "TRD": ["TOOL DESIGN", "MACHINING", "ASSEMBLY"],
            "HO": ["FINANCE", "HUMAN RESOURCES", "IT SUPPORT", "SALES"],
        }

        for code, depts in dept_data.items():
            unit = unit_objs[code]
            for dept_name in depts:
                dept, d_created = Department.objects.get_or_create(
                    unit=unit,
                    name=dept_name,
                    defaults={"is_active": True}
                )
                if d_created:
                    self.stdout.write(f"Seeded Department: {dept_name} under {code}")

        # 4. Seed AdminContact
        contact, c_created = AdminContact.objects.get_or_create(
            id=1,
            defaults={
                "admin_name": "SURESH KUMAR (IT HEAD)",
                "admin_phone": "9876543210",
                "admin_email": "suresh.kumar@gplast.com"
            }
        )
        if c_created:
            self.stdout.write("Seeded IT Support Contact card details")

        # 5. Seed AdminNotificationEmail
        notif_email, n_created = AdminNotificationEmail.objects.get_or_create(
            email="it.alerts@gplast.com",
            defaults={"is_active": True}
        )
        if n_created:
            self.stdout.write("Seeded default admin notification email")

        # 6. Seed 10 sample tickets with history
        if Ticket.objects.count() == 0:
            self.stdout.write("Seeding 10 sample tickets...")
            
            # Helper to create a ticket and its initial history
            # Sample data
            tickets_samples = [
                {
                    "employee_id": "EMP001",
                    "employee_name": "Ramesh Babu",
                    "mobile": "9876543210",
                    "email": "employee@gplast.com",
                    "screen_number": "SCR-101 (Moulding Entry)",
                    "subject": "ERP Injection Moulding screen loading error",
                    "description": "The Injection Moulding production entry screen shows a loading spinner forever when attempting to submit raw material batch details.",
                    "priority": "High",
                    "error_type": "Regular",
                    "status": "Open",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "unit": "IMD",
                    "dept": "PRODUCTION",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee")
                    ]
                },
                {
                    "employee_id": "EMP002",
                    "employee_name": "Vikram Singh",
                    "mobile": "9876543211",
                    "email": "vikram@gplast.com",
                    "screen_number": "SCR-204 (Quality Testing)",
                    "subject": "Quality approval button is disabled",
                    "description": "After entering the inspection dimension details, the approve button is grayed out, preventing confirmation of casting batch B-55.",
                    "priority": "Critical",
                    "error_type": "New",
                    "status": "Assigned",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "assigned_person": "Rahul Sen",
                    "unit": "DCD",
                    "dept": "QUALITY CONTROL",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee"),
                        ("Assigned to Rahul Sen", "Ticket assigned to Rahul Sen", "Admin")
                    ]
                },
                {
                    "employee_id": "EMP003",
                    "employee_name": "Sneha Roy",
                    "mobile": "9876543212",
                    "email": "sneha@gplast.com",
                    "screen_number": "SCR-305 (Tool Design)",
                    "subject": "CAD file upload failed on Tool Room module",
                    "description": "Attempting to upload a 2.5MB DXF format tool plan throws an unhandled database unique constraint error.",
                    "priority": "Medium",
                    "error_type": "No Idea",
                    "status": "Hold",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "assigned_person": "Praveen Nair",
                    "hold_reason": "Waiting for developer analysis",
                    "unit": "TRD",
                    "dept": "TOOL DESIGN",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee"),
                        ("Assigned to Praveen Nair", "Ticket assigned to Praveen Nair", "Admin"),
                        ("Status changed to Hold — Reason: Waiting for developer analysis", "Hold details added", "Admin")
                    ]
                },
                {
                    "employee_id": "EMP004",
                    "employee_name": "Arjun Das",
                    "mobile": "9876543213",
                    "email": "arjun@gplast.com",
                    "screen_number": "SCR-402 (Salary slip)",
                    "subject": "Unable to download salary slip for May 2026",
                    "description": "The HR portal throws a PDF generation timeout error when I click the salary slip download button.",
                    "priority": "Low",
                    "error_type": "Regular",
                    "status": "Closed",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "closing_remarks": "Resolved. Reconfigured the PDF generator buffer size on the HR app server.",
                    "closed_by": "SURESH KUMAR (IT HEAD)",
                    "closed_at": timezone.now(),
                    "unit": "HO",
                    "dept": "HUMAN RESOURCES",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee"),
                        ("Closed by Suresh Kumar — Issue resolved", "Closed", "Admin")
                    ]
                },
                {
                    "employee_id": "EMP005",
                    "employee_name": "Rajesh Kannan",
                    "mobile": "9876543214",
                    "email": "rajesh@gplast.com",
                    "screen_number": "SCR-110 (Moulding Maintenance)",
                    "subject": "Preventive Maintenance schedule lock",
                    "description": "System does not allow updating PM logs for Injection Moulding Machine #3, stating it is locked by another transaction.",
                    "priority": "High",
                    "error_type": "New",
                    "status": "Escalated",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "vendor_ticket_number": "VND-ERP-2026-904",
                    "escalated_at": timezone.now(),
                    "unit": "IMD",
                    "dept": "MAINTENANCE",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee"),
                        ("Assigned to Praveen Nair", "Ticket assigned to Praveen Nair", "Admin"),
                        ("Escalated to ERP Vendor", "Escalated to vendor - Ticket VND-ERP-2026-904", "Admin")
                    ]
                },
                {
                    "employee_id": "EMP006",
                    "employee_name": "Maria Fernandes",
                    "mobile": "9876543215",
                    "email": "maria@gplast.com",
                    "screen_number": "SCR-412 (Sales Invoicing)",
                    "subject": "Tax calculation error on GST invoices",
                    "description": "The system computes 12% IGST instead of 18% IGST for state tax calculations on tool orders.",
                    "priority": "Critical",
                    "error_type": "Regular",
                    "status": "Closed",
                    "created_by_role": "Admin",
                    "created_by_user": admin_user,
                    "admin_creation_reason": "Walk-in Support",
                    "closing_remarks": "Fixed GST master tax code mapping for the tool category.",
                    "closed_by": "SURESH KUMAR (IT HEAD)",
                    "closed_at": timezone.now(),
                    "unit": "HO",
                    "dept": "SALES",
                    "history": [
                        ("Ticket Created", "Ticket created by Admin on behalf of employee (Walk-in Support)", "Admin"),
                        ("Closed by Suresh Kumar — Issue resolved", "Closed", "Admin")
                    ]
                },
                {
                    "employee_id": "EMP007",
                    "employee_name": "Sunil Varma",
                    "mobile": "9876543216",
                    "email": "sunil@gplast.com",
                    "screen_number": "SCR-311 (Machining CNC)",
                    "subject": "CNC program transfer file format issue",
                    "description": "ERP toolroom screen fails to parse uploaded G-code files, reporting invalid character encoding.",
                    "priority": "Medium",
                    "error_type": "No Idea",
                    "status": "Open",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "unit": "TRD",
                    "dept": "MACHINING",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee")
                    ]
                },
                {
                    "employee_id": "EMP008",
                    "employee_name": "Siddharth Malhotra",
                    "mobile": "9876543217",
                    "email": "sid@gplast.com",
                    "screen_number": "SCR-401 (Voucher Entry)",
                    "subject": "Petty cash entry ledger mismatch",
                    "description": "Debiting petty cash ledger does not reflect in the corresponding branch trial balance screen.",
                    "priority": "High",
                    "error_type": "Regular",
                    "status": "Closed",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "closing_remarks": "Ledger reconciliation completed. Glitch cleared.",
                    "closed_by": "SURESH KUMAR (IT HEAD)",
                    "closed_at": timezone.now(),
                    "unit": "HO",
                    "dept": "FINANCE",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee"),
                        ("Closed by Suresh Kumar — Ledger synced", "Closed", "Admin")
                    ]
                },
                {
                    "employee_id": "EMP009",
                    "employee_name": "Deepa Mehta",
                    "mobile": "9876543218",
                    "email": "deepa@gplast.com",
                    "screen_number": "SCR-201 (Die Casting Entry)",
                    "subject": "ERP system hanging during machine output logs",
                    "description": "Submitting hourly production output logs on Machine DC-05 takes more than 2 minutes and frequently yields a Gateway Timeout error.",
                    "priority": "Critical",
                    "error_type": "Regular",
                    "status": "Open",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "unit": "DCD",
                    "dept": "PRODUCTION",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee")
                    ]
                },
                {
                    "employee_id": "EMP010",
                    "employee_name": "Karan Johar",
                    "mobile": "9876543219",
                    "email": "karan@gplast.com",
                    "screen_number": "SCR-320 (Assembly Check)",
                    "subject": "Serial number tracking failure on mold components",
                    "description": "Unable to scan barcode for tool assembly components. The scanner outputs standard characters, but ERP reports invalid scanner sequence format.",
                    "priority": "Medium",
                    "error_type": "No Idea",
                    "status": "Assigned",
                    "created_by_role": "Employee",
                    "created_by_user": emp_user,
                    "assigned_person": "Rahul Sen",
                    "unit": "TRD",
                    "dept": "ASSEMBLY",
                    "history": [
                        ("Ticket Created", "Ticket Created by Employee", "Employee"),
                        ("Assigned to Rahul Sen", "Ticket assigned to Rahul Sen", "Admin")
                    ]
                }
            ]

            for s in tickets_samples:
                unit_obj = Unit.objects.get(code=s["unit"])
                dept_obj = Department.objects.get(unit=unit_obj, name=s["dept"])
                
                # Create ticket
                # Manually generate numbers to ensure consistent seed sequencing
                date_str = timezone.now().astimezone(timezone.get_current_timezone()).strftime('%Y%m%d')
                seq = Ticket.objects.filter(ticket_number__startswith=f"GPLAST-{date_str}").count() + 1
                t_num = f"GPLAST-{date_str}-{seq:04d}"
                
                ticket = Ticket.objects.create(
                    ticket_number=t_num,
                    unit=unit_obj,
                    department=dept_obj,
                    employee_id=s["employee_id"],
                    employee_name=s["employee_name"],
                    mobile=s["mobile"],
                    email=s["email"],
                    screen_number=s["screen_number"],
                    subject=s["subject"],
                    description=s["description"],
                    priority=s["priority"],
                    error_type=s["error_type"],
                    status=s["status"],
                    created_by_role=s["created_by_role"],
                    admin_creation_reason=s.get("admin_creation_reason"),
                    assigned_person=s.get("assigned_person"),
                    hold_reason=s.get("hold_reason"),
                    closing_remarks=s.get("closing_remarks"),
                    closed_by=s.get("closed_by"),
                    closed_at=s.get("closed_at"),
                    vendor_ticket_number=s.get("vendor_ticket_number"),
                    escalated_at=s.get("escalated_at"),
                    created_by_user=s["created_by_user"],
                )
                
                # Create history entries
                for action_val, remarks_val, perf in s["history"]:
                    TicketHistory.objects.create(
                        ticket=ticket,
                        action=action_val,
                        remarks=remarks_val,
                        performed_by=perf
                    )
            
            self.stdout.write("Successfully seeded 10 sample tickets with complete audit logs.")
        else:
            self.stdout.write("Tickets already exist in the database, skipping ticket seed.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
