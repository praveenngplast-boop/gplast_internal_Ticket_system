# tickets/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

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
    path('ticket/<int:ticket_id>/download/', views.download_ticket_excel, name='download_ticket_excel'),

    # ============================================================
    # ADMIN URLS
    # ============================================================
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-ticket/', views.create_ticket_admin, name='create_ticket_admin'),
    path('admin/tickets/', views.all_tickets, name='all_tickets'),
    path('admin/ticket/<int:pk>/', views.ticket_detail_admin, name='admin_ticket_detail'),
    path('admin/reports/', views.reports, name='reports'),
    path('admin/download-ticket/<int:pk>/excel/', views.download_ticket_excel, name='download_ticket_excel'),

    # ============================================================
    # NOTIFICATION URLS - ADD THIS SECTION
    # ============================================================
    path('admin/notifications/get/', views.get_notifications, name='get_notifications'),
    path('admin/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('admin/notifications/mark-read/<int:ticket_id>/', views.mark_notification_read, name='mark_notification_read'),

    # ============================================================
    # SETTINGS URLS - GET PAGES
    # ============================================================
    path('admin/settings/', views.settings_page, name='settings_page'),
    path('admin/settings/units-departments/', views.settings_units_departments, name='settings_units_departments'),
    path('admin/settings/communication/', views.settings_communication, name='settings_communication'),
    path('admin/settings/employees/', views.settings_employees_page, name='settings_employees_page'),
    path('admin/settings/credentials/', views.settings_credentials_page, name='settings_credentials_page'),
    path('admin/settings/dept-employees/', views.settings_dept_employees, name='settings_dept_employees'),

    # ============================================================
    # SETTINGS URLS - POST ACTIONS (HANDLERS)
    # ============================================================
    path('admin/settings/contact/', views.settings_contact, name='settings_contact'),
    path('admin/settings/units/', views.settings_units, name='settings_units'),
    path('admin/settings/departments/', views.settings_departments, name='settings_departments'),
    path('admin/settings/emails/', views.settings_emails, name='settings_emails'),
    path('admin/settings/passwords/', views.settings_passwords, name='settings_passwords'),
    path('admin/settings/employees/handler/', views.settings_employees, name='settings_employees'),
    path('admin/settings/employees/download/', views.download_employee_list, name='download_employee_list'),
    path('admin/settings/employees/template/', views.download_employee_template, name='download_employee_template'),
    path('admin/settings/credentials/handler/', views.settings_credentials, name='settings_credentials'),
    path('admin/settings/credentials/download/', views.download_credentials, name='download_credentials'),

    # ============================================================
    # TEST NOTIFICATION URLS
    # ============================================================
    path('test-notifications/', views.test_notifications, name='test_notifications'),
    path('test/success/', views.test_success_message, name='test_success'),
    path('test/error/', views.test_error_message, name='test_error'),
    path('test/warning/', views.test_warning_message, name='test_warning'),
    path('test/info/', views.test_info_message, name='test_info'),

    # ============================================================
    # AJAX ENDPOINTS
    # ============================================================
    path('ajax/get-units/', views.get_units, name='get_units'),
    path('ajax/get-departments/', views.get_departments_by_unit, name='get_departments_by_unit'),
    path('ajax/get-employee/', views.get_employee_details, name='get_employee_details'),
    path('ajax/get-employees-by-department/', views.get_employees_by_department, name='get_employees_by_department'),
]