from .contact import settings_contact
from .units import settings_units, settings_departments
from .emails import settings_emails
from .settings_password import settings_passwords
from .employees import (
	settings_employees,
	download_employee_list,
	download_employee_template,
)
from .credentials import settings_credentials, download_credentials
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
)

__all__ = [
	'settings_contact',
	'settings_units',
	'settings_departments',
	'settings_emails',
	'settings_passwords',
	'settings_employees',
	'download_employee_list',
	'download_employee_template',
	'settings_credentials',
	'download_credentials',
	'screen_master_add',
	'screen_master_edit',
	'screen_master_delete',
	'screen_master_download_excel',
	'screen_master_download_template',
	'screen_master_bulk_upload',
	'screen_mapping_add',
	'screen_mapping_remove',
	'screen_mapping_delete_erp',
	'screen_mapping_export_excel',
	'settings_screen_mapping_page',
	'ajax_get_screens_for_erp',
]
 