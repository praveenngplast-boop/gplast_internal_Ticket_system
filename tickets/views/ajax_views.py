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
- ✅ NEW: Get Unit Head Details
- ✅ NEW: Get Unit Dashboard Stats
- ✅ NEW: Get Unit Tickets
"""
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import logging

from tickets.models import Unit, Department, EmployeeMaster, Ticket, ERPHolderMapping, UnitHead

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
# ✅ FIXED: EMPLOYEE DETAILS WITH ERP USER ID
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
        
        # ✅ Get ERP User ID from ERPHolderMapping
        erp_mapping = ERPHolderMapping.objects.filter(employee=emp).first()
        erp_user_id = erp_mapping.erp_user_id if erp_mapping else None
        
        # ✅ FIXED: Check if this employee's email matches a Unit Head
        # UnitHead has 'user' field (ForeignKey to User), not 'employee'
        is_unit_head = False
        unit_head_data = None
        
        if emp.email:
            # Check if there's a UnitHead with a user having this email
            unit_head = UnitHead.objects.filter(
                email=emp.email,
                is_active=True
            ).first()
            
            if unit_head:
                is_unit_head = True
                unit_head_data = {
                    'name': unit_head.name,
                    'email': unit_head.email,
                    'is_active': unit_head.is_active,
                    'unit_id': unit_head.unit_id,
                    'unit_code': unit_head.unit.code if unit_head.unit else '',
                }
        
        # Prepare employee data with ERP User ID and Unit Head info
        emp_data = {
            'employee_id': emp.employee_id,
            'employee_name': emp.employee_name,
            'mobile': emp.mobile,
            'email': emp.email,
            'unit_id': emp.unit_id or None,
            'unit_code': emp.unit.code if emp.unit else None,
            'department_id': emp.department_id or None,
            'department_name': emp.department.name if emp.department else None,
            'erp_user_id': erp_user_id,
            'is_unit_head': is_unit_head,
            'unit_head_data': unit_head_data,
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
            # ✅ Get ERP User ID for each employee
            erp_mapping = ERPHolderMapping.objects.filter(employee=emp).first()
            erp_user_id = erp_mapping.erp_user_id if erp_mapping else None
            
            # ✅ FIXED: Check if employee's email matches a Unit Head
            is_unit_head = False
            if emp.email:
                is_unit_head = UnitHead.objects.filter(
                    email=emp.email,
                    is_active=True
                ).exists()
            
            employee_list.append({
                'id': emp.id,
                'employee_id': emp.employee_id or '-',
                'employee_name': emp.employee_name or '-',
                'mobile': emp.mobile or '-',
                'email': emp.email or '-',
                'is_active': emp.is_active,
                'can_assign_ticket': emp.can_assign_ticket,
                'erp_user_id': erp_user_id,
                'is_unit_head': is_unit_head,
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
# ✅ NEW: GET UNIT HEAD DETAILS
# ============================================================
def get_unit_head_details(request):
    """
    AJAX: Get Unit Head details for a specific unit
    Query params: unit_id
    Returns: JSON with Unit Head details
    """
    unit_id = request.GET.get('unit_id')
    
    if not unit_id:
        return JsonResponse({
            'success': False,
            'message': 'Unit ID is required'
        })
    
    try:
        unit_head = UnitHead.objects.filter(unit_id=unit_id, is_active=True).first()
        
        if unit_head:
            return JsonResponse({
                'success': True,
                'found': True,
                'unit_head': {
                    'id': unit_head.id,
                    'name': unit_head.name,
                    'email': unit_head.email,
                    'unit_id': unit_head.unit_id,
                    'unit_code': unit_head.unit.code if unit_head.unit else '',
                    'user_id': unit_head.user_id,
                    'username': unit_head.user.username if unit_head.user else '',
                    'is_active': unit_head.is_active,
                    'created_at': unit_head.created_at.strftime('%Y-%m-%d %H:%M:%S') if unit_head.created_at else '',
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'found': False,
                'message': 'No Unit Head assigned to this unit'
            })
            
    except Exception as e:
        logger.error(f"Error in get_unit_head_details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================================
# ✅ NEW: GET UNIT DASHBOARD STATS
# ============================================================
def get_unit_dashboard_stats(request):
    """
    AJAX: Get dashboard statistics for a specific unit
    Query params: unit_id
    Returns: JSON with ticket statistics for the unit
    """
    unit_id = request.GET.get('unit_id')
    
    if not unit_id:
        return JsonResponse({
            'success': False,
            'message': 'Unit ID is required'
        })
    
    try:
        unit_tickets = Ticket.objects.filter(unit_id=unit_id)
        
        stats = {
            'total': unit_tickets.count(),
            'open': unit_tickets.filter(status='Open').count(),
            'assigned': unit_tickets.filter(status='Assigned').count(),
            'hold': unit_tickets.filter(status='Hold').count(),
            'escalated': unit_tickets.filter(status='Escalated').count(),
            'closed': unit_tickets.filter(status='Closed').count(),
            'critical': unit_tickets.filter(priority='Critical').count(),
            'high': unit_tickets.filter(priority='High').count(),
            'medium': unit_tickets.filter(priority='Medium').count(),
            'low': unit_tickets.filter(priority='Low').count(),
        }
        
        # Get Unit Head info
        unit_head = UnitHead.objects.filter(unit_id=unit_id, is_active=True).first()
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'unit_head': {
                'name': unit_head.name if unit_head else None,
                'email': unit_head.email if unit_head else None,
            } if unit_head else None
        })
        
    except Exception as e:
        logger.error(f"Error in get_unit_dashboard_stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================================
# ✅ NEW: GET UNIT TICKETS
# ============================================================
def get_unit_tickets_ajax(request):
    """
    AJAX: Get tickets for a specific unit with filters
    Query params: unit_id, status, priority, limit
    Returns: JSON with tickets list
    """
    unit_id = request.GET.get('unit_id')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    limit = int(request.GET.get('limit', 20))
    
    if not unit_id:
        return JsonResponse({
            'success': False,
            'message': 'Unit ID is required'
        })
    
    try:
        tickets_qs = Ticket.objects.filter(unit_id=unit_id)
        
        if status:
            tickets_qs = tickets_qs.filter(status=status)
        if priority:
            tickets_qs = tickets_qs.filter(priority=priority)
        
        tickets_qs = tickets_qs.order_by('-created_at')[:limit]
        
        ticket_list = []
        for ticket in tickets_qs:
            # Get ERP ID
            erp_id = 'Not Mapped'
            erp_mapping = ERPHolderMapping.objects.filter(
                employee__employee_id=ticket.employee_id
            ).first()
            if erp_mapping:
                erp_id = erp_mapping.erp_user_id
            
            ticket_list.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status,
                'priority': ticket.priority,
                'employee_name': ticket.employee_name,
                'employee_id': ticket.employee_id,
                'department': ticket.department.name if ticket.department else '',
                'erp_id': erp_id,
                'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'main_error_type': ticket.main_error_type or 'N/A',
                'sub_error_type': ticket.sub_error_type or 'N/A',
                'url': f'/unit-head/ticket/{ticket.id}/'
            })
        
        return JsonResponse({
            'success': True,
            'tickets': ticket_list,
            'count': len(ticket_list)
        })
        
    except Exception as e:
        logger.error(f"Error in get_unit_tickets_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
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
        
        # ✅ NEW: Get Unit Head count
        unit_head_count = UnitHead.objects.filter(is_active=True).count()
        
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
                'unit_heads': unit_head_count,
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
    Query params: limit (optional), unit_id (optional)
    """
    try:
        limit = int(request.GET.get('limit', 50))
        unit_id = request.GET.get('unit_id')
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        tickets_qs = Ticket.objects.filter(
            status='Closed',
            closed_at__gte=thirty_days_ago
        )
        
        # ✅ NEW: Filter by unit if provided
        if unit_id:
            tickets_qs = tickets_qs.filter(unit_id=unit_id)
        
        tickets = tickets_qs.order_by('-closed_at')[:limit]
        
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
            'total': tickets_qs.count()
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
    Query params: unit_id (optional)
    """
    try:
        closed_tickets = Ticket.objects.filter(status='Closed')
        
        # ✅ NEW: Filter by unit if provided
        unit_id = request.GET.get('unit_id')
        if unit_id:
            closed_tickets = closed_tickets.filter(unit_id=unit_id)
        
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
        
        # Get ERP ID
        erp_id = 'Not Mapped'
        erp_mapping = ERPHolderMapping.objects.filter(
            employee__employee_id=ticket.employee_id
        ).first()
        if erp_mapping:
            erp_id = erp_mapping.erp_user_id
        
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
                'erp_id': erp_id,
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
    Query params: query, limit (optional), unit_id (optional)
    """
    query = request.GET.get('query', '').strip()
    limit = int(request.GET.get('limit', 20))
    unit_id = request.GET.get('unit_id')
    
    if not query:
        return JsonResponse({
            'success': True,
            'tickets': [],
            'count': 0,
            'message': 'No search query provided'
        })
    
    try:
        tickets_qs = Ticket.objects.filter(
            Q(ticket_number__icontains=query) |
            Q(subject__icontains=query) |
            Q(employee_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(unit__code__icontains=query) |
            Q(department__name__icontains=query) |
            Q(description__icontains=query)
        )
        
        # ✅ NEW: Filter by unit if provided
        if unit_id:
            tickets_qs = tickets_qs.filter(unit_id=unit_id)
        
        tickets = tickets_qs.order_by('-created_at')[:limit]
        
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
            'total_matching': tickets_qs.count()
        })
    except Exception as e:
        logger.error(f"Error in search_tickets_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })