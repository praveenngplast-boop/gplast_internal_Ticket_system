# tickets/views/settings_views.py
"""
Settings Views (GET) - All settings page views
- Settings Dashboard
- Units & Departments
- Communication
- Employees
- Credentials
- Dept Employees
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from tickets.models import Unit, Department, AdminContact, AdminNotificationEmail, EmployeeMaster, DepartmentCredential
from tickets.forms import UnitForm, DepartmentForm, AdminContactForm, AdminNotificationEmailForm

from .utils import (
    is_admin,
    _get_contact_data,
    _get_employee_directory_data,
    _get_credentials_data,
)


# ============================================================
# SETTINGS DASHBOARD
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='admin_dashboard')
def settings_page(request):
    """
    Settings dashboard/index page with navigation cards
    URL: /admin/settings/
    """
    return render(request, 'admin_panel/settings_index.html')


# ============================================================
# UNITS & DEPARTMENTS
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='admin_dashboard')
def settings_units_departments(request):
    """
    Manage Units and Departments
    URL: /admin/settings/units-departments/
    """
    context = {
        'unit_form': UnitForm(),
        'dept_form': DepartmentForm(),
        'units': Unit.objects.all().order_by('code'),
        'departments': Department.objects.all().order_by('unit__code', 'name'),
    }
    return render(request, 'admin_panel/units_departments.html', context)


# ============================================================
# COMMUNICATION SETTINGS
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='admin_dashboard')
def settings_communication(request):
    """
    Manage Helpdesk Contact and Notification Emails
    URL: /admin/settings/communication/
    """
    contact_obj = _get_contact_data()
    context = {
        'contact': contact_obj,
        'contact_form': AdminContactForm(instance=contact_obj),
        'email_form': AdminNotificationEmailForm(),
        'emails': AdminNotificationEmail.objects.all().order_by('-created_at'),
    }
    return render(request, 'admin_panel/communication.html', context)


# ============================================================
# EMPLOYEE MANAGEMENT
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='admin_dashboard')
def settings_employees_page(request):
    """
    Complete employee management with Can Assign toggle
    URL: /admin/settings/employees/
    """
    employees_qs, emp_search = _get_employee_directory_data(request)
    context = {
        'employees': employees_qs,
        'emp_search': emp_search,
        'all_units': Unit.objects.filter(is_active=True).order_by('code'),
        'departments': Department.objects.all().order_by('unit__code', 'name'),
    }
    return render(request, 'admin_panel/employees.html', context)


# ============================================================
# DEPARTMENT CREDENTIALS
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='admin_dashboard')
def settings_credentials_page(request):
    """
    Manage department credentials
    URL: /admin/settings/credentials/
    """
    all_credentials, credentials_by_unit = _get_credentials_data()
    context = {
        'all_units': Unit.objects.filter(is_active=True).order_by('code'),
        'credentials': all_credentials,
        'credentials_by_unit': credentials_by_unit,
        'employee_users': User.objects.filter(is_staff=False, is_active=True).order_by('username'),
    }
    return render(request, 'admin_panel/credentials.html', context)


# ============================================================
# DEPARTMENT-WISE EMPLOYEE VIEW
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='admin_dashboard')
def settings_dept_employees(request):
    """
    View employees organized by department (tree view)
    URL: /admin/settings/dept-employees/
    """
    all_credentials, credentials_by_unit = _get_credentials_data()
    context = {
        'all_units': Unit.objects.filter(is_active=True).order_by('code'),
        'credentials_by_unit': credentials_by_unit,
    }
    return render(request, 'admin_panel/dept_employees.html', context)