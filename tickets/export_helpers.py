# tickets/export_helpers.py

from django.utils import timezone
from openpyxl.styles import Alignment, Font, PatternFill


def add_replies_sheet(workbook, tickets_queryset):
    """
    Add a sheet with all ticket replies to the workbook.
    
    Args:
        workbook: The openpyxl workbook object
        tickets_queryset: QuerySet of tickets to include replies for
    
    Returns:
        None (modifies workbook in place)
    """
    worksheet = workbook.create_sheet('Ticket Replies')
    headers = ['Ticket Number', 'Timestamp', 'Sender', 'Role', 'Reply', 'Attachment']
    worksheet.append(headers)

    # Style the header row
    header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    for cell in worksheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # ✅ FIX 1: Add chunk_size parameter to iterator()
    # This resolves the ValueError when using prefetch_related with iterator
    for reply in tickets_queryset.prefetch_related('replies').order_by('created_at').values_list(
        'id', 'ticket_number'
    ).iterator(chunk_size=2000):  # ✅ Added chunk_size=2000
        ticket_id, ticket_number = reply
        for ticket_reply in tickets_queryset.model.objects.get(pk=ticket_id).replies.all():
            worksheet.append([
                ticket_number,
                timezone.localtime(ticket_reply.created_at).strftime('%d-%b-%Y %I:%M %p'),
                ticket_reply.author_name,
                ticket_reply.author_role,
                ticket_reply.body,
                ticket_reply.attachment.name if ticket_reply.attachment else '',
            ])

    # Set column widths
    widths = [20, 23, 24, 16, 60, 35]
    for index, width in enumerate(widths, 1):
        worksheet.column_dimensions[chr(64 + index)].width = width
    
    # Freeze the header row
    worksheet.freeze_panes = 'A2'


def add_replies_sheet_optimized(workbook, tickets_queryset):
    """
    Optimized version that uses a single query for all replies.
    This is more efficient for large datasets.
    
    Args:
        workbook: The openpyxl workbook object
        tickets_queryset: QuerySet of tickets to include replies for
    
    Returns:
        None (modifies workbook in place)
    """
    from tickets.models import TicketReply
    
    worksheet = workbook.create_sheet('Ticket Replies')
    headers = ['Ticket Number', 'Timestamp', 'Sender', 'Role', 'Reply', 'Attachment']
    worksheet.append(headers)

    # Style the header row
    header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    for cell in worksheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # ✅ FIX 2: Optimized approach - get all replies in one query
    # This is much more efficient than the N+1 query approach
    ticket_ids = tickets_queryset.values_list('id', flat=True)
    
    if ticket_ids:
        replies = TicketReply.objects.filter(
            ticket__in=ticket_ids
        ).select_related('ticket').order_by('ticket__ticket_number', 'created_at')
        
        # ✅ Add chunk_size here too
        for reply in replies.iterator(chunk_size=2000):
            worksheet.append([
                reply.ticket.ticket_number,
                timezone.localtime(reply.created_at).strftime('%d-%b-%Y %I:%M %p'),
                reply.author_name,
                reply.author_role,
                reply.body,
                reply.attachment.name if reply.attachment else '',
            ])

    # Set column widths
    widths = [20, 23, 24, 16, 60, 35]
    for index, width in enumerate(widths, 1):
        worksheet.column_dimensions[chr(64 + index)].width = width
    
    # Freeze the header row
    worksheet.freeze_panes = 'A2'


def append_replies_section(worksheet, row, ticket, section_font, header_font, data_font, section_fill, header_fill, border):
    """
    Append a replies section to an existing worksheet for a single ticket.
    
    Args:
        worksheet: The openpyxl worksheet object
        row: The starting row number
        ticket: The ticket object
        section_font: Font for section header
        header_font: Font for column headers
        data_font: Font for data rows
        section_fill: Fill for section header
        header_fill: Fill for column headers
        border: Border style for cells
    
    Returns:
        int: The next row number after the replies section
    """
    # Section header
    worksheet.merge_cells(f'A{row}:F{row}')
    worksheet[f'A{row}'] = 'REPLIES'
    worksheet[f'A{row}'].font = section_font
    worksheet[f'A{row}'].fill = section_fill
    worksheet[f'A{row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    row += 1

    # Column headers
    headers = ['Timestamp', 'Sender', 'Role', 'Reply', 'Attachment']
    for column, header in enumerate(headers, 1):
        cell = worksheet.cell(row=row, column=column, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')
    row += 1

    # Reply data rows
    for reply in ticket.replies.all().order_by('created_at'):
        values = [
            timezone.localtime(reply.created_at).strftime('%d-%b-%Y %I:%M %p'),
            reply.author_name,
            reply.author_role,
            reply.body,
            reply.attachment.name if reply.attachment else '',
        ]
        for column, value in enumerate(values, 1):
            cell = worksheet.cell(row=row, column=column, value=value)
            cell.font = data_font
            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        row += 1

    return row + 1

