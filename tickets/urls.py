from django.urls import path
from django.contrib import messages
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Role-based redirects & auth
    path('role-redirect/', views.role_redirect, name='role_redirect'),
    path('logout/', views.custom_logout, name='custom_logout'),

    # =========================================================================
    # EMPLOYEE URLS
    # =========================================================================
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),

    # =========================================================================
    # ADMIN URLS
    # =========================================================================
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-ticket/', views.create_ticket_admin, name='create_ticket_admin'),
    path('admin/tickets/', views.all_tickets, name='all_tickets'),
    path('admin/ticket/<int:pk>/', views.ticket_detail_admin, name='admin_ticket_detail'),
    path('admin/reports/', views.reports, name='reports'),
    
    # Settings URLs
    path('admin/settings/', views.settings_page, name='settings_page'),
    path('admin/settings/contact/', views.settings_contact, name='settings_contact'),
    path('admin/settings/units/', views.settings_units, name='settings_units'),
    path('admin/settings/departments/', views.settings_departments, name='settings_departments'),
    path('admin/settings/emails/', views.settings_emails, name='settings_emails'),
    path('admin/settings/passwords/', views.settings_passwords, name='settings_passwords'),

    # =========================================================================
    # TEST NOTIFICATION URLS
    # =========================================================================
    path('test-notifications/', views.test_notifications, name='test_notifications'),
    path('test/success/', views.test_success_message, name='test_success'),
    path('test/error/', views.test_error_message, name='test_error'),
    path('test/warning/', views.test_warning_message, name='test_warning'),
    path('test/info/', views.test_info_message, name='test_info'),

    # =========================================================================
    # AJAX ENDPOINTS
    # =========================================================================
    path('ajax/get-departments/', views.get_departments_by_unit, name='get_departments_by_unit'),
]