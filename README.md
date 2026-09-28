Here is the complete, updated `README.md` — reflecting your current project structure and the changes we've made (oversight admin_view, split-pane ticket list, 9-card ticket detail, single-ticket Excel/CSV exports, filters, Reports page, dashboards).

```markdown
# GPLAST Internal Ticket System

Internal Django ticketing and support system for GPLAST ERP. It supports ticket creation and resolution, administration, settings management, audit logging, reports, notifications, attachments, scheduled email reports, native Windows toast notifications, ticket archival, and an auditor **Oversight** workspace.

This guide covers the complete project structure and deployment on an on-premises Dell server running Windows Server. The application uses MySQL and Django.

---

## Features

### Core ticket workflow

- Employee, Admin, Unit Head, and **Auditor (Oversight)** workflows
- Ticket assignment, status changes, closure, reopening, attachments, and history
- Units, departments, employees, credentials, ERP mappings, and screen mappings
- Settings audit log with date filters and Excel export
- Dashboard, ticket reports, escalated aging reports, and Excel exports

### Oversight (read-only audit workspace)

- Dedicated `/admin_view/` namespace for auditors
- Oversight dashboard with KPI strip and recent tickets table
- Split-pane ticket list with multi-select dropdown filters:
  - Search by subject, description, or ticket number
  - Quick presets (All / Open / Assigned / Hold / Escalated / Closed / Escalated + Closed)
  - Status, Priority, Unit, Department, and Assigned Person
  - Unit → Department → Assigned cascade with locked states
- Read-only ticket detail with 9 stacked cards:
  - Headline, Status, Priority, Assigned, Target
  - Description, Attachment, Comments, Details
- Audit History table (Action / Performed By / Timestamp / Remarks)
- Single-ticket Excel and CSV exports with full ticket data, description, closing details, and conversation
- Filtered list exports (CSV and Excel) with Description column
- Reports page with grouped summaries (status, priority, top units)

### Desktop notifications

- Native Windows toast notifications delivered to logged-in users
- Toast fires on ticket created, assigned, replied, status changed, priority changed, and escalated events
- Clicking a toast opens the ticket directly
- No external infrastructure required (no Redis, no Celery, no WebSocket)
- Works on Chrome, Edge, and Firefox on Windows

### Email notifications

- Email fallback for events when the browser is closed
- Assignee emails delivered to the address on file in `EmployeeMaster`
- Scheduled daily, weekly, or monthly summary reports sent by the email scheduler

### Ticket archive

- Closed tickets older than 90 days are auto-archived by a nightly command
- Archived tickets are hidden from active lists by default
- Dedicated archive page with KPIs, filters, and bulk restore
- Restore any archived ticket back to active lists with one click
- Every archive and restore is logged in `TicketHistory`
- Excel export of archived tickets with archive metadata

### Notifications history

- `Notification` model stores every toast and email event
- Browser polls `/notifications/poll/` for new rows
- Unread count and history available for any logged-in user

---

## Complete Folder Structure

```text
gplast_internal_Ticket_system/
|
|-- manage.py                              Django command-line entry point
|-- requirements.txt                       Python dependencies
|-- README.md                              Project, setup, architecture, and operations guide
|-- .env                                   Local/private configuration; never commit
|-- .env.example                           Safe configuration template
|
|-- gplast_ticket/                         Django project package
|   |-- __init__.py
|   |-- settings.py                        Database, email, security, static, media, and logging settings
|   |-- urls.py                            Root URL configuration; includes tickets.urls
|   |-- asgi.py                            ASGI entry point
|   `-- wsgi.py                            WSGI entry point for Waitress/IIS
|
|-- tickets/                               Main Django application
|   |-- __init__.py
|   |-- admin.py                           Django admin registrations
|   |-- apps.py                            Application configuration
|   |-- context_processors.py              Shared navigation and notification context
|   |-- email_utils.py                     Scheduled report email generation, notification email helper
|   |-- export_helpers.py                  Shared Excel reply-sheet and reply-section writers
|   |-- forms.py                           Ticket, close-ticket, and TicketReplyForm definitions
|   |-- models.py                          Ticket, TicketHistory, TicketReply, Notification, users, units, and settings models
|   |-- notification_tags.py               Notification template tags
|   |-- tests.py                           Automated Django tests
|   |-- urls.py                            Employee, Admin, Unit Head, AJAX, report, settings, archive, and notification routes
|   |-- utils.py                           Role checks, attachment validation, reopening, and shared helpers
|   |
|   |-- migrations/
|   |   |-- __init__.py
|   |   |-- 0001_initial.py                Initial database schema
|   |   |-- 0002_ticket_target_date.py     Adds ticket target dates
|   |   |-- 0003_ticketreply.py             Adds conversation replies and reply attachments
|   |   |-- 0004_notification.py            Adds desktop notification model
|   |   `-- 0005_ticket_archive.py          Adds archive fields to Ticket
|   |
|   |-- management/
|   |   `-- commands/
|   |       |-- send_emails.py             Sends due scheduled reports
|   |       |-- run_email_scheduler.py     Continuously checks the email schedule
|   |       `-- archive_old_tickets.py     Auto-archives closed tickets older than N days
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   `-- notify.py                      Central notification service (toasts + emails)
|   |
|   |-- templatetags/
|   |   |-- __init__.py
|   |   `-- ticket_filters.py              Aging, priority, and ticket display filters
|   |
|   `-- views/
|       |-- __init__.py                    Central view exports
|       |-- auth_views.py                  Login, logout, and role redirects
|       |-- employee_views.py              Employee dashboard, tickets, exports, and permissions
|       |-- admin_views.py                 Admin dashboard, ticket actions, archive, restore, and settings actions
|       |-- unit_head_views.py             Unit Head dashboard, unit filtering, and exports
|       |-- reply_views.py                 Shared permission-aware reply endpoint
|       |-- reports_views.py               Reports, escalated aging, exports, and escalated detail page
|       |-- ajax_views.py                  AJAX statistics, search, and ticket data endpoints
|       |-- settings_views.py               Settings pages
|       |-- audit_views.py                 Audit log display and export
|       |-- backup_views.py                Full database backup export
|       |-- scheduled_email_views.py       Scheduled email settings
|       |-- notification_views.py          Desktop toast poll / mark-read endpoints
|       |
|       `-- admin_view/                    OVERSIGHT (read-only auditor workspace)
|           |-- __init__.py
|           |-- decorators.py              auditor_required, auditor_can
|           |-- urls.py                    /admin_view/ routes (mounted by root urls.py)
|           |-- context_processors.py      Oversight context processor
|           `-- views.py                   Dashboard, tickets_page (list+detail), exports, actions
|
|-- templates/
|   |-- base.html                          Shared shell, sidebar, Bootstrap, global CSS, global JS, notifications include
|   |-- auth/login.html                    Login page
|   |-- tickets/_ticket_replies.html       Shared conversation list and reply form
|   |
|   |-- employee/                          Employee dashboard and ticket pages
|   |   |-- dashboard.html                 KPI cards, charts, and drill-down modal
|   |   |-- create_ticket.html             Employee ticket creation
|   |   |-- my_tickets.html                Employee ticket list and filters
|   |   |-- ticket_detail.html             Employee ticket detail and replies
|   |   `-- _ticket_list_modal.html        Employee ticket-list markup/styles
|   |
|   |-- admin_panel/                       Admin, reports, settings, and archive pages
|   |   |-- dashboard.html                 System KPIs, charts, and drill-down modal
|   |   |-- all_tickets.html               Admin ticket list and filters
|   |   |-- ticket_detail.html             Admin editing/workflow page
|   |   |-- archived_tickets.html          Dedicated archive page with bulk restore
|   |   |-- escalated_aging_report.html    Escalated aging report
|   |   |-- escalated_ticket_detail.html   Read-only individual escalated page
|   |   |-- reports.html                   Admin reports
|   |   |-- create_ticket.html             Admin ticket creation
|   |   |-- settings_*.html                Settings and administration screens
|   |   `-- _ticket_list_modal.html        Admin ticket-list markup
|   |
|   |-- admin_view/                        OVERSIGHT templates
|   |   |-- dashboard.html                 Oversight dashboard (KPI strip + recent tickets)
|   |   |-- ticket_list.html               Split filter panel + ticket table
|   |   |-- ticket_detail.html             9-card read-only ticket detail
|   |   |-- reports.html                   Reports (status / priority / top units)
|   |   `-- partials/
|   |       |-- _read_only_banner.html     Amber "Oversight mode" banner
|   |       |-- _kpi_strip.html            KPI cards (Total / Open / Critical / Escalated / Overdue)
|   |       `-- _recent_tickets.html       Recent tickets table (row → detail)
|   |
|   `-- unit_head/                         Unit Head dashboard and unit-scoped pages
|       |-- dashboard.html                 Unit KPIs, charts, and drill-down modal
|       |-- all_tickets.html               Unit-scoped ticket list
|       |-- my_tickets.html                Unit Head ticket view
|       |-- ticket_detail.html             Unit-scoped detail and replies
|       |-- reports.html                   Unit reports
|       `-- _ticket_list_modal.html        Unit Head ticket-list markup/styles
|
|-- static/
|   |-- css/
|   |   |-- shared/
|   |   |   |-- base.css                   Global layout, variables, navigation, badges, modal base
|   |   |   `-- components.css             Shared responsive buttons, drill-downs, replies, tables, controls
|   |   |-- employee/                      Employee-specific pages and dashboard styles
|   |   |-- admin_panel/                   Admin, reports, settings, dashboard, archive styles
|   |   |-- admin_view/                    OVERSIGHT page styles
|   |   |   |-- oversight.css              Shared oversight components (badges, cards, buttons, forms)
|   |   |   |-- dashboard.css              Oversight dashboard page
|   |   |   |-- ticket_list.css            Split-pane list + dropdowns + table
|   |   |   |-- ticket_detail.css          9-card detail, audit table, comments, responsive
|   |   |   `-- reports.css                Reports page (cards, stat lists, chart wrap)
|   |   |-- unit_head/                     Unit Head pages and dashboard styles
|   |   `-- style.css                      Legacy stylesheet retained for compatibility
|   |
|   |-- js/
|   |   |-- base.js                        Sidebar, theme, and global layout behavior
|   |   |-- shared/
|   |   |   |-- charts.js                  Shared chart helpers
|   |   |   |-- confirmations.js           Shared confirmation hook location
|   |   |   |-- ticket_ui.js               Shared JSON, aging, modal, and UI helpers
|   |   |   `-- desktop_notifications.js   Native Windows toast engine
|   |   |-- employee/                      Employee dashboard and ticket scripts
|   |   |-- admin_panel/                   Admin dashboard, settings, reports, archive scripts
|   |   |-- admin_view/                    OVERSIGHT page scripts
|   |   |   |-- ticket_list.js             Dropdown filters, cascade, row nav
|   |   |   |-- ticket_detail.js           Priority confirm, comment guard, autosize
|   |   |   |-- reports.js                 Chart.js rendering for reports
|   |   |   `-- dashboard.js               Recent-tickets row navigation
|   |   `-- unit_head/                     Unit Head dashboard and ticket scripts
|   |
|   `-- images/                            Logos, favicon, and interface images
|
|-- media/
|   |-- attachments/                       Original ticket attachments
|   |-- attachments/replies/               Reply attachments
|   `-- attachments/reopen/                Reopen attachments
|
|-- logs/django.log                        Runtime application log
|-- staticfiles/                           collectstatic output; generated, not source
`-- venv/                                  Local Python environment; recreate per machine
```

Do not commit `.env`, `venv/`, `media/`, `logs/`, `staticfiles/`, or Python `__pycache__` directories.

---

## Application Architecture

### Roles

- **Employee:** creates tickets and views/replies to tickets in the employee's permitted department scope.
- **Admin:** manages all tickets, assignments, escalation, closure, reopening, settings, reports, archive, and replies.
- **Unit Head:** views and replies to tickets in the assigned unit and uses unit-scoped reports and exports.
- **Auditor (Oversight):** read-only view across every unit and department. Can post comments and change priority (if permitted) but cannot change workflow status, assign, escalate, close, or reopen.

Role permissions are enforced in Django views. Frontend visibility is not treated as a security boundary.

### Oversight workspace

- Mounted at `/admin_view/` by the root URL config.
- Uses `@auditor_required` on every view; a small set of views additionally use `@auditor_can('tickets.<perm>')`.
- `tickets_page` in `admin_view/views.py` handles both list and detail — the presence of `ticket_id` in the URL decides which template renders:
  - `/admin_view/tickets/` → `admin_view/ticket_list.html`
  - `/admin_view/tickets/<id>/` → `admin_view/ticket_detail.html`
- Filters are multi-select and cascade (Unit → Department → Assigned).
- The Oversight template uses `oversight.css` plus one page-specific CSS per page. Every Oversight page shares the same design tokens.

### Ticket communication

- `TicketHistory` stores workflow/audit events such as assignment, escalation, closure, reopening, priority changes, target-date changes, archive, and restore.
- `TicketReply` stores user conversation messages separately from workflow history.
- Replies can include an attachment under `media/attachments/replies/`.
- `templates/tickets/_ticket_replies.html` is reused by Employee, Admin, Unit Head, and the escalated-ticket page.
- `tickets/views/reply_views.py` applies the role and department/unit checks before saving a reply.

### Desktop notifications

- `Notification` model stores one row per (recipient, event, ticket).
- `tickets/services/notify.py` is the single entry point.
- `static/js/shared/desktop_notifications.js` polls `/notifications/poll/` every 30 seconds (120 seconds when the tab is hidden).
- The browser converts each new row into a native Windows toast.
- Email fallback: assignee emails are sent for events when the browser is not polling.
- Self-notifications are suppressed.

### Ticket archive

- `Ticket.is_archived` + `archived_at` + `archived_by` fields drive the archive state.
- A custom `TicketManager` hides archived tickets from every normal query (`Ticket.objects.all()` returns active tickets only).
- Use `Ticket.objects.with_archived()` to see everything.
- Use `Ticket.objects.archived_only()` to see only archived tickets.
- `manage.py archive_old_tickets --days 90` archives closed tickets older than 90 days.
- The archive page `/custom-admin/archive/` lists archived tickets with KPIs, filters, and bulk restore.
- Restore single or bulk via POST. Every action writes a `TicketHistory` entry.

### Shared frontend controls

- `static/css/shared/components.css` owns responsive controls, drill-down modal layout, badges, tables, reply panels, focus states, and mobile behavior.
- `static/js/shared/ticket_ui.js` owns shared JSON response validation, aging formatting, HTML escaping, modal state helpers, and cleanup behavior.
- Role dashboards keep their own data and filters but use shared route data and shared UI styling.

### Exports

Individual and filtered Excel exports include ticket replies. Reply data is written with ticket number, timestamp, sender, role, message, and attachment name. The full backup includes the `TicketReply` model sheet. Archived tickets have a dedicated export at `/custom-admin/tickets/export-archived/`.

**Oversight exports:**
- `/admin_view/tickets/<pk>/excel/` — single-ticket Excel
- `/admin_view/tickets/<pk>/csv/` — single-ticket CSV
- `/admin_view/reports/export/csv/` — filtered list CSV (respects current filters)
- `/admin_view/reports/export/xlsx/` — filtered list Excel (respects current filters)

---

## Important URLs

```text
/login/
/dashboard/
/create-ticket/
/my-tickets/

/custom-admin/dashboard/
/custom-admin/tickets/
/custom-admin/reports/
/custom-admin/settings/
/custom-admin/settings/communication/
/custom-admin/settings/audit/
/custom-admin/settings/audit/download-excel/
/custom-admin/settings/backup/
/custom-admin/archive/
/custom-admin/ticket/<id>/restore/
/custom-admin/tickets/bulk-restore/
/custom-admin/tickets/export-archived/

/notifications/poll/
/notifications/<id>/read/
/notifications/read-all/

# Oversight (read-only auditor workspace)
/admin_view/
/admin_view/tickets/
/admin_view/tickets/<id>/
/admin_view/tickets/<id>/comment/
/admin_view/tickets/<id>/priority/
/admin_view/tickets/<pk>/excel/
/admin_view/tickets/<pk>/csv/
/admin_view/reports/
/admin_view/reports/export/csv/
/admin_view/reports/export/xlsx/
```

---

## Settings Dashboard Structure

The administrator Settings dashboard in `templates/admin_panel/settings_index.html` is organized into four sections:

- **Configuration:** Units & Departments, Communication, and Department Credentials
- **People & Access:** Employee Master, Department Employees, and ERP User ID Mapping
- **System Records:** Audit Logs, Screen Master, and Screen Mapping
- **Backup & Recovery:** Full System Backup, which downloads all application records as a timestamped Excel workbook

The Settings dashboard and backup route are available only to administrator accounts.

---

## On-Premises Dell Server Requirements

- Windows Server with a fixed LAN IP or DNS name
- Python 3.10 or newer
- MySQL 8.x, on the same server or an approved database server
- Permission to create a database and database user
- Firewall access for the selected web port, normally TCP 8000 or TCP 80/443 through IIS
- Outbound SMTP access to the configured mail provider
- A dedicated Windows service account with access to the application, media, and logs folders
- Backup storage for the MySQL database and `media` folder

Do not expose Django `runserver` directly to the public internet.

---

## Copy the Project to the Server

Use a stable path such as:

```text
C:\Apps\GPLAST\gplast_internal_Ticket_system
```

Copy the source to this folder. Do not copy the development `venv` folder. Do not copy an old `.env` containing shared or expired secrets.

```powershell
Set-Location C:\Apps\GPLAST\gplast_internal_Ticket_system
```

---

## Create the Python Environment

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Create the MySQL Database

Use a dedicated application user instead of MySQL root:

```sql
CREATE DATABASE gplast_ticketsystemdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gplast_ticketsystemdb'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON gplast_ticketsystemdb.* TO 'gplast_ticketsystemdb'@'localhost';
FLUSH PRIVILEGES;
```

If MySQL is on another server, replace `localhost` with the approved application-server address.

---

## Configure `.env`

Create `.env` from `.env.example`. Keep it out of source control and restrict its NTFS permissions.

```dotenv
SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,SERVER_NAME_OR_IP
APP_URL=http://SERVER_NAME_OR_IP:8000

DB_NAME=gplast_ticketsystemdb
DB_USER=gplast_ticketsystemdb
DB_PASSWORD=REPLACE_WITH_DATABASE_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=3306
```

Example SMTP configuration using SSL:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_HOST_USER=application-mailbox@example.com
EMAIL_HOST_PASSWORD=REPLACE_WITH_SMTP_PASSWORD_OR_APP_PASSWORD
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
DEFAULT_FROM_EMAIL=GPLAST Support <application-mailbox@example.com>
EMAIL_TIMEOUT=30
```

For STARTTLS providers, normally use port `587`, `EMAIL_USE_TLS=True`, and `EMAIL_USE_SSL=False`. Do not enable TLS and SSL together.

The application timezone is `Asia/Kolkata`.

---

## Initialize Django

```powershell
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Make sure these folders exist and are writable by the service account:

```text
logs\
media\
media\attachments\
media\attachments\replies\
media\attachments\reopen\
staticfiles\
```

---

## Test Before Production

```powershell
python manage.py check
python manage.py test
```

Temporary local test only:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Stop `runserver` after testing. It is not a production web server.

---

## Production Web Hosting on Windows

Waitress is included in `requirements.txt`:

```powershell
.\venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 gplast_ticket.wsgi:application
```

For direct internal LAN access:

```powershell
.\venv\Scripts\waitress-serve.exe --listen=0.0.0.0:8000 gplast_ticket.wsgi:application
```

For stronger production security, bind Waitress to `127.0.0.1:8000` and use IIS as an HTTPS reverse proxy.

---

## Automatic Email Scheduler

Continuous scheduler command:

```powershell
Set-Location C:\Apps\GPLAST\gplast_internal_Ticket_system
.\venv\Scripts\python.exe manage.py run_email_scheduler --interval 30
```

One-time due check:

```powershell
python manage.py send_emails
```

Immediate intentional test:

```powershell
python manage.py send_emails --force
```

---

## Automatic Ticket Archive

Dry run (preview only):

```powershell
python manage.py archive_old_tickets --days 90 --dry-run
```

Archive for real:

```powershell
python manage.py archive_old_tickets --days 90
```

Every archived ticket receives `is_archived=True`, `archived_at=now`, `archived_by="System (auto)"`, and a `TicketHistory` entry.

---

## Windows Service Configuration

Use NSSM or a company-approved Windows service wrapper.

**Web service:**
```text
Application: C:\Apps\GPLAST\gplast_internal_Ticket_system\venv\Scripts\waitress-serve.exe
Arguments: --listen=127.0.0.1:8000 gplast_ticket.wsgi:application
Startup directory: C:\Apps\GPLAST\gplast_internal_Ticket_system
Startup type: Automatic
```

**Email scheduler service:**
```text
Application: C:\Apps\GPLAST\gplast_internal_Ticket_system\venv\Scripts\python.exe
Arguments: manage.py run_email_scheduler --interval 30
Startup directory: C:\Apps\GPLAST\gplast_internal_Ticket_system
Startup type: Automatic
```

Use either the continuous scheduler service or a repeating `send_emails` task, not both.

---

## Windows Task Scheduler — Nightly Archive

```text
Name:      GPLAST Auto-Archive Tickets
Trigger:   Daily at 02:00 AM
Action:    Start a program

Program:   C:\Apps\GPLAST\gplast_internal_Ticket_system\venv\Scripts\python.exe
Arguments: manage.py archive_old_tickets --days 90
Start in:  C:\Apps\GPLAST\gplast_internal_Ticket_system

Run whether user is logged on or not: yes
Run with highest privileges: yes
```

---

## Firewall and Network

```powershell
New-NetFirewallRule -DisplayName "GPLAST Ticket System" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -RemoteAddress 10.0.0.0/8
```

If IIS is used, expose only approved HTTP/HTTPS ports and keep Waitress on localhost.

---

## Static Files and Uploaded Media

Run after each release that changes CSS, JavaScript, or images:

```powershell
python manage.py collectstatic --noinput
```

Static files are collected into `staticfiles`. User-uploaded ticket attachments are stored under `media`. Back up `media` separately and never delete it during deployment.

**Tip:** If a page still serves stale CSS or JS after you edit a file, run `python manage.py collectstatic --noinput --clear` to wipe and re-copy the static tree.

---

## Logs and Monitoring

Application errors are written to:

```text
logs\django.log
```

Useful checks:

```powershell
python manage.py check
python manage.py send_emails
python manage.py archive_old_tickets --days 90 --dry-run
Get-Content .\logs\django.log -Tail 100
Get-NetTCPConnection -LocalPort 8000
```

---

## Backup and Recovery

Example database backup:

```powershell
mysqldump -u gplast_ticketsystemdb -p --routines --triggers gplast_ticketsystemdb > C:\Backups\gplast_ticketsystemdb.sql
```

Back up:

- MySQL database `gplast_ticketsystemdb`
- `media\` and ticket attachments
- `.env` in a protected backup location
- Deployment and Windows service configuration

---

## Updating the Application

1. Back up the database and media folder.
2. Stop the web and scheduler services.
3. Copy the new source while preserving `.env`, `media`, and `logs`.
4. Install updated requirements.
5. Run migrations and checks.
6. Collect static files.
7. Start the web service and scheduler service.
8. Test login, ticket creation, audit filtering, Excel export, email, and desktop notifications.

```powershell
Set-Location C:\Apps\GPLAST\gplast_internal_Ticket_system
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py collectstatic --noinput
```

---

## Troubleshooting

### Website does not open

- Confirm the Waitress service is running.
- Check the listening port with `Get-NetTCPConnection -LocalPort 8000`.
- Check Windows Firewall and the server LAN IP.
- Check `ALLOWED_HOSTS` and `APP_URL`.

### Scheduled email is not sent

- Confirm the scheduler service or repeating `send_emails` task is running.
- Confirm the schedule is enabled and at least one report is selected.
- Confirm admin and unit-head addresses are valid.
- Run `python manage.py send_emails` and read its output.
- Remember `last_sent_at` prevents a second automatic send on the same local date.

### Test email fails

- Verify SMTP host, port, username, password, SSL, and TLS values.
- Use an app password when required by the provider.
- Confirm outbound SMTP traffic is allowed.

### Database connection fails

- Confirm MySQL is running.
- Verify all `DB_*` values in `.env`.
- Confirm the MySQL user has privileges on `gplast_ticketsystemdb`.

### Attachments fail

- Confirm `media\attachments\replies` and `media\attachments\reopen` exist.
- Confirm the service account has write permission.
- Confirm the reverse proxy request-size limit.
- Do not remove `media` during deployment.

### Desktop notifications do not appear

- Open the browser DevTools Console. Look for `[GPLAST] Notification permission granted.`
- If permission is denied, click the padlock icon in the URL bar, set Notifications to **Allow**, and reload.
- On Windows, open Settings → System → Notifications & actions.
- Confirm `static/js/shared/desktop_notifications.js` is loaded.
- Confirm the user has at least one row in `tickets_notification`.

### Archive page does not open

- Confirm `python manage.py check` passes.
- Confirm the archive views are exported from `tickets/views/__init__.py`.
- Confirm `templates/admin_panel/archived_tickets.html` exists.
- Confirm `tickets/urls.py` includes the archive routes.
- Confirm the logged-in user is an administrator.

### Auto-archive does not run

- Run `python manage.py archive_old_tickets --days 90 --dry-run`.
- Check Windows Task Scheduler history for the archive job.
- Check `logs\django.log` for errors from the command.
- Confirm the service account has read/write access to the project folder.

### Oversight chart shows nothing

- The chart was removed from the Oversight dashboard; only the KPI strip and recent tickets table remain. If you re-add the chart, ensure `av_dashboard_data` is passed in the `dashboard()` view context and that Chart.js loads.

### Oversight Reports — "Failed lookup for key [unit__name]"

- The `reports` view groups by `unit__code`, not `unit__name`. Templates must use `{{ row.unit__code }}`.

### Oversight exports return 403

- The `export_csv` and `export_xlsx` views are decorated with `@auditor_required`. Any logged-in auditor can export. If you want to restrict exports, add the permission to the `Ticket` model's `Meta.permissions` and switch back to `@auditor_can('tickets.export_ticket_reports')`.

### Static files are stale

- Run `python manage.py collectstatic --noinput --clear` to wipe the collected tree and re-copy from `static/`.
- Hard-reload the browser with **Ctrl + Shift + R**.

---

## Security Checklist

- Set `DEBUG=False`.
- Use a long random `SECRET_KEY`.
- Set `ALLOWED_HOSTS` to approved names and addresses only.
- Use a least-privilege MySQL user.
- Protect `.env` and exclude it from source control.
- Use HTTPS through IIS or an approved reverse proxy.
- Restrict access to the company LAN or VPN.
- Rotate database and SMTP credentials according to policy.
- Keep Windows, Python, MySQL, and packages patched.
- Back up the database and media files.
- Monitor application and Windows service logs.

---

## Important Operational Note

The web server, the scheduled email worker, and the nightly archive job are three separate processes. Starting the Django web application alone does not send automatic scheduled emails and does not auto-archive tickets. Production must keep:

- The web service running (Waitress or IIS).
- The email scheduler service running, or a repeating `send_emails` task.
- The nightly archive task scheduled.
```

---

## Summary of changes vs. your previous README

| Section | What changed |
|---|---|
| **Features** | Added the **Oversight** workspace as its own feature block (split-pane list, 9-card detail, cascading filters, single-ticket exports, reports) |
| **Folder structure** | Added `tickets/views/admin_view/`, `templates/admin_view/` with partials, `static/css/admin_view/`, `static/js/admin_view/` |
| **Application Architecture** | Added the Oversight workspace section (routes, templates, permission model) |
| **Exports** | Added the four Oversight export endpoints |
| **Important URLs** | Added the `/admin_view/...` routes |
| **Troubleshooting** | Added "Oversight chart shows nothing", "Reports — unit__name error", "Oversight exports return 403", "Static files are stale" |
| **Static Files** | Added the `collectstatic --clear` tip |
| **Roles** | Added "Auditor (Oversight)" |

Save this as `README.md` at the project root.