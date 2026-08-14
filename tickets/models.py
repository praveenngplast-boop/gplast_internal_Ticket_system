from django.db import models
from django.contrib.auth.models import User
import re


class Unit(models.Model):
    code = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        self.full_name = self.full_name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.full_name}"


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


class AdminContact(models.Model):
    admin_name = models.CharField(max_length=100)
    admin_phone = models.CharField(max_length=15)
    admin_email = models.EmailField()

    def __str__(self):
        return f"{self.admin_name} - {self.admin_phone}"


class AdminNotificationEmail(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class EmployeeMaster(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)
    employee_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10)
    email = models.EmailField()
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    can_assign_ticket = models.BooleanField(
        default=False,
        verbose_name="Can Assign Tickets",
        help_text="Enable if this employee can be assigned tickets to other employees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']
        verbose_name = 'Employee Master'
        verbose_name_plural = 'Employee Masters'

    def save(self, *args, **kwargs):
        self.employee_id = self.employee_id.upper()
        self.employee_name = self.employee_name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.employee_name}"


class DepartmentCredential(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['unit__code', 'department__name']
        verbose_name = 'Department Credential'
        verbose_name_plural = 'Department Credentials'
        unique_together = ['unit', 'department']

    def __str__(self):
        return f"{self.unit.code} - {self.department.name} ({self.username})"


def generate_ticket_number():
    """Generate a unique ticket number"""
    from tickets.models import Ticket
    
    last_ticket = Ticket.objects.all().order_by('id').last()
    
    if last_ticket and last_ticket.ticket_number:
        ticket_num = last_ticket.ticket_number
        
        try:
            last_number = int(ticket_num)
            new_number = last_number + 1
        except ValueError:
            try:
                match = re.search(r'(\d{4})$', ticket_num)
                if match:
                    last_number = int(match.group(1))
                    new_number = last_number + 1
                else:
                    new_number = 1
            except (ValueError, AttributeError):
                new_number = 1
    else:
        new_number = 1
    
    return f"{new_number:04d}"


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
    screen_number = models.CharField(max_length=50)
    subject = models.CharField(max_length=150)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    error_type = models.CharField(max_length=50, choices=ERROR_TYPE_CHOICES)
    attachment_1 = models.FileField(upload_to='attachments/', blank=True, null=True)
    attachment_2 = models.FileField(upload_to='attachments/', blank=True, null=True)
    attachment_3 = models.FileField(upload_to='attachments/', blank=True, null=True)
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
    updated_at = models.DateTimeField(auto_now=True)
    
    # ============================================================
    # ✅ NOTIFICATION FIELDS - Bell notification system
    # ============================================================
    is_viewed = models.BooleanField(
        default=False,
        help_text="Admin has viewed this ticket"
    )
    viewed_at = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="When the ticket was first viewed by admin"
    )
    notification_sent = models.BooleanField(
        default=False,
        help_text="Notification email has been sent to admin"
    )

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = generate_ticket_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=255)
    remarks = models.TextField(blank=True, null=True)
    performed_by = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.action} ({self.timestamp})"


# ============================================================
# SETTINGS AUDIT LOG MODEL
# ============================================================

class SettingsAuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('TOGGLE', 'Toggled'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    SETTING_TYPES = [
        ('UNIT', 'Unit'),
        ('DEPARTMENT', 'Department'),
        ('EMPLOYEE', 'Employee'),
        ('CREDENTIAL', 'Credential'),
        ('CONTACT', 'Contact'),
        ('EMAIL', 'Email'),
        ('PASSWORD', 'Password'),
        ('GENERAL', 'General'),
    ]
    
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_by_name = models.CharField(max_length=150)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES)
    setting_name = models.CharField(max_length=200)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    change_summary = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Settings Audit Log'
        verbose_name_plural = 'Settings Audit Logs'
    
    def __str__(self):
        return f"{self.performed_by_name} - {self.action_type} - {self.setting_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"