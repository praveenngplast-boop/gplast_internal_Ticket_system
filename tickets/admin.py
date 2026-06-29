from django.contrib import admin
from tickets.models import Unit, Department, AdminContact, AdminNotificationEmail, Ticket, TicketHistory

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'full_name', 'is_active', 'created_at')
    search_fields = ('code', 'full_name')
    list_filter = ('is_active',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'is_active', 'created_at')
    search_fields = ('name', 'unit__code')
    list_filter = ('is_active', 'unit')

@admin.register(AdminContact)
class AdminContactAdmin(admin.ModelAdmin):
    list_display = ('admin_name', 'admin_phone', 'admin_email')

@admin.register(AdminNotificationEmail)
class AdminNotificationEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'unit', 'department', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'unit', 'created_by_role')
    search_fields = ('ticket_number', 'subject', 'employee_name', 'employee_id')
    readonly_fields = ('ticket_number', 'created_at')

@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'action', 'performed_by', 'timestamp')
    list_filter = ('performed_by', 'timestamp')
    search_fields = ('ticket__ticket_number', 'action')
