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

### Reporting & Export
- Admin Reports page with filterable ticket exports
- Export to Excel `.xlsx` via `openpyxl`
- Includes ticket metadata, status, dates, comments, and vendor references

### Notifications
- Ticket email notifications for creation and closure
- Sends email to the employee and configured admin notification emails
- Admin email list managed from the settings page

### Dashboard & Analytics
- KPI summary cards for open, assigned, hold, escalated, closed, and critical tickets
- Dashboard visualizations powered by Chart.js
- Light/dark theme support for consistency across pages

### UI & UX Enhancements
- Responsive Bootstrap layout for desktop and mobile
- Light/dark theme support with CSS variables
- Clear filters and advanced filter panels on ticket list pages
- Confirmation prompts for destructive actions

---

## 📁 Project Structure

- `manage.py` — Django entrypoint
- `gplast_ticket/` — Project settings, URLs, WSGI, ASGI
- `tickets/` — Main app
  - `models.py` — Unit, Department, Ticket, TicketHistory, notification models
  - `views.py` — employee/admin ticket views, reports, settings
  - `forms.py` — form definitions and validation
  - `templates/` — HTML templates for admin, employee, emails, and base layout
  - `static/` — CSS, JS, images, and theme assets
  - `management/commands/seed_data.py` — seed script for demo data
- `requirements.txt` — Python dependencies
- `.env.example` — environment variable sample

---

## 🛠 Installation

### Prerequisites
- Python 3.11+
- MySQL Server 8.x or compatible
- Git (optional)

### Setup
```powershell
cd c:\Users\ERP\Desktop\gplast_ticket_system\tikcet-system
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Environment
Copy `.env.example` to `.env` and update values:
```ini
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=gplast_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=3306
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Database setup
```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
```

### Run locally
```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

---

## ⚙️ Default Accounts

The seed command may create default admin and employee users. Check `tickets/management/commands/seed_data.py` for seeded credentials.

---

## 📦 Dependencies

Current dependencies in `requirements.txt`:
- `Django>=4.2,<5.1`
- `mysqlclient`
- `openpyxl`
- `Pillow`
- `python-decouple`
- `whitenoise`
- `PyMySQL`

---

## 📧 Email Alerts Configuration

To enable email alerts for ticket creations and closures:

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=support@gplast.com
EMAIL_HOST_PASSWORD=SecureMailPassword123
DEFAULT_FROM_EMAIL=GPLAST Support <support@gplast.com>
```

The system sends emails to ticket contacts and active admin notification addresses configured in the settings page.

---

## 🔒 Security Notes
- Uses Django auth and session middleware.
- CSRF protection is enabled on all forms.
- Uses Django ORM for query safety.
- File uploads are restricted by allowed extensions and max size.

---

## ✅ Validation

Run app checks and tests:
```powershell
python manage.py check
python manage.py test
```

---

## 📌 Future Improvements
- Add role-based permissions beyond `is_staff`
- Add ticket comments and attachments gallery
- Add pagination for ticket lists
- Add REST API support for external integration
