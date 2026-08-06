# GPLAST ERP IT Support Ticket System

A full-stack IT & ERP support ticketing system built with **Django 4.x** and **MySQL**. The app provides a modern employee experience plus an admin operations panel for ticket lifecycle management, reporting, and system configuration.

---

## 🌟 Project Overview

GPLAST ERP IT Support Ticket System is designed for internal use by employees and administrators. It enables:
- Employee ticket creation with file attachments
- Admin ticket assignment, hold, escalation, and closure
- Master data management for Units and Departments
- Configurable notification email list
- Dashboard analytics and Excel export reporting
- Light/dark UI support for improved usability
- Hierarchical department-employee view with real-time search
- Bulk employee upload via Excel files
- Unit-wise credential management

The codebase is intentionally database-agnostic at the ORM level, with MySQL as the default backend and potential compatibility for other relational databases.

---

## 🧩 Tech Stack

- Python 3.11+ (or compatible 3.x)
- Django 4.2.x
- MySQL / MariaDB
- `mysqlclient` and `PyMySQL`
- `python-decouple` for environment settings
- `openpyxl` for Excel export
- `Pillow` for image/file handling
- `whitenoise` for static file delivery
- Bootstrap 5 for responsive UI
- FontAwesome for icons
- Chart.js for dashboard visualizations

---

## 🚀 Main Features

### Authentication & Authorization
- Single login screen for both employees and admins
- Role-based redirect:
  - Admin users access the Admin Panel
  - Employee users access the Employee Portal
- Custom logout and role redirect flows

### Employee Portal
- Create tickets with required fields and file attachment support
- View all tickets created by the logged-in employee
- Search and filter tickets by status, priority, ticket number, text, and dates
- View ticket history and current status
- View and update personal profile information

### Admin Panel
- Full ticket list with status, priority, unit, department, and ticket number filters
- Advanced search with ticket number, search text, and date range filtering
- Ticket detail workflow for Assign / Hold / Escalate / Close
- Admin ticket creation on behalf of employees
- View ticket history logs and audit trail

### Ticket Lifecycle & Status Management
- Managed statuses: `Open`, `Assigned`, `Hold`, `Escalated`, `Closed`
- Assigned tickets require assigned person input
- Hold tickets require hold reason input
- Escalated tickets store vendor ticket number and escalation timestamp
- Closed tickets capture closing remarks, error type, and closed timestamp

### Master Data Management
- Manage Units and Departments in Admin Settings
- Soft delete for Units and Departments via `is_active` flags
- Auto-uppercase unit codes, unit names, and department names on save
- Deactivate units and departments without deleting ticket history
- Hierarchical tree view for department-employee visualization

### Employee Management
- Add employees manually with validation
- Bulk upload employees via Excel files (`.xlsx`, `.xls`)
- Download employee list as Excel
- Download template for bulk upload
- Edit and toggle employee status
- View employees by department in hierarchical tree view
- Real-time search across departments and employees

### Credential Management
- Unit-wise credential storage for department access
- Store username and password for each department
- Toggle credential active/inactive status
- Download all credentials as Excel
- Edit and delete credentials

### Communication & Notifications
- Helpdesk contact management (name and email)
- Configurable notification email list for ticket alerts
- Ticket email notifications for creation and closure
- Sends email to the employee and configured admin notification emails
- Admin email list managed from the settings page

### Reporting & Export
- Admin Reports page with filterable ticket exports
- Export to Excel `.xlsx` via `openpyxl`
- Includes ticket metadata, status, dates, comments, and vendor references
- Download employee list and credentials as Excel

### Dashboard & Analytics
- KPI summary cards for open, assigned, hold, escalated, closed, and critical tickets
- Dashboard visualizations powered by Chart.js
- Light/dark theme support for consistency across pages

### UI & UX Enhancements
- Responsive Bootstrap layout for desktop and mobile
- Light/dark theme support with CSS variables
- Clear filters and advanced filter panels on ticket list pages
- Confirmation prompts for destructive actions
- Toast notifications for user feedback
- Hierarchical tree view for department navigation
- Real-time search filtering
- Animated transitions and interactions

---

## 📁 Project Structure

```
gplast_ticket_system/
├── manage.py                           # Django entrypoint
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
├── gplast_ticket/                      # Project settings
│   ├── __init__.py
│   ├── settings.py                     # Django settings
│   ├── urls.py                         # Main URL routing
│   ├── wsgi.py
│   └── asgi.py
├── tickets/                            # Main application
│   ├── __init__.py
│   ├── admin.py                        # Django admin configuration
│   ├── models.py                       # Database models
│   │   ├── Unit                        # Organizational units
│   │   ├── Department                  # Departments under units
│   │   ├── Employee                    # Employee profiles
│   │   ├── Ticket                      # Support tickets
│   │   ├── TicketHistory               # Ticket audit trail
│   │   ├── EmailNotification           # Notification emails
│   │   ├── HelpdeskContact             # Helpdesk contact info
│   │   └── DepartmentCredential        # Department credentials
│   ├── views.py                        # View controllers
│   │   ├── employee_views.py           # Employee portal views
│   │   ├── admin_views.py              # Admin panel views
│   │   ├── settings_views.py           # Settings management views
│   │   ├── reports_views.py            # Reports and exports
│   │   └── ajax_views.py               # AJAX endpoints
│   ├── forms.py                        # Form definitions
│   ├── urls.py                         # App URL routing
│   ├── decorators.py                   # Custom decorators
│   ├── utils.py                        # Utility functions
│   ├── context_processors.py           # Global context processors
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py            # Seed data command
│   ├── templates/                      # HTML templates
│   │   ├── base.html                   # Base template
│   │   ├── auth/                       # Authentication templates
│   │   │   ├── login.html
│   │   │   └── logout.html
│   │   ├── admin_panel/                # Admin panel templates
│   │   │   ├── dashboard.html
│   │   │   ├── tickets.html
│   │   │   ├── ticket_detail.html
│   │   │   ├── create_ticket.html
│   │   │   ├── reports.html
│   │   │   ├── settings.html
│   │   │   └── profile.html
│   │   ├── employee_portal/            # Employee portal templates
│   │   │   ├── dashboard.html
│   │   │   ├── tickets.html
│   │   │   ├── create_ticket.html
│   │   │   └── profile.html
│   │   ├── includes/                   # Reusable components
│   │   │   ├── navbar.html
│   │   │   ├── sidebar.html
│   │   │   ├── footer.html
│   │   │   └── theme_toggle.html
│   │   └── emails/                     # Email templates
│   │       ├── ticket_creation.html
│   │       └── ticket_closure.html
│   └── static/                         # Static files
│       ├── css/
│       │   ├── style.css
│       │   └── theme.css
│       ├── js/
│       │   ├── main.js
│       │   ├── theme.js
│       │   └── dashboard.js
│       └── images/
│           ├── logo.png
│           └── favicon.ico
├── media/                              # User-uploaded files
│   └── ticket_attachments/
├── logs/                               # Application logs
└── scripts/                            # Utility scripts
    └── backup_db.py
```

---

## 🛠 Installation

### Prerequisites
- Python 3.11+
- MySQL Server 8.x or compatible
- Git (optional)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/gplast_ticket_system.git
cd gplast_ticket_system

# Create and activate virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env` and update values:
```ini
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.yourdomain.com

# Database Settings
DB_NAME=gplast_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=3306

# Email Settings (Optional - Console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# For production:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.office365.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=support@gplast.com
# EMAIL_HOST_PASSWORD=your-email-password
# DEFAULT_FROM_EMAIL=GPLAST Support <support@gplast.com>

# App Settings
TIME_ZONE=Asia/Kolkata
LANGUAGE_CODE=en-in
```

### Database Setup
```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE gplast_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed initial data
python manage.py seed_data
```

### Static Files
```bash
python manage.py collectstatic
```

### Run Locally
```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## ⚙️ Default Accounts

After running `seed_data`, the following default accounts are created:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| employee1 | emp123 | Employee |
| employee2 | emp123 | Employee |

**Note:** Change default passwords immediately in production.

---

## 📦 Dependencies

Current dependencies in `requirements.txt`:
```
Django>=4.2,<5.1
mysqlclient>=2.1.0
openpyxl>=3.1.0
Pillow>=10.0.0
python-decouple>=3.8
whitenoise>=6.5.0
PyMySQL>=1.1.0
```

---

## 📧 Email Alerts Configuration

To enable email alerts for ticket creations and closures:

```ini
# In .env file
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=support@gplast.com
EMAIL_HOST_PASSWORD=SecureMailPassword123
DEFAULT_FROM_EMAIL=GPLAST Support <support@gplast.com>
```

The system sends emails to:
- Ticket creator (employee)
- Configured admin notification emails (managed in settings page)

---

## 🔒 Security Notes
- Uses Django authentication and session middleware
- CSRF protection enabled on all forms
- Uses Django ORM for SQL injection prevention
- File uploads restricted by allowed extensions and max size (5MB)
- Password hashing with Django's default PBKDF2
- HTTPS recommended for production deployment
- Environment variables for sensitive configuration

---

## 📊 API Endpoints (AJAX)

The system provides AJAX endpoints for dynamic content:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ajax/get-departments/` | GET | Get departments by unit ID |
| `/ajax/get-employees-by-department/` | GET | Get employees by department ID |
| `/ajax/update-ticket-status/` | POST | Update ticket status |
| `/ajax/dashboard-stats/` | GET | Get dashboard statistics |

---

## ✅ Validation & Testing

Run app checks and tests:
```bash
# Check for common issues
python manage.py check

# Run tests
python manage.py test

# Run specific test
python manage.py test tickets.tests.test_models
```

---

## 📌 Future Improvements

- [ ] Role-based permissions beyond `is_staff`
- [ ] Ticket comments and attachments gallery
- [ ] Pagination for ticket lists
- [ ] REST API support for external integration
- [ ] Two-factor authentication (2FA)
- [ ] Real-time notifications via WebSockets
- [ ] Mobile application (React Native)
- [ ] Advanced reporting with charts and graphs
- [ ] Automated ticket escalation rules
- [ ] SLA management and tracking
- [ ] Knowledge base for common issues
- [ ] Integration with external ITSM tools

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

## 📞 Support

For support, email:
- **IT Support**: support@gplast.com
- **Development Team**: dev@gplast.com

---

## 🏢 About GPLAST

GPLAST is a leading manufacturer of plastic products, committed to innovation and quality. This internal IT support system is part of our digital transformation initiative to streamline operations and improve employee experience.

---

## 📝 Changelog

### Version 2.0.0 (Current)
- Added hierarchical department-employee tree view
- Added bulk employee upload via Excel
- Added unit-wise credential management
- Added real-time search and filtering
- Added toast notification system
- Improved dark/light theme support
- Added employee profile management
- Enhanced reporting exports

### Version 1.0.0
- Initial release
- Basic ticket management
- Employee and admin portals
- Email notifications
- Dashboard analytics