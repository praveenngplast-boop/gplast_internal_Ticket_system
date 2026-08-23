# tickets/views/ajax_views.py
"""
AJAX Endpoints for dynamic content loading
- Get Units
- Get Departments by Unit
- Get Employee Details (with ERP User ID)
- Get Employees by Department
- Get Ticket Statistics
- Get Closed Tickets
- Get Error Type Statistics
"""
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import logging

from tickets.models import Unit, Department, EmployeeMaster, Ticket, ERPHolderMapping

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


# ============================================================
# ✅ UPDATED: EMPLOYEE DETAILS WITH ERP USER ID
# ============================================================
def get_employee_details(request):
    """
    AJAX: Get employee details by Employee ID with ERP User ID
    Query params: employee_id (required), unit_id (optional), department_id (optional)
    Returns: JSON with employee details including erp_user_id
    """
    eid = request.GET.get('employee_id', '').strip().upper()
    u_uid = request.GET.get('unit_id', '')
    u_did = request.GET.get('department_id', '')
    
    if not eid: 
        return JsonResponse({
            'found': False, 
            'mismatch': False,
            'message': 'Please enter an Employee ID.'
        })
    
    try:
        # Find the employee
        emp = EmployeeMaster.objects.get(employee_id=eid, is_active=True)
        
        # ✅ NEW: Get ERP User ID from ERPHolderMapping
        erp_mapping = ERPHolderMapping.objects.filter(employee=emp).first()
        erp_user_id = erp_mapping.erp_user_id if erp_mapping else None
        
        # Prepare employee data with ERP User ID
        emp_data = {
            'employee_id': emp.employee_id,
            'employee_name': emp.employee_name,
            'mobile': emp.mobile,
            'email': emp.email,
            'unit_id': emp.unit_id or None,
            'unit_code': emp.unit.code if emp.unit else None,
            'department_id': emp.department_id or None,
            'department_name': emp.department.name if emp.department else None,
            'erp_user_id': erp_user_id,  # ✅ NEW: ERP User ID
        }
        
        # Check if unit/department validation is required
        if u_uid and u_did:
            try:
                u_uid = int(u_uid)
                u_did = int(u_did)
            except (ValueError, TypeError):
                pass
            
            unit_match = (emp.unit_id == u_uid) if emp.unit_id else False
            dept_match = (emp.department_id == u_did) if emp.department_id else False
            
            mismatches = []
            
            if not unit_match:
                mismatches.append(f'Unit: {emp.unit.code if emp.unit else "None"}')
            if not dept_match:
                mismatches.append(f'Department: {emp.department.name if emp.department else "None"}')
            
            if mismatches:
                return JsonResponse({
                    'found': True,
                    'mismatch': True,
                    'employee': emp_data,
                    'message': f'⚠️ Employee belongs to different {", ".join(mismatches)}'
                })
        
        # Employee found and matches (or no validation required)
        return JsonResponse({
            'found': True,
            'mismatch': False,
            'employee': emp_data,
            'message': '✅ Employee verified successfully!'
        })
        
    except EmployeeMaster.DoesNotExist:
        return JsonResponse({
            'found': False, 
            'mismatch': False,
            'message': f'❌ Employee "{eid}" not found. Please check and try again.'
        })
    except Exception as e:
        logger.error(f"Error in get_employee_details: {str(e)}")
        return JsonResponse({
            'found': False, 
            'mismatch': False,
            'message': 'Error fetching employee details.'
        })


def get_employees_by_department(request):
    """
    AJAX: Get all employees for a department with ERP User ID
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
            # ✅ NEW: Get ERP User ID for each employee
            erp_mapping = ERPHolderMapping.objects.filter(employee=emp).first()
            erp_user_id = erp_mapping.erp_user_id if erp_mapping else None
            
            employee_list.append({
                'id': emp.id,
                'employee_id': emp.employee_id or '-',
                'employee_name': emp.employee_name or '-',
                'mobile': emp.mobile or '-',
                'email': emp.email or '-',
                'is_active': emp.is_active,
                'can_assign_ticket': emp.can_assign_ticket,
                'erp_user_id': erp_user_id,  # ✅ NEW: ERP User ID
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


# ============================================================
# TICKET STATISTICS
# ============================================================

def get_ticket_statistics(request):
    """
    AJAX: Get ticket statistics for dashboard
    Returns: JSON with ticket counts
    """
    try:
        total = Ticket.objects.count()
        open_count = Ticket.objects.filter(status='Open').count()
        assigned_count = Ticket.objects.filter(status='Assigned').count()
        hold_count = Ticket.objects.filter(status='Hold').count()
        escalated_count = Ticket.objects.filter(status='Escalated').count()
        closed_count = Ticket.objects.filter(status='Closed').count()
        
        critical_count = Ticket.objects.filter(priority='Critical').count()
        high_count = Ticket.objects.filter(priority='High').count()
        medium_count = Ticket.objects.filter(priority='Medium').count()
        low_count = Ticket.objects.filter(priority='Low').count()
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        closed_30_days = Ticket.objects.filter(
            status='Closed',
            closed_at__gte=thirty_days_ago
        ).count()
        
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = Ticket.objects.filter(created_at__gte=today_start).count()
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total': total,
                'open': open_count,
                'assigned': assigned_count,
                'hold': hold_count,
                'escalated': escalated_count,
                'closed': closed_count,
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count,
                'low': low_count,
                'closed_30_days': closed_30_days,
                'today': today_count,
            }
        })
    except Exception as e:
        logger.error(f"Error in get_ticket_statistics: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_closed_tickets_30_days(request):
    """
    AJAX: Get closed tickets from last 30 days
    Query params: limit (optional, default 50)
    """
    try:
        limit = int(request.GET.get('limit', 50))
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        tickets = Ticket.objects.filter(
            status='Closed',
            closed_at__gte=thirty_days_ago
        ).order_by('-closed_at')[:limit]
        
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'employee_name': ticket.employee_name,
                'employee_id': ticket.employee_id,
                'unit': ticket.unit.code if ticket.unit else '',
                'department': ticket.department.name if ticket.department else '',
                'priority': ticket.priority,
                'closed_at': ticket.closed_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_at else '',
                'closed_by': ticket.closed_by or '',
                'closing_remarks': ticket.closing_remarks or '',
                'main_error_type': ticket.main_error_type or 'N/A',
                'sub_error_type': ticket.sub_error_type or 'N/A',
                'error_type_display': f"{ticket.main_error_type} → {ticket.sub_error_type}" if ticket.main_error_type and ticket.sub_error_type else (ticket.main_error_type or ticket.error_type or 'Not Set'),
                'url': f'/admin/ticket/{ticket.id}/'
            })
        
        return JsonResponse({
            'success': True,
            'tickets': ticket_list,
            'count': len(ticket_list),
            'total': Ticket.objects.filter(
                status='Closed',
                closed_at__gte=thirty_days_ago
            ).count()
        })
    except Exception as e:
        logger.error(f"Error in get_closed_tickets_30_days: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_error_type_statistics(request):
    """
    AJAX: Get error type statistics for closed tickets
    """
    try:
        closed_tickets = Ticket.objects.filter(status='Closed')
        
        main_error_stats = (
            closed_tickets
            .exclude(main_error_type__isnull=True)
            .exclude(main_error_type__exact='')
            .values('main_error_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        sub_error_stats = (
            closed_tickets
            .exclude(sub_error_type__isnull=True)
            .exclude(sub_error_type__exact='')
            .values('sub_error_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        roadmap_count = closed_tickets.filter(main_error_type='Roadmap Error').count()
        gpl_count = closed_tickets.filter(main_error_type='GPL Error').count()
        
        total_with_error = closed_tickets.exclude(
            main_error_type__isnull=True
        ).exclude(
            main_error_type__exact=''
        ).count()
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'main_errors': list(main_error_stats),
                'sub_errors': list(sub_error_stats),
                'roadmap_count': roadmap_count,
                'gpl_count': gpl_count,
                'total_with_error': total_with_error,
                'total_closed': closed_tickets.count(),
            }
        })
    except Exception as e:
        logger.error(f"Error in get_error_type_statistics: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_ticket_by_number(request):
    """
    AJAX: Get ticket details by ticket number
    Query params: ticket_number
    """
    ticket_number = request.GET.get('ticket_number', '').strip()
    
    if not ticket_number:
        return JsonResponse({
            'success': False,
            'message': 'Ticket number is required'
        })
    
    try:
        ticket = Ticket.objects.get(ticket_number=ticket_number)
        
        return JsonResponse({
            'success': True,
            'ticket': {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status,
                'priority': ticket.priority,
                'employee_name': ticket.employee_name,
                'employee_id': ticket.employee_id,
                'unit': ticket.unit.code if ticket.unit else '',
                'department': ticket.department.name if ticket.department else '',
                'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'closed_at': ticket.closed_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.closed_at else '',
                'main_error_type': ticket.main_error_type or 'N/A',
                'sub_error_type': ticket.sub_error_type or 'N/A',
                'error_type': ticket.error_type or 'Not Set',
                'closing_remarks': ticket.closing_remarks or '',
                'closed_by': ticket.closed_by or '',
                'url': f'/admin/ticket/{ticket.id}/'
            }
        })
    except Ticket.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Ticket #{ticket_number} not found'
        })
    except Exception as e:
        logger.error(f"Error in get_ticket_by_number: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def search_tickets_ajax(request):
    """
    AJAX: Search tickets across ALL history
    Query params: query, limit (optional)
    """
    query = request.GET.get('query', '').strip()
    limit = int(request.GET.get('limit', 20))
    
    if not query:
        return JsonResponse({
            'success': True,
            'tickets': [],
            'count': 0,
            'message': 'No search query provided'
        })
    
    try:
        tickets = Ticket.objects.filter(
            Q(ticket_number__icontains=query) |
            Q(subject__icontains=query) |
            Q(employee_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(unit__code__icontains=query) |
            Q(department__name__icontains=query) |
            Q(description__icontains=query)
        ).order_by('-created_at')[:limit]
        
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'employee_name': ticket.employee_name,
                'status': ticket.status,
                'priority': ticket.priority,
                'unit': ticket.unit.code if ticket.unit else '',
                'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'main_error_type': ticket.main_error_type or 'N/A',
                'sub_error_type': ticket.sub_error_type or 'N/A',
                'error_type_display': f"{ticket.main_error_type} → {ticket.sub_error_type}" if ticket.main_error_type and ticket.sub_error_type else (ticket.main_error_type or ticket.error_type or 'Not Set'),
                'url': f'/admin/ticket/{ticket.id}/'
            })
        
        return JsonResponse({
            'success': True,
            'tickets': ticket_list,
            'count': len(ticket_list),
            'total_matching': Ticket.objects.filter(
                Q(ticket_number__icontains=query) |
                Q(subject__icontains=query) |
                Q(employee_name__icontains=query) |
                Q(employee_id__icontains=query) |
                Q(unit__code__icontains=query) |
                Q(department__name__icontains=query) |
                Q(description__icontains=query)
            ).count()
        })
    except Exception as e:
        logger.error(f"Error in search_tickets_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })