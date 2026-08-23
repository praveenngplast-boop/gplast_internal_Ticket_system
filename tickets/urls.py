# tickets/urls.py

from django.urls import path
from . import views
from tickets.views import erp_mapping_views
from tickets.views.reports_views import (
    reports,
    download_ticket_excel,
    export_closed_tickets_30_days,
    escalated_aging_report,
)
# Import the few action views used directly by these URL patterns.
from tickets.views.settings_action import (
    screen_mapping_delete_erp,
    screen_master_download_template,
    screen_master_bulk_upload,
)

urlpatterns = [
    # ============================================================
    # AUTH URLS
    # ============================================================
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('role-redirect/', views.role_redirect, name='role_redirect'),
    path('logout/', views.custom_logout, name='custom_logout'),

    # ============================================================
    # EMPLOYEE URLS
    # ============================================================
    path('', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('all-tickets/', views.all_tickets, name='all_tickets'),
    path('ticket/<int:ticket_id>/update/', views.update_ticket_status, name='update_ticket_status'),
    path('ticket/<int:ticket_id>/download/', views.download_individual_ticket_excel, name='employee_download_ticket_excel'),
    path('export/closed-30-days/', views.employee_export_closed_tickets_30_days, name='employee_export_closed_30_days'),

    # ============================================================
    # ADMIN URLS
    # ============================================================
    path('custom-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/create-ticket/', views.create_ticket_admin, name='create_ticket_admin'),
    path('custom-admin/tickets/', views.all_tickets, name='all_tickets'),
    path('custom-admin/ticket/<int:pk>/', views.ticket_detail_admin, name='admin_ticket_detail'),
    
    # ✅ REPORTS URLS - Using imported reports_views functions
    path('custom-admin/reports/', reports, name='reports'),
    path('custom-admin/reports/escalated-aging/', escalated_aging_report, name='escalated_aging_report'),
    path('custom-admin/download-ticket/<int:pk>/excel/', download_ticket_excel, name='admin_download_ticket_excel'),
    path('custom-admin/export/closed-30-days/', export_closed_tickets_30_days, name='export_closed_30_days'),

    # ============================================================
    # NOTIFICATION URLS
    # ============================================================
    path('custom-admin/notifications/get/', views.get_notifications, name='get_notifications'),
    path('custom-admin/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('custom-admin/notifications/mark-read/<int:ticket_id>/', views.mark_notification_read, name='mark_notification_read'),

    # ============================================================
    # SETTINGS URLS - GET PAGES
    # ============================================================
    path('custom-admin/settings/', views.settings_page, name='settings_page'),
    path('custom-admin/settings/email-reports/', views.settings_email_reports, name='settings_email_reports'),
    path('custom-admin/settings/units-departments/', views.settings_units_departments, name='settings_units_departments'),
    path('custom-admin/settings/communication/', views.settings_communication, name='settings_communication'),
    path('custom-admin/settings/employees/', views.settings_employees_page, name='settings_employees_page'),
    path('custom-admin/settings/credentials/', views.settings_credentials_page, name='settings_credentials_page'),
    path('custom-admin/settings/dept-employees/', views.settings_dept_employees, name='settings_dept_employees'),
    path('custom-admin/settings/audit/', views.settings_audit_log, name='settings_audit_log'),
    
    # ✅ FIXED: Use admin_download_audit_log_excel instead of download_audit_log_excel
    path('custom-admin/settings/audit/download-excel/', views.admin_download_audit_log_excel, name='admin_download_audit_log_excel'),

    # ============================================================
    # SETTINGS URLS - POST ACTIONS
    # ============================================================
    path('custom-admin/settings/contact/', views.settings_contact, name='settings_contact'),
    path('custom-admin/settings/units/', views.settings_units, name='settings_units'),
    path('custom-admin/settings/departments/', views.settings_departments, name='settings_departments'),
    path('custom-admin/settings/emails/', views.settings_emails, name='settings_emails'),
    path('custom-admin/settings/passwords/', views.settings_passwords, name='settings_passwords'),
    path('custom-admin/settings/employees/handler/', views.settings_employees, name='settings_employees'),
    path('custom-admin/settings/employees/download/', views.download_employee_list, name='download_employee_list'),
    path('custom-admin/settings/employees/template/', views.download_employee_template, name='download_employee_template'),
    path('custom-admin/settings/credentials/handler/', views.settings_credentials, name='settings_credentials'),
    path('custom-admin/settings/credentials/download/', views.download_credentials, name='download_credentials'),

    # ============================================================
    # ERP USER ID MAPPING URLS
    # ============================================================
    path('custom-admin/settings/erp-mapping/', erp_mapping_views.erp_mapping_page, name='settings_erp_mapping'),
    path('custom-admin/settings/erp-mapping/add/', erp_mapping_views.erp_mapping_add, name='settings_erp_mapping_add'),
    path('custom-admin/settings/erp-mapping/remove/', erp_mapping_views.erp_mapping_remove, name='settings_erp_mapping_remove'),
    
    # ERP USER ID MAPPING - EXPORT URLS
    path('custom-admin/settings/erp-mapping/export-excel/', erp_mapping_views.erp_mapping_export_excel, name='settings_erp_mapping_export_excel'),
    
    # ERP USER ID MAPPING - AJAX URLS
    path('ajax/get-erp-mappings/', erp_mapping_views.erp_mapping_list, name='settings_erp_mapping_list'),
    path('ajax/search-employees/', erp_mapping_views.erp_mapping_search_employees, name='settings_erp_mapping_search_employees'),

    # ============================================================
    # TEST NOTIFICATION URLS
    # ============================================================
    path('test-notifications/', views.test_notifications, name='test_notifications'),
    path('test/success/', views.test_success_message, name='test_success'),
    path('test/error/', views.test_error_message, name='test_error'),
    path('test/warning/', views.test_warning_message, name='test_warning'),
    path('test/info/', views.test_info_message, name='test_info'),

    # ============================================================
    # SCREEN MASTER URLS
    # ============================================================
    path('custom-admin/settings/screen-master/', views.settings_screen_master, name='settings_screen_master'),
    path('custom-admin/settings/screen-master/add/', views.screen_master_add, name='screen_master_add'),
    path('custom-admin/settings/screen-master/edit/', views.screen_master_edit, name='screen_master_edit'),
    path('custom-admin/settings/screen-master/delete/', views.screen_master_delete, name='screen_master_delete'),
    path('custom-admin/settings/screen-master/download/', views.screen_master_download_excel, name='screen_master_download_excel'),
    # ✅ USING IMPORTED FUNCTIONS
    path('custom-admin/settings/screen-master/download-template/', screen_master_download_template, name='screen_master_download_template'),
    path('custom-admin/settings/screen-master/bulk-upload/', screen_master_bulk_upload, name='screen_master_bulk_upload'),

    # ============================================================
    # SCREEN MAPPING URLS
    # ============================================================
    path('custom-admin/settings/screen-mapping/', views.settings_screen_mapping_page, name='settings_screen_mapping'),
    path('custom-admin/settings/screen-mapping/add/', views.screen_mapping_add, name='screen_mapping_add'),
    path('custom-admin/settings/screen-mapping/remove/', views.screen_mapping_remove, name='screen_mapping_remove'),
    # ✅ USING IMPORTED FUNCTION
    path('custom-admin/settings/screen-mapping/delete-erp/', screen_mapping_delete_erp, name='screen_mapping_delete_erp'),
    path('custom-admin/settings/screen-mapping/export/', views.screen_mapping_export_excel, name='screen_mapping_export_excel'),

    # ============================================================
    # AJAX ENDPOINTS
    # ============================================================
    path('ajax/get-units/', views.get_units, name='get_units'),
    path('ajax/get-departments/', views.get_departments_by_unit, name='get_departments_by_unit'),
    path('ajax/get-employee/', views.ajax_get_employee_details, name='ajax_get_employee_details'),
    path('ajax/get-employees-by-department/', views.get_employees_by_department, name='get_employees_by_department'),
    path('ajax/get-screens-for-erp/', views.ajax_get_screens_for_erp, name='ajax_get_screens_for_erp'),
]