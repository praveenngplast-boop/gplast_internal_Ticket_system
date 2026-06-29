from django.urls import path
from tickets import views

urlpatterns = [
    # Role Redirect
    path('role-redirect/', views.role_redirect, name='role_redirect'),
    path('logout/', views.custom_logout, name='custom_logout'),

    # Employee Routes
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/create-ticket/', views.create_ticket, name='create_ticket'),
    path('employee/my-tickets/', views.my_tickets, name='my_tickets'),
    path('employee/ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),

    # Admin Routes
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create-ticket/', views.create_ticket_admin, name='create_ticket_admin'),
    path('admin/tickets/', views.all_tickets, name='all_tickets'),
    path('admin/ticket/<int:pk>/', views.ticket_detail_admin, name='admin_ticket_detail'),
    path('admin/reports/', views.reports, name='reports'),
    path('admin/settings/', views.settings_page, name='settings_page'),

    # AJAX Endpoints
    path('ajax/departments/', views.get_departments_by_unit, name='ajax_departments'),
]
