# tickets/views/settings_action/__init__.py

from .contact import settings_contact
from .units import (
    settings_units,
    settings_departments,
    departments_bulk_upload,
    departments_download_template,
)
from .emails import settings_emails
from .settings_password import settings_passwords
from .employees import (
    settings_employees,
    download_employee_list,
    download_employee_template,
)
from .credentials import (
    settings_credentials,
    download_credentials,
    credentials_bulk_upload,
    credentials_download_template,
)
from .screen_master import (
    screen_master_add,
    screen_master_edit,
    screen_master_delete,
    screen_master_download_excel,
    screen_master_download_template,
    screen_master_bulk_upload,
)
from .screen_mapping import (
    screen_mapping_add,
    screen_mapping_remove,
    screen_mapping_delete_erp,
    screen_mapping_export_excel,
    settings_screen_mapping_page,
    ajax_get_screens_for_erp,
    screen_mapping_bulk_upload,
    screen_mapping_download_template,
)

# Unit Head Management Actions
from .unit_heads import (
    settings_unit_heads_page,
    settings_unit_heads,
)

# ERP Mapping Views
from .erp_mapping_views import (
    erp_mapping_page,
    erp_mapping_add,
    erp_mapping_remove,
    erp_mapping_unmap,
    erp_mapping_export_excel,
    erp_mapping_bulk_upload,
    erp_mapping_download_template,
    erp_mapping_list,
    erp_mapping_search_employees,
)

__all__ = [
    # Contact
    'settings_contact',
    
    # Units
    'settings_units',
    'settings_departments',
    'departments_bulk_upload',
    'departments_download_template',
    
    # Emails
    'settings_emails',
    
    # Passwords
    'settings_passwords',
    
    # Employees
    'settings_employees',
    'download_employee_list',
    'download_employee_template',
    
    # Credentials
    'settings_credentials',
    'download_credentials',
    'credentials_bulk_upload',
    'credentials_download_template',
    
    # Screen Master
    'screen_master_add',
    'screen_master_edit',
    'screen_master_delete',
    'screen_master_download_excel',
    'screen_master_download_template',
    'screen_master_bulk_upload',
    
    # Screen Mapping
    'screen_mapping_add',
    'screen_mapping_remove',
    'screen_mapping_delete_erp',
    'screen_mapping_export_excel',
    'settings_screen_mapping_page',
    'ajax_get_screens_for_erp',
    'screen_mapping_bulk_upload',
    'screen_mapping_download_template',
    
    # Unit Head Management
    'settings_unit_heads_page',
    'settings_unit_heads',
    
    # ERP USER ID MAPPING
    'erp_mapping_page',
    'erp_mapping_add',
    'erp_mapping_remove',
    'erp_mapping_unmap',
    'erp_mapping_export_excel',
    'erp_mapping_bulk_upload',
    'erp_mapping_download_template',
    'erp_mapping_list',
    'erp_mapping_search_employees',
]