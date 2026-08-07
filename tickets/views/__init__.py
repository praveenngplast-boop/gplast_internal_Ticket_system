# tickets/views/__init__.py
"""
Import all views for easy access from tickets.views
"""

# ============================================================
# Auth Views
# ============================================================
from .auth_views import CustomLoginView, role_redirect, custom_logout

# ============================================================
# Employee Views
# ============================================================
from .employee_views import (
    employee_dashboard,
    create_ticket,
    my_tickets,
    ticket_detail,
    all_tickets,
    employee_ticket_detail,
    download_ticket_excel,
    update_ticket_status,
)

# ============================================================
# Admin Views
# ============================================================
from .admin_views import (
    admin_dashboard,
    create_ticket_admin,
    all_tickets,
    ticket_detail_admin,
    download_ticket_excel,
    reports,
    test_notifications,
    test_success_message,
    test_error_message,
    test_warning_message,
    test_info_message,
    get_notifications,              # <-- ADD THIS
    mark_all_notifications_read,    # <-- ADD THIS
    mark_notification_read,         # <-- ADD THIS
)

# ============================================================
# Settings Views (GET)
# ============================================================
from .settings_views import (
    settings_page,
    settings_units_departments,
    settings_communication,
    settings_employees_page,
    settings_credentials_page,
    settings_dept_employees,
)

# ============================================================
# Settings Actions (POST)
# ============================================================
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

# ============================================================
# AJAX Views
# ============================================================
from .ajax_views import (
    get_units,
    get_departments_by_unit,
    get_employee_details,
    get_employees_by_department,
)

# ============================================================
# Utilities (re-export for convenience)
# ============================================================
from .utils import (
    is_admin,
    format_timedelta_display,
    get_client_ip,
    reopen_ticket_logic,
    generate_ticket_list_html,
    generate_admin_ticket_list_html,
    _get_contact_data,
    _get_employee_directory_data,
    _get_credentials_data,
)