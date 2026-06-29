from django.db import models
from django.contrib.auth.models import User

# Unit — Admin-managed, ALL CAPS enforced
class Unit(models.Model):
    code = models.CharField(max_length=10, unique=True)       # e.g. IMD
    full_name = models.CharField(max_length=100, unique=True)  # e.g. INJECTION MOULDING
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        self.full_name = self.full_name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.full_name}"

# Department — linked to Unit, ALL CAPS enforced
class Department(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.unit.code})"

# AdminContact — singleton setting
class AdminContact(models.Model):
    admin_name = models.CharField(max_length=100)
    admin_phone = models.CharField(max_length=15)
    admin_email = models.EmailField()

    def __str__(self):
        return f"{self.admin_name} - {self.admin_phone}"

# AdminNotificationEmail — multiple recipients
class AdminNotificationEmail(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

# Ticket
class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ]
    ERROR_TYPE_CHOICES = [
        ('New', 'New'),
        ('Regular', 'Regular'),
        ('No Idea', 'No Idea'),
        ('ERP Error', 'ERP Error'),
        ('Data Entry Error', 'Data Entry Error'),
        ('DB Error', 'DB Error'),
        ('Server Error', 'Server Error'),
        ('IT Error', 'IT Error'),
        ('User Error', 'User Error'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Assigned', 'Assigned'),
        ('Hold', 'Hold'),
        ('Escalated', 'Escalated'),
        ('Closed', 'Closed')
    ]
    CREATED_BY_CHOICES = [
        ('Employee', 'Employee'),
        ('Admin', 'Admin')
    ]
    ADMIN_REASON_CHOICES = [
        ('Phone Call', 'Phone Call'),
        ('Walk-in Support', 'Walk-in Support'),
        ('Manager Request', 'Manager Request'),
        ('Email Forwarded', 'Email Forwarded'),
        ('Other', 'Other')
    ]

    ticket_number = models.CharField(max_length=30, unique=True, editable=False)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    employee_id = models.CharField(max_length=50)
    employee_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10)
    email = models.EmailField()
    screen_number = models.CharField(max_length=50)           # Mandatory
    subject = models.CharField(max_length=150)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    error_type = models.CharField(max_length=50, choices=ERROR_TYPE_CHOICES)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_by_role = models.CharField(max_length=10, choices=CREATED_BY_CHOICES, default='Employee')
    admin_creation_reason = models.CharField(max_length=50, choices=ADMIN_REASON_CHOICES, blank=True, null=True)
    assigned_person = models.CharField(max_length=100, blank=True, null=True)
    hold_reason = models.TextField(blank=True, null=True)
    closing_remarks = models.TextField(blank=True, null=True)
    closed_by = models.CharField(max_length=100, blank=True, null=True)
    vendor_ticket_number = models.CharField(max_length=100, blank=True, null=True)
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    escalated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

# TicketHistory
class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=255)
    remarks = models.TextField(blank=True, null=True)
    performed_by = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.action} ({self.timestamp})"
