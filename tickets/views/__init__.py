# tickets/views/__init__.py

from .auth_views import (
    CustomLoginView,
    role_redirect,
    custom_logout,
)

from .admin_views import (
    admin_dashboard,
    create_ticket_admin,
    all_tickets,
    ticket_detail_admin,
    download_ticket_excel as admin_download_ticket_excel,
    export_closed_tickets_30_days as admin_export_closed_tickets_30_days,
    reports,
    get_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    test_notifications,
    test_success_message,
    test_error_message,
    test_warning_message,
    test_info_message,
    download_audit_log_excel as admin_download_audit_log_excel,
)

from .employee_views import (
    employee_dashboard,
    create_ticket,
    all_tickets as employee_all_tickets,
    my_tickets,
    employee_ticket_detail,
    ticket_detail,
    update_ticket_status,
    download_individual_ticket_excel,  # ✅ This is the correct function name
    export_closed_tickets_30_days as employee_export_closed_tickets_30_days,
    get_employee_details,
    # ===== NEW FUNCTIONS =====
    export_filtered_tickets_excel,
    export_filtered_my_tickets_excel,
)

from .settings_views import (
    settings_page,
    settings_units_departments,
    settings_communication,
    settings_employees_page,
    settings_credentials_page,
    settings_dept_employees,
    settings_audit_log,
    download_audit_log_excel as settings_download_audit_log_excel,
)

from .settings_actions import (
    settings_contact,
    settings_units,
    settings_departments,
    settings_emails,
    settings_passwords,
    settings_employees,
    download_employee_list,
    download_employee_template,
    settings_credentials,
    download_credentials,
)

from .ajax_views import (
    get_units,
    get_departments_by_unit,
    get_employee_details as ajax_get_employee_details,
    get_employees_by_department,
)

# Export all views
__all__ = [
    # Auth views
    'CustomLoginView',
    'role_redirect',
    'custom_logout',
    
    # Admin views
    'admin_dashboard',
    'create_ticket_admin',
    'all_tickets',
    'ticket_detail_admin',
    'admin_download_ticket_excel',
    'admin_export_closed_tickets_30_days',
    'reports',
    'get_notifications',
    'mark_all_notifications_read',
    'mark_notification_read',
    'test_notifications',
    'test_success_message',
    'test_error_message',
    'test_warning_message',
    'test_info_message',
    'admin_download_audit_log_excel',
    
    # Employee views
    'employee_dashboard',
    'create_ticket',
    'employee_all_tickets',
    'my_tickets',
    'employee_ticket_detail',
    'ticket_detail',
    'update_ticket_status',
    'download_individual_ticket_excel',  # ✅ Correct function name
    'employee_export_closed_tickets_30_days',
    'get_employee_details',
    'export_filtered_tickets_excel',
    'export_filtered_my_tickets_excel',
    
    # Settings views
    'settings_page',
    'settings_units_departments',
    'settings_communication',
    'settings_employees_page',
    'settings_credentials_page',
    'settings_dept_employees',
    'settings_audit_log',
    'settings_download_audit_log_excel',
    'settings_contact',
    'settings_units',
    'settings_departments',
    'settings_emails',
    'settings_passwords',
    'settings_employees',
    'download_employee_list',
    'download_employee_template',
    'settings_credentials',
    'download_credentials',
    
    # AJAX views
    'get_units',
    'get_departments_by_unit',
    'ajax_get_employee_details',
    'get_employees_by_department',
]