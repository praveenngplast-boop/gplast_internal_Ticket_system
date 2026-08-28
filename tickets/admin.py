from django.contrib import admin
from tickets.models import (
    Unit, 
    Department, 
    AdminContact, 
    # AdminNotificationEmail,  # COMMENTED - Email related model
    Ticket, 
    TicketHistory, 
    UnitHead, 
    # EmailSchedule,  # COMMENTED - Email related model
    EmployeeMaster,
    DepartmentCredential,
    SettingsAuditLog,
    ERPHolderMapping,
    ScreenMaster,
    ScreenMapping,
    ReopenAttachment,
)


# ============================================================
# UNIT ADMIN
# ============================================================
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'full_name', 'is_active', 'created_at')
    search_fields = ('code', 'full_name')
    list_filter = ('is_active',)
    readonly_fields = ('created_at',)


# ============================================================
# DEPARTMENT ADMIN
# ============================================================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'is_active', 'created_at')
    search_fields = ('name', 'unit__code')
    list_filter = ('is_active', 'unit')
    readonly_fields = ('created_at',)


# ============================================================
# ADMIN CONTACT ADMIN
# ============================================================
@admin.register(AdminContact)
class AdminContactAdmin(admin.ModelAdmin):
    list_display = ('admin_name', 'admin_phone', 'admin_email')
    search_fields = ('admin_name', 'admin_email')


# ============================================================
# ADMIN NOTIFICATION EMAIL ADMIN - COMMENTED OUT (Email sending disabled)
# ============================================================
# @admin.register(AdminNotificationEmail)
# class AdminNotificationEmailAdmin(admin.ModelAdmin):
#     list_display = ('email', 'is_active', 'created_at')
#     search_fields = ('email',)
#     list_filter = ('is_active',)
#     readonly_fields = ('created_at',)


# ============================================================
# UNIT HEAD ADMIN - UPDATED WITH USER FIELD
# ============================================================
@admin.register(UnitHead)
class UnitHeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'email', 'user', 'is_active', 'created_at')
    list_display_links = ('name', 'unit')
    search_fields = ('name', 'email', 'unit__code', 'user__username')
    list_filter = ('is_active', 'unit')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Unit Head Details', {
            'fields': ('name', 'email', 'unit', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'unit')


# ============================================================
# EMAIL SCHEDULE ADMIN - COMMENTED OUT (Email sending disabled)
# ============================================================
# @admin.register(EmailSchedule)
# class EmailScheduleAdmin(admin.ModelAdmin):
#     list_display = ('enabled', 'frequency', 'send_time', 'updated_at', 'last_sent_at')
#     list_filter = ('enabled', 'frequency')
#     search_fields = ('subject_template',)
#     readonly_fields = ('updated_at', 'last_sent_at')
#     filter_horizontal = ('units',)


# ============================================================
# EMPLOYEE MASTER ADMIN
# ============================================================
@admin.register(EmployeeMaster)
class EmployeeMasterAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'employee_name', 'unit', 'department', 'is_active', 'can_assign_ticket')
    search_fields = ('employee_id', 'employee_name', 'mobile', 'email')
    list_filter = ('is_active', 'unit', 'department', 'can_assign_ticket')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee_id', 'employee_name', 'mobile', 'email')
        }),
        ('Organization', {
            'fields': ('unit', 'department')
        }),
        ('Permissions', {
            'fields': ('is_active', 'can_assign_ticket')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# DEPARTMENT CREDENTIAL ADMIN
# ============================================================
@admin.register(DepartmentCredential)
class DepartmentCredentialAdmin(admin.ModelAdmin):
    list_display = ('unit', 'department', 'username', 'is_active', 'created_at')
    search_fields = ('username', 'unit__code', 'department__name')
    list_filter = ('is_active', 'unit')
    readonly_fields = ('created_at', 'updated_at')


# ============================================================
# TICKET ADMIN
# ============================================================
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'unit', 'department', 'status', 'priority', 'created_at')
    list_display_links = ('ticket_number', 'subject')
    list_filter = ('status', 'priority', 'unit', 'created_by_role', 'created_at')
    search_fields = ('ticket_number', 'subject', 'employee_name', 'employee_id', 'description')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'subject', 'description', 'priority', 'error_type')
        }),
        ('Employee Details', {
            'fields': ('employee_id', 'employee_name', 'mobile', 'email')
        }),
        ('Organization', {
            'fields': ('unit', 'department', 'screen_number')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_person', 'hold_reason')
        }),
        ('Closure Details', {
            'fields': ('main_error_type', 'sub_error_type', 'closing_remarks', 'closed_by', 'closed_at'),
            'classes': ('collapse',)
        }),
        ('Escalation', {
            'fields': ('vendor_ticket_number', 'escalated_at'),
            'classes': ('collapse',)
        }),
        ('Attachments', {
            'fields': ('attachment_1', 'attachment_2', 'attachment_3'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_by_user', 'created_by_role', 'admin_creation_reason', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        # ('Notifications', {  # COMMENTED - Email notification related
        #     'fields': ('is_viewed', 'viewed_at', 'notification_sent'),
        #     'classes': ('collapse',)
        # }),
    )


# ============================================================
# TICKET HISTORY ADMIN
# ============================================================
@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'action', 'performed_by', 'timestamp')
    list_filter = ('performed_by', 'timestamp')
    search_fields = ('ticket__ticket_number', 'action', 'remarks')
    readonly_fields = ('timestamp',)


# ============================================================
# REOPEN ATTACHMENT ADMIN
# ============================================================
@admin.register(ReopenAttachment)
class ReopenAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_by',)
    search_fields = ('ticket__ticket_number', 'file')
    readonly_fields = ('uploaded_at',)


# ============================================================
# SETTINGS AUDIT LOG ADMIN
# ============================================================
@admin.register(SettingsAuditLog)
class SettingsAuditLogAdmin(admin.ModelAdmin):
    list_display = ('performed_by_name', 'action_type', 'setting_type', 'setting_name', 'created_at')
    list_display_links = ('performed_by_name', 'setting_name')
    list_filter = ('action_type', 'setting_type', 'created_at')
    search_fields = ('performed_by_name', 'setting_name', 'change_summary', 'remarks')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('performed_by', 'performed_by_name', 'ip_address', 'user_agent')
        }),
        ('Action Details', {
            'fields': ('action_type', 'setting_type', 'setting_name')
        }),
        ('Changes', {
            'fields': ('old_value', 'new_value', 'change_summary', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# ERP HOLDER MAPPING ADMIN
# ============================================================
@admin.register(ERPHolderMapping)
class ERPHolderMappingAdmin(admin.ModelAdmin):
    list_display = ('erp_user_id', 'employee', 'created_at')
    search_fields = ('erp_user_id', 'employee__employee_id', 'employee__employee_name')
    list_filter = ('employee__unit',)
    readonly_fields = ('created_at', 'updated_at')


# ============================================================
# SCREEN MASTER ADMIN
# ============================================================
@admin.register(ScreenMaster)
class ScreenMasterAdmin(admin.ModelAdmin):
    list_display = ('screen_code', 'screen_name', 'screen_type', 'is_active', 'created_at')
    search_fields = ('screen_code', 'screen_name')
    list_filter = ('is_active', 'screen_type')
    readonly_fields = ('created_at', 'updated_at')


# ============================================================
# SCREEN MAPPING ADMIN
# ============================================================
@admin.register(ScreenMapping)
class ScreenMappingAdmin(admin.ModelAdmin):
    list_display = ('screen', 'erp_user_id', 'created_at')
    search_fields = ('screen__screen_code', 'screen__screen_name', 'erp_user_id')
    list_filter = ('screen__screen_type',)
    readonly_fields = ('created_at',)


# ============================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================
admin.site.site_header = 'GPLAST Ticket System Administration'
admin.site.site_title = 'GPLAST Ticket System'
admin.site.index_title = 'Welcome to GPLAST Ticket System Admin'