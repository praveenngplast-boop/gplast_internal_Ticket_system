from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tickets.models import Unit, Department, AdminContact, AdminNotificationEmail, Ticket, TicketHistory

class Command(BaseCommand):
    help = "Seeds database with default GPLAST users, units, and departments"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # 1. Create Default Users
        admin_user, created = User.objects.get_or_create(username="GPLERPADMIN")
        if created:
            admin_user.set_password("GPLADMIN")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.email = "admin@gplast.com"
            admin_user.save()
            self.stdout.write("Created Admin user: GPLERPADMIN / GPLADMIN")
        else:
            self.stdout.write("Admin user already exists")

        emp_user, created = User.objects.get_or_create(username="GPLERPUSERS")
        if created:
            emp_user.set_password("GPLUSER")
            emp_user.is_staff = False
            emp_user.is_superuser = False
            emp_user.email = "employee@gplast.com"
            emp_user.save()
            self.stdout.write("Created Employee user: GPLERPUSERS / GPLUSER")
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

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
