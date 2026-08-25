from django.db import models
from django.db.models import Q
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


class UnitHead(models.Model):
    unit = models.OneToOneField(Unit, on_delete=models.CASCADE, related_name='head')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.unit.code})"


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


class EmailSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    REPORT_CHOICES = [
        ('open', 'Open Tickets'),
        ('escalated', 'Escalated Tickets'),
        ('escalated_aging', 'Escalated Aging'),
        ('hold', 'Hold Tickets'),
        ('assigned', 'Assigned Tickets'),
    ]

    enabled = models.BooleanField(default=False)
    reports = models.JSONField(default=list)
    frequency = models.JSONField(default=list)
    send_time = models.TimeField(default='08:00')
    send_unit_heads = models.BooleanField(default=True)
    send_admins = models.BooleanField(default=True)
    additional_emails = models.TextField(blank=True, default='')
    all_units = models.BooleanField(default=True)
    units = models.ManyToManyField(Unit, blank=True, related_name='email_schedules')
    subject_template = models.CharField(max_length=255, default='Ticket Report - {{date}}')
    updated_at = models.DateTimeField(auto_now=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return 'Scheduled Email Reports'


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
    
    # ============================================================
    # OLD ERROR TYPE - Used for employee ticket creation (New/Repeated)
    # ============================================================
    ERROR_TYPE_CHOICES = [
        ('New', 'New'),
        ('Repeated', 'Repeated'),
    ]
    
    # ============================================================
    # NEW ERROR TYPES - Used for admin closing tickets
    # ============================================================
    MAIN_ERROR_TYPE_CHOICES = [
        ('Roadmap Error', 'Roadmap Error'),
        ('GPL Error', 'GPL Error'),
    ]
    
    # Roadmap Error Sub-Types
    ROADMAP_SUB_ERROR_CHOICES = [
        ('Database Error', 'Database Error'),
        ('Logic / Functional Error', 'Logic / Functional Error'),
        ('Application Error', 'Application Error'),
        ('Calculation Error', 'Calculation Error'),
        ('Report / Print Error', 'Report / Print Error'),
        ('Workflow / Approval Error', 'Workflow / Approval Error'),
        ('Integration / API Error', 'Integration / API Error'),
        ('Barcode Error', 'Barcode Error'),
        ('Performance Error', 'Performance Error'),
        ('Access / Permission Error', 'Access / Permission Error'),
        ('Master Data / Configuration Error', 'Master Data / Configuration Error'),
        ('Other ERP Error', 'Other ERP Error'),
    ]
    
    # GPL Error Sub-Types
    GPL_SUB_ERROR_CHOICES = [
        ('User / Data Entry Error', 'User / Data Entry Error'),
        ('Process / Procedure Error', 'Process / Procedure Error'),
        ('Master Data Error', 'Master Data Error'),
        ('Other GPL Error', 'Other GPL Error'),
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

    # ============================================================
    # BASIC TICKET FIELDS
    # ============================================================
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
    
    # ============================================================
    # ERROR TYPE - Used for employee ticket creation
    # ============================================================
    error_type = models.CharField(
        max_length=50, 
        choices=ERROR_TYPE_CHOICES,
        default='New',
        verbose_name="Error Type"
    )
    
    # ============================================================
    # NEW FIELDS - Used when admin closes the ticket
    # ============================================================
    main_error_type = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        choices=MAIN_ERROR_TYPE_CHOICES,
        verbose_name="Main Error Type",
        help_text="Select the main error category when closing the ticket"
    )
    
    sub_error_type = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Sub Error Type",
        help_text="Select the sub-error type based on the main error category"
    )
    
    # ============================================================
    # ATTACHMENTS
    # ============================================================
    attachment_1 = models.FileField(upload_to='attachments/', blank=True, null=True)
    attachment_2 = models.FileField(upload_to='attachments/', blank=True, null=True)
    attachment_3 = models.FileField(upload_to='attachments/', blank=True, null=True)
    
    # ============================================================
    # STATUS & LIFECYCLE
    # ============================================================
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_by_role = models.CharField(max_length=10, choices=CREATED_BY_CHOICES, default='Employee')
    admin_creation_reason = models.CharField(max_length=50, choices=ADMIN_REASON_CHOICES, blank=True, null=True)
    assigned_person = models.CharField(max_length=100, blank=True, null=True)
    hold_reason = models.TextField(blank=True, null=True)
    closing_remarks = models.TextField(blank=True, null=True)
    closed_by = models.CharField(max_length=100, blank=True, null=True)
    vendor_ticket_number = models.CharField(max_length=100, blank=True, null=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    escalated_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ============================================================
    # NOTIFICATION FIELDS - Bell notification system
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

    def get_screen_display(self):
        """Return the screen name and code for legacy code or ID values."""
        screen = ScreenMaster.objects.filter(
            Q(screen_code=self.screen_number) | Q(pk=self.screen_number)
        ).first()
        if screen:
            return f'{screen.screen_name} ({screen.screen_code})'
        return self.screen_number or 'Not Set'
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def get_main_error_display(self):
        """Get display value for main error type"""
        if self.main_error_type:
            return self.main_error_type
        return "N/A"
    
    def get_sub_error_display(self):
        """Get display value for sub error type"""
        if self.sub_error_type:
            return self.sub_error_type
        return "N/A"
    
    def get_full_error_details(self):
        """Get full error details as dictionary"""
        return {
            'main_error_type': self.get_main_error_display(),
            'sub_error_type': self.get_sub_error_display(),
        }
    
    def has_closing_error_details(self):
        """Check if ticket has closing error details"""
        return bool(self.main_error_type and self.sub_error_type)
    
    def is_closed(self):
        """Check if ticket is closed"""
        return self.status == 'Closed'
    
    def can_reopen(self):
        """Check if ticket can be reopened (within 48 hours of closing)"""
        if not self.is_closed():
            return False
        if not self.closed_at:
            return False
        from django.utils import timezone
        from datetime import timedelta
        time_since_close = timezone.now() - self.closed_at
        return time_since_close.total_seconds() <= 48 * 3600


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=255)
    remarks = models.TextField(blank=True, null=True)
    performed_by = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.action} ({self.timestamp})"

    def get_performed_by_display(self):
        """Return a readable user label for current and legacy history rows."""
        if self.performed_by and self.performed_by.isdigit():
            user = User.objects.filter(pk=int(self.performed_by)).first()
            if user:
                return user.get_full_name() or user.username
        return self.performed_by or 'System'


class ReopenAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='reopen_attachments')
    file = models.FileField(upload_to='attachments/reopen/')
    uploaded_by = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.file.name}"


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
        ('SCREEN', 'Screen'),
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

    def get_performed_by_display(self):
        """Return a readable user label for current and legacy audit rows."""
        if self.performed_by:
            return self.performed_by.get_full_name() or self.performed_by.username
        if self.performed_by_name and self.performed_by_name.isdigit():
            user = User.objects.filter(pk=int(self.performed_by_name)).first()
            if user:
                return user.get_full_name() or user.username
        return self.performed_by_name or 'System'


# ============================================================
# ERP USER ID MAPPING MODEL
# ============================================================

class ERPHolderMapping(models.Model):
    """
    Maps ERP User IDs to Employee IDs
    One ERP User ID can have multiple Employee IDs mapped to it
    No restrictions on department or unit
    """
    erp_user_id = models.CharField(
        max_length=50, 
        db_index=True,
        verbose_name="ERP User ID",
        help_text="ERP User ID (e.g., 0001, 0002)"
    )
    employee = models.ForeignKey(
        EmployeeMaster, 
        on_delete=models.CASCADE, 
        related_name='erp_mappings',
        verbose_name="Employee",
        help_text="Employee mapped to this ERP User ID"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        unique_together = ['erp_user_id', 'employee']
        ordering = ['erp_user_id', 'employee__employee_id']
        verbose_name = 'ERP User ID Mapping'
        verbose_name_plural = 'ERP User ID Mappings'
        indexes = [
            models.Index(fields=['erp_user_id']),
            models.Index(fields=['employee']),
        ]
    
    def __str__(self):
        return f"ERP {self.erp_user_id} → {self.employee.employee_id} ({self.employee.employee_name})"
    
    def get_employee_details(self):
        return {
            'employee_id': self.employee.employee_id,
            'employee_name': self.employee.employee_name,
            'mobile': self.employee.mobile,
            'email': self.employee.email,
            'unit_code': self.employee.unit.code if self.employee.unit else '',
            'unit_name': self.employee.unit.full_name if self.employee.unit else '',
            'department_name': self.employee.department.name if self.employee.department else '',
        }


# ============================================================
# SCREEN MASTER MODEL
# ============================================================

class ScreenMaster(models.Model):
    """
    Master list of ERP Screens/Modules.
    Screen Name and Screen Code must be unique.
    """
    SCREEN_TYPE_CHOICES = [
        ('ALL', 'General'),
        ('ENTRY', 'Data Entry'),
        ('CONFIGURATION', 'Configuration'),
        ('QUERY', 'Report/Query'),
    ]

    screen_name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Screen Name",
        help_text="Full name of the screen/module (e.g., Sales Order Entry)"
    )
    screen_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Screen Code",
        help_text="Short code for the screen (e.g., SO-001)"
    )
    screen_type = models.CharField(
        max_length=20,
        choices=SCREEN_TYPE_CHOICES,
        default='ALL',
        verbose_name="Screen Type",
        help_text="The category of the screen"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['screen_name']
        verbose_name = 'Screen Master'
        verbose_name_plural = 'Screen Masters'

    def save(self, *args, **kwargs):
        self.screen_name = self.screen_name.strip()
        self.screen_code = self.screen_code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.screen_code} - {self.screen_name} ({self.get_screen_type_display()})"


# ============================================================
# SCREEN MAPPING MODEL
# ============================================================

class ScreenMapping(models.Model):
    """
    Maps screens from ScreenMaster to ERP User IDs.
    One screen can be mapped to multiple ERP IDs.
    One ERP ID can have multiple screens.
    """
    screen = models.ForeignKey(
        ScreenMaster,
        on_delete=models.CASCADE,
        related_name='screen_mappings',
        verbose_name="Screen"
    )
    erp_user_id = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="ERP User ID",
        help_text="ERP User ID (links to ERPHolderMapping.erp_user_id)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['screen', 'erp_user_id']
        ordering = ['erp_user_id', 'screen__screen_name']
        verbose_name = 'Screen Mapping'
        verbose_name_plural = 'Screen Mappings'
        indexes = [
            models.Index(fields=['erp_user_id']),
            models.Index(fields=['screen']),
        ]

    def __str__(self):
        return f"{self.screen.screen_code} → ERP {self.erp_user_id}"