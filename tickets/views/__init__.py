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

# ✅ Import Reports Views from separate file
from .reports_views import (
    reports,
    download_ticket_excel as admin_download_ticket_excel,
    export_closed_tickets_30_days as admin_export_closed_tickets_30_days,
)

from .employee_views import (
    employee_dashboard,
    create_ticket,
    all_tickets as employee_all_tickets,
    my_tickets,
    employee_ticket_detail,
    ticket_detail,
    update_ticket_status,
    download_individual_ticket_excel,
    export_closed_tickets_30_days as employee_export_closed_tickets_30_days,
    get_employee_details,
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
    settings_screen_master,
)
from .audit_views import (
    settings_audit_log,
    download_audit_log_excel as settings_download_audit_log_excel,
)
from .backup_views import download_full_backup
from .scheduled_email_views import settings_email_reports

# Import settings action views from the package.
from .settings_action import (
    # Contact
    settings_contact,
    # Units
    settings_units,
    settings_departments,
    # Emails
    settings_emails,
    # Passwords
    settings_passwords,
    # Employees
    settings_employees,
    download_employee_list,
    download_employee_template,
    # Credentials
    settings_credentials,
    download_credentials,
    # Screen Master
    screen_master_add,
    screen_master_edit,
    screen_master_delete,
    screen_master_download_excel,
    screen_master_download_template,
    screen_master_bulk_upload,
    # Screen Mapping
    screen_mapping_add,
    screen_mapping_remove,
    screen_mapping_delete_erp,
    screen_mapping_export_excel,
    settings_screen_mapping_page,
    ajax_get_screens_for_erp,
)

from .ajax_views import (
    get_units,
    get_departments_by_unit,
    get_employee_details as ajax_get_employee_details,
    get_employees_by_department,
)

# ============================================================
# ERP USER ID MAPPING VIEWS
# ============================================================
from .erp_mapping_views import (
    erp_mapping_page,
    erp_mapping_add,
    erp_mapping_remove,
    erp_mapping_list,
    erp_mapping_search_employees,
    erp_mapping_export_excel,
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
    'download_individual_ticket_excel',
    'employee_export_closed_tickets_30_days',
    'get_employee_details',
    'export_filtered_tickets_excel',
    'export_filtered_my_tickets_excel',
    
    # Settings views
    'settings_page',
    'settings_email_reports',
    'settings_units_departments',
    'settings_communication',
    'settings_employees_page',
    'settings_credentials_page',
    'settings_dept_employees',
    'settings_audit_log',
    'settings_download_audit_log_excel',
    'download_full_backup',
    'settings_screen_master',
    
    # Settings Actions
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
    'screen_master_add',
    'screen_master_edit',
    'screen_master_delete',
    'screen_master_download_excel',
    'screen_master_download_template',
    'screen_master_bulk_upload',
    'screen_mapping_add',
    'screen_mapping_remove',
    'screen_mapping_delete_erp',
    'screen_mapping_export_excel',
    'settings_screen_mapping_page',
    'ajax_get_screens_for_erp',
    
    # AJAX views
    'get_units',
    'get_departments_by_unit',
    'ajax_get_employee_details',
    'get_employees_by_department',
    
    # ERP USER ID MAPPING VIEWS
    'erp_mapping_page',
    'erp_mapping_add',
    'erp_mapping_remove',
    'erp_mapping_list',
    'erp_mapping_search_employees',
    'erp_mapping_export_excel',
]