# tickets/views/ajax_views.py
"""
AJAX Endpoints for dynamic content loading
- Get Units
- Get Departments by Unit
- Get Employee Details
- Get Employees by Department
"""
from django.http import JsonResponse
from django.db.models import Q
import logging

from tickets.models import Unit, Department, EmployeeMaster

logger = logging.getLogger(__name__)


def get_units(request):
    """
    AJAX: Get all active units
    Returns: JSON with units list
    """
    try:
        units = Unit.objects.filter(is_active=True).order_by('code')
        units_list = []
        for unit in units:
            units_list.append({
                'id': unit.id,
                'code': unit.code,
                'name': unit.full_name or unit.code,
                'full_name': unit.full_name or unit.code
            })
        return JsonResponse({
            'units': units_list, 
            'success': True,
            'count': len(units_list)
        })
    except Exception as e:
        logger.error(f"Error in get_units: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'units': []
        })


def get_departments_by_unit(request):
    """
    AJAX: Get departments for a specific unit
    Query params: unit_id (optional)
    Returns: JSON with departments list
    """
    unit_id = request.GET.get('unit_id')
    
    try:
        if unit_id:
            departments = Department.objects.filter(unit_id=unit_id, is_active=True).order_by('name')
        else:
            departments = Department.objects.filter(is_active=True).order_by('name')
        
        departments_list = []
        for dept in departments:
            departments_list.append({
                'id': dept.id,
                'name': dept.name,
                'unit_id': dept.unit_id
            })
        
        return JsonResponse({
            'success': True,
            'departments': departments_list,
            'count': len(departments_list)
        })
    except Exception as e:
        logger.error(f"Error in get_departments_by_unit: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'departments': []
        })


def get_employee_details(request):
    """
    AJAX: Get employee details by Employee ID
    Query params: employee_id, unit_id, department_id (for validation)
    Returns: JSON with employee data or error message
    """
    eid = request.GET.get('employee_id', '').strip().upper()
    u_uid = request.GET.get('unit_id', '')
    u_did = request.GET.get('department_id', '')
    
    if not eid: 
        return JsonResponse({
            'found': False, 
            'message': 'Please enter an Employee ID.'
        })
    
    try:
        emp = EmployeeMaster.objects.get(employee_id=eid, is_active=True)
        
        mismatches = []
        if u_uid and emp.unit_id and str(emp.unit_id) != str(u_uid):
            mismatches.append(f'Unit: {emp.unit.code if emp.unit else "Unknown"} (expected: {u_uid})')
        if u_did and emp.department_id and str(emp.department_id) != str(u_did):
            mismatches.append(f'Department: {emp.department.name if emp.department else "Unknown"} (expected: {u_did})')
        
        if mismatches:
            return JsonResponse({
                'found': False, 
                'message': f'Employee belongs to different department/unit: {", ".join(mismatches)}',
                'mismatch': True,
                'employee': {
                    'employee_id': emp.employee_id,
                    'employee_name': emp.employee_name,
                    'mobile': emp.mobile,
                    'email': emp.email,
                    'unit_id': emp.unit_id or None,
                    'unit_code': emp.unit.code if emp.unit else None,
                    'department_id': emp.department_id or None,
                    'department_name': emp.department.name if emp.department else None
                }
            })
        
        return JsonResponse({
            'found': True,
            'employee': {
                'employee_id': emp.employee_id,
                'employee_name': emp.employee_name,
                'mobile': emp.mobile,
                'email': emp.email,
                'unit_id': emp.unit_id or None,
                'unit_code': emp.unit.code if emp.unit else None,
                'department_id': emp.department_id or None,
                'department_name': emp.department.name if emp.department else None
            }
        })
    except EmployeeMaster.DoesNotExist:
        return JsonResponse({
            'found': False, 
            'message': f'Employee "{eid}" not found.'
        })
    except Exception as e:
        logger.error(f"Error in get_employee_details: {str(e)}")
        return JsonResponse({
            'found': False, 
            'message': 'Error fetching employee details.'
        })


def get_employees_by_department(request):
    """
    AJAX: Get all employees for a department
    Query params: department_id
    Returns: JSON with employee list, count, and department info
    """
    dept_id = request.GET.get('department_id')
    
    if not dept_id:
        return JsonResponse({
            'success': False, 
            'message': 'Department ID is required'
        })
    
    try:
        department = Department.objects.get(id=dept_id, is_active=True)
        employees = EmployeeMaster.objects.filter(
            department=department
        ).order_by('employee_id')
        
        employee_list = []
        for emp in employees:
            employee_list.append({
                'id': emp.id,
                'employee_id': emp.employee_id or '-',
                'employee_name': emp.employee_name or '-',
                'mobile': emp.mobile or '-',
                'email': emp.email or '-',
                'is_active': emp.is_active,
                'can_assign_ticket': emp.can_assign_ticket
            })
        
        return JsonResponse({
            'success': True,
            'department_name': department.name,
            'department_id': department.id,
            'employees': employee_list,
            'count': len(employee_list)
        })
        
    except Department.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Department not found'
        })
    except Exception as e:
        logger.error(f"Error in get_employees_by_department: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })