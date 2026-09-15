# Full updated `README.md`

Here is the complete README with every feature you've added since the last version: desktop toast notifications, email fallback, in-app notification history, auto-archive, dedicated archive page, and bulk restore.

```markdown
# GPLAST Internal Ticket System

Internal Django ticketing and support system for GPLAST ERP. It supports ticket creation and resolution, administration, settings management, audit logging, reports, notifications, attachments, scheduled email reports, native Windows toast notifications, and ticket archival.

This guide covers the complete project structure and deployment on an on-premises Dell server running Windows Server. The application uses MySQL and Django.

## Features

### Core ticket workflow

- Employee and administrator ticket workflows
- Ticket assignment, status changes, closure, reopening, attachments, and history
- Units, departments, employees, credentials, ERP mappings, and screen mappings
- Settings audit log with date filters and Excel export
- Dashboard, ticket reports, escalated aging reports, and Excel exports

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

## Complete Folder Structure

The repository is organized as a Django project with one application, role-specific templates, role-specific assets, and shared UI utilities.

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
|   |-- admin.py                            Django admin registrations
|   |-- apps.py                             Application configuration
|   |-- context_processors.py               Shared navigation and notification context
|   |-- email_utils.py                      Scheduled report email generation, notification email helper
|   |-- export_helpers.py                   Shared Excel reply-sheet and reply-section writers
|   |-- forms.py                             Ticket, close-ticket, and TicketReplyForm definitions
|   |-- models.py                            Ticket, TicketHistory, TicketReply, Notification, users, units, and settings models
|   |-- notification_tags.py                 Notification template tags
|   |-- tests.py                             Automated Django tests
|   |-- urls.py                              Employee, Admin, Unit Head, AJAX, report, settings, archive, and notification routes
|   |-- utils.py                             Role checks, attachment validation, reopening, and shared helpers
|   |
|   |-- migrations/
|   |   |-- __init__.py
|   |   |-- 0001_initial.py                  Initial database schema
|   |   |-- 0002_ticket_target_date.py       Adds ticket target dates
|   |   |-- 0003_ticketreply.py               Adds conversation replies and reply attachments
|   |   |-- 0004_notification.py              Adds desktop notification model
|   |   `-- 0005_ticket_archive.py            Adds archive fields to Ticket
|   |
|   |-- management/commands/
|   |   |-- send_emails.py                   Sends due scheduled reports
|   |   |-- run_email_scheduler.py           Continuously checks the email schedule
|   |   `-- archive_old_tickets.py           Auto-archives closed tickets older than N days
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   `-- notify.py                        Central notification service (toasts + emails)
|   |
|   |-- templatetags/
|   |   |-- __init__.py
|   |   `-- ticket_filters.py                Aging, priority, and ticket display filters
|   |
|   `-- views/
|       |-- __init__.py                      Central view exports
|       |-- auth_views.py                    Login, logout, and role redirects
|       |-- employee_views.py                Employee dashboard, tickets, exports, and permissions
|       |-- admin_views.py                   Admin dashboard, ticket actions, archive, restore, and settings actions
|       |-- unit_head_views.py               Unit Head dashboard, unit filtering, and exports
|       |-- reply_views.py                   Shared permission-aware reply endpoint
|       |-- reports_views.py                 Reports, escalated aging, exports, and escalated detail page
|       |-- ajax_views.py                    AJAX statistics, search, and ticket data endpoints
|       |-- settings_views.py                 Settings pages
|       |-- audit_views.py                   Audit log display and export
|       |-- backup_views.py                  Full database backup export
|       |-- scheduled_email_views.py         Scheduled email settings
|       |-- notification_views.py            Desktop toast poll / mark-read endpoints
|       |-- settings_action/                 POST handlers for settings administration
|       `-- utils.py                         View-level role and formatting helpers
|
|-- templates/
|   |-- base.html                           Shared shell, sidebar, Bootstrap, global CSS, global JS, notifications include
|   |-- auth/login.html                     Login page
|   |-- tickets/_ticket_replies.html        Shared conversation list and reply form
|   |
|   |-- employee/                           Employee dashboard and ticket pages
|   |   |-- dashboard.html                   KPI cards, charts, and drill-down modal
|   |   |-- create_ticket.html                Employee ticket creation
|   |   |-- my_tickets.html                   Employee ticket list and filters
|   |   |-- ticket_detail.html                 Employee ticket detail and replies
|   |   `-- _ticket_list_modal.html            Employee ticket-list markup/styles
|   |
|   |-- admin_panel/                        Admin, reports, settings, and archive pages
|   |   |-- dashboard.html                   System KPIs, charts, and drill-down modal
|   |   |-- all_tickets.html                  Admin ticket list and filters
|   |   |-- ticket_detail.html                 Admin editing/workflow page
|   |   |-- archived_tickets.html             Dedicated archive page with bulk restore
|   |   |-- escalated_aging_report.html       Escalated aging report
|   |   |-- escalated_ticket_detail.html       Read-only individual escalated page
|   |   |-- reports.html                      Admin reports
|   |   |-- create_ticket.html                Admin ticket creation
|   |   |-- settings_*.html                   Settings and administration screens
|   |   `-- _ticket_list_modal.html            Admin ticket-list markup
|   |
|   `-- unit_head/                          Unit Head dashboard and unit-scoped pages
|       |-- dashboard.html                   Unit KPIs, charts, and drill-down modal
|       |-- all_tickets.html                  Unit-scoped ticket list
|       |-- my_tickets.html                   Unit Head ticket view
|       |-- ticket_detail.html                 Unit-scoped detail and replies
|       |-- reports.html                      Unit reports
|       `-- _ticket_list_modal.html            Unit Head ticket-list markup/styles
|
|-- static/
|   |-- css/
|   |   |-- shared/
|   |   |   |-- base.css                      Global layout, variables, navigation, badges, and modal base styles
|   |   |   `-- components.css                Shared responsive buttons, drill-downs, replies, tables, and controls
|   |   |-- employee/                         Employee-specific pages and dashboard styles
|   |   |-- admin_panel/                      Admin, reports, settings, dashboard, and archive styles
|   |   |-- unit_head/                        Unit Head pages and dashboard styles
|   |   `-- style.css                         Legacy stylesheet retained for compatibility
|   |
|   |-- js/
|   |   |-- base.js                            Sidebar, theme, and global layout behavior
|   |   |-- shared/
|   |   |   |-- charts.js                      Shared chart helpers
|   |   |   |-- confirmations.js                Shared confirmation hook location
|   |   |   |-- ticket_ui.js                    Shared JSON, aging, modal, and UI helpers
|   |   |   `-- desktop_notifications.js        Native Windows toast engine (polls and shows toasts)
|   |   |-- employee/                          Employee dashboard and ticket scripts
|   |   |-- admin_panel/                       Admin dashboard, settings, reports, and archive scripts
|   |   `-- unit_head/                         Unit Head dashboard and ticket scripts
|   |
|   `-- images/                               Logos, favicon, and interface images
|
|-- media/
|   |-- attachments/                          Original ticket attachments
|   |-- attachments/replies/                  Reply attachments
|   `-- attachments/reopen/                   Reopen attachments
|
|-- logs/django.log                           Runtime application log
|-- staticfiles/                              collectstatic output; generated, not source
`-- venv/                                     Local Python environment; recreate per machine
```

Do not commit `.env`, `venv/`, `media/`, `logs/`, `staticfiles/`, or Python `__pycache__` directories.

## Application Architecture

### Roles

- **Employee:** creates tickets and views/replies to tickets in the employee's permitted department scope.
- **Admin:** manages all tickets, assignments, escalation, closure, reopening, settings, reports, archive, and replies.
- **Unit Head:** views and replies to tickets in the assigned unit and uses unit-scoped reports and exports.

Role permissions are enforced in Django views. Frontend visibility is not treated as a security boundary.

### Ticket communication

- `TicketHistory` stores workflow/audit events such as assignment, escalation, closure, reopening, priority changes, target-date changes, archive, and restore.
- `TicketReply` stores user conversation messages separately from workflow history.
- Replies can include an attachment under `media/attachments/replies/`.
- `templates/tickets/_ticket_replies.html` is reused by Employee, Admin, Unit Head, and the individual escalated-ticket page.
- `tickets/views/reply_views.py` applies the role and department/unit checks before saving a reply.

### Desktop notifications

- `Notification` model stores one row per (recipient, event, ticket).
- `tickets/services/notify.py` is the single entry point. Every view calls a `notify_*` helper; the service decides recipients and writes rows.
- `static/js/shared/desktop_notifications.js` polls `/notifications/poll/` every 30 seconds (120 seconds when the tab is hidden).
- The browser converts each new row into a native Windows toast. Clicking the toast opens the ticket.
- Email fallback: assignee emails are sent for events when the browser is not polling.
- Self-notifications are suppressed — you never get your own toast.

### Ticket archive

- `Ticket.is_archived` + `archived_at` + `archived_by` fields drive the archive state.
- A custom `TicketManager` hides archived tickets from every normal query (`Ticket.objects.all()` returns active tickets only).
- Use `Ticket.objects.with_archived()` to see everything.
- Use `Ticket.objects.archived_only()` to see only archived tickets.
- `manage.py archive_old_tickets --days 90` archives closed tickets older than 90 days. Scheduled nightly via Task Scheduler or Windows service.
- The archive page `/custom-admin/archive/` lists archived tickets with KPIs, filters, and bulk restore.
- Restore single or bulk via POST. Every action writes a `TicketHistory` entry.

### Shared frontend controls

- `static/css/shared/components.css` owns responsive controls, drill-down modal layout, badges, tables, reply panels, focus states, and mobile behavior.
- `static/js/shared/ticket_ui.js` owns shared JSON response validation, aging formatting, HTML escaping, modal state helpers, and cleanup behavior.
- Role dashboards keep their own data and filters but use shared route data and shared UI styling.

### Exports

Individual and filtered Excel exports include ticket replies. Reply data is written with ticket number, timestamp, sender, role, message, and attachment name. The full backup includes the `TicketReply` model sheet. Archived tickets have a dedicated export at `/custom-admin/tickets/export-archived/`.

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
```

## Settings Dashboard Structure

The administrator Settings dashboard in `templates/admin_panel/settings_index.html` is organized into four sections:

- **Configuration:** Units & Departments, Communication, and Department Credentials
- **People & Access:** Employee Master, Department Employees, and ERP User ID Mapping
- **System Records:** Audit Logs, Screen Master, and Screen Mapping
- **Backup & Recovery:** Full System Backup, which downloads all application records as a timestamped Excel workbook

The Settings dashboard and backup route are available only to administrator accounts.

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

## Copy the Project to the Server

Use a stable path such as:

```text
C:\Apps\GPLAST\gplast_internal_Ticket_system
```

Copy the source to this folder. Do not copy the development `venv` folder. Do not copy an old `.env` containing shared or expired secrets.

```powershell
Set-Location C:\Apps\GPLAST\gplast_internal_Ticket_system
```

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

## Create the MySQL Database

Use a dedicated application user instead of MySQL root:

```sql
CREATE DATABASE gplast_ticketsystemdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gplast_ticketsystemdb'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON gplast_ticketsystemdb.* TO 'gplast_ticketsystemdb'@'localhost';
FLUSH PRIVILEGES;
```

If MySQL is on another server, replace `localhost` with the approved application-server address and configure the MySQL firewall and bind address.

## Configure `.env`

Create `.env` from `.env.example`. Keep it out of source control and restrict its NTFS permissions to the application service account and administrators.

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

The application timezone is `Asia/Kolkata`. Scheduled email times use this timezone.

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

## Production Web Hosting on Windows

Waitress is included in `requirements.txt`:

```powershell
.\venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 gplast_ticket.wsgi:application
```

For direct internal LAN access, use:

```powershell
.\venv\Scripts\waitress-serve.exe --listen=0.0.0.0:8000 gplast_ticket.wsgi:application
```

For stronger production security, bind Waitress to `127.0.0.1:8000` and use IIS or an approved reverse proxy for HTTPS and access control.

## Automatic Email Scheduler

The Django web server does not execute scheduled email code. Automatic email delivery requires a separate scheduler process or a repeating Windows task.

Continuous scheduler command:

```powershell
Set-Location C:\Apps\GPLAST\gplast_internal_Ticket_system
.\venv\Scripts\python.exe manage.py run_email_scheduler --interval 30
```

The scheduler checks every 30 seconds. It sends only when:

- The schedule is enabled.
- At least one report is selected.
- Admins or unit heads are enabled as recipients.
- Valid recipient email addresses exist.
- The configured local time has been reached.
- The selected daily, weekly, or monthly frequency is due.
- A successful report has not already been sent on the current local date.

`EmailSchedule.last_sent_at` records the last successful send. This prevents duplicate automatic sends on the same local day.

One-time due check:

```powershell
python manage.py send_emails
```

Immediate intentional test:

```powershell
python manage.py send_emails --force
```

The settings buttons work as follows:

- `Save Schedule` stores configuration only.
- `Send Test Email` sends immediately.
- `Send Now` sends immediately.

## Automatic Ticket Archive

The archive command runs separately from the web server, exactly like the email scheduler.

Dry run (preview only):

```powershell
python manage.py archive_old_tickets --days 90 --dry-run
```

Archive for real:

```powershell
python manage.py archive_old_tickets --days 90
```

The command only archives tickets that are:

- `status='Closed'`
- `is_archived=False`
- `closed_at` older than N days

Every archived ticket receives:

- `is_archived=True`
- `archived_at=now`
- `archived_by="System (auto)"`
- A `TicketHistory` entry: `Archived Ticket — Auto-archived (closed more than N days ago)`

## Windows Service Configuration

Use NSSM or a company-approved Windows service wrapper for the continuous scheduler. Configure it as:

```text
Application: C:\Apps\GPLAST\gplast_internal_Ticket_system\venv\Scripts\python.exe
Arguments: manage.py run_email_scheduler --interval 30
Startup directory: C:\Apps\GPLAST\gplast_internal_Ticket_system
Startup type: Automatic
Account: Dedicated application service account
```

Create a second service for the web process:

```text
Application: C:\Apps\GPLAST\gplast_internal_Ticket_system\venv\Scripts\waitress-serve.exe
Arguments: --listen=127.0.0.1:8000 gplast_ticket.wsgi:application
Startup directory: C:\Apps\GPLAST\gplast_internal_Ticket_system
Startup type: Automatic
```

If a service wrapper is not approved, use Windows Task Scheduler to run `send_emails` every minute:

```text
Program: C:\Apps\GPLAST\gplast_internal_Ticket_system\venv\Scripts\python.exe
Arguments: manage.py send_emails
Start in: C:\Apps\GPLAST\gplast_internal_Ticket_system
Trigger: Repeat every 1 minute indefinitely
Run whether user is logged on or not
```

Use either the continuous scheduler service or the repeating task, not both.

## Windows Task Scheduler — Nightly Archive

Create a third Task Scheduler entry for the nightly archive job:

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

## Configure Scheduled Reports in the Admin UI

1. Log in as an administrator.
2. Open Settings, then Communication.
3. Select one or more reports.
4. Select Daily, Weekly, or Monthly frequency.
5. Set the time in Chennai time (`Asia/Kolkata`).
6. Enable Admins and/or Unit Heads.
7. Configure notification emails, additional CC emails, and unit-head addresses.
8. Enable scheduled reports.
9. Save the schedule.
10. Use `Send Test Email` to verify SMTP delivery.
11. Confirm the scheduler service is running.

## Firewall and Network

Example rule for internal port 8000. Replace the network range with the company-approved subnet:

```powershell
New-NetFirewallRule -DisplayName "GPLAST Ticket System" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -RemoteAddress 10.0.0.0/8
```

If IIS or a reverse proxy is used, expose only approved HTTP/HTTPS ports and keep Waitress on localhost. For email, allow outbound traffic to the SMTP host and port. Confirm DNS, gateway, and server time.

## Static Files and Uploaded Media

Run after each release that changes CSS, JavaScript, or images:

```powershell
python manage.py collectstatic --noinput
```

Static files are collected into `staticfiles`. User-uploaded ticket attachments are stored under `media`. Back up `media` separately and never delete it during deployment.

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

Also monitor Windows Event Viewer and the logs of the web and scheduler services.

## Backup and Recovery

Back up the database, uploaded media, protected configuration, and service settings.

Example database backup:

```powershell
mysqldump -u gplast_ticketsystemdb -p --routines --triggers gplast_ticketsystemdb > C:\Backups\gplast_ticketsystemdb.sql
```

Back up:

- MySQL database `gplast_ticketsystemdb`
- `media\` and ticket attachments
- `.env` in a protected backup location
- Deployment and Windows service configuration

Test restoration periodically on a separate machine.

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

## Troubleshooting

### Website does not open

- Confirm the Waitress service is running.
- Check the listening port with `Get-NetTCPConnection -LocalPort 8000`.
- Check Windows Firewall and the server LAN IP.
- Check `ALLOWED_HOSTS` and `APP_URL`.

### Scheduled email is not sent

- Confirm the scheduler service or repeating `send_emails` task is running.
- Confirm the schedule is enabled.
- Confirm at least one report and recipient group are selected.
- Confirm admin and unit-head addresses are valid.
- Run `python manage.py send_emails` and read its output.
- Confirm server time and `Asia/Kolkata` timezone.
- Check `logs\django.log` and SMTP provider logs.
- Remember `last_sent_at` prevents a second automatic send on the same local date.

### Test email fails

- Verify SMTP host, port, username, password, SSL, and TLS values.
- Use an app password when required by the provider.
- Confirm outbound SMTP traffic is allowed.
- Confirm the sender address is authorized.
- Rotate credentials if they were exposed.

### Database connection fails

- Confirm MySQL is running.
- Verify all `DB_*` values in `.env`.
- Confirm the MySQL user has privileges on `gplast_ticketsystemdb`.
- Test the connection using the MySQL client.

### Attachments fail

- Confirm `media\attachments\replies` and `media\attachments\reopen` exist.
- Confirm the service account has write permission.
- Confirm the reverse proxy request-size limit.
- Do not remove `media` during deployment.

### Desktop notifications do not appear

- Open the browser DevTools Console. Look for `[GPLAST] Notification permission granted.`
- If the message says `permission not granted`, click the padlock icon in the URL bar, set Notifications to **Allow**, and reload.
- On Windows, open Settings → System → Notifications & actions. Make sure the browser is enabled and Focus Assist is off.
- If nothing appears at all, confirm `static/js/shared/desktop_notifications.js` is loaded by checking the Sources tab in DevTools.
- Confirm the user has at least one row in the `tickets_notification` table.

### Archive page does not open

- Confirm `python manage.py check` passes.
- Confirm the four archive views are exported from `tickets/views/__init__.py`.
- Confirm `templates/admin_panel/archived_tickets.html` exists.
- Confirm `tickets/urls.py` includes the archive routes.
- Confirm the logged-in user is an administrator.

### Auto-archive does not run

- Run `python manage.py archive_old_tickets --days 90 --dry-run`. If it lists tickets, the command works.
- Check Windows Task Scheduler history for the archive job.
- Check `logs\django.log` for errors from the command.
- Confirm the service account running the task has read/write access to the project folder.

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

## Important Operational Note

The web server, the scheduled email worker, and the nightly archive job are three separate processes. Starting the Django web application alone does not send automatic scheduled emails and does not auto-archive tickets. Production must keep:

- The web service running (Waitress or IIS).
- The email scheduler service running, or a repeating `send_emails` task.
- The nightly archive task scheduled.
```

## Summary of changes vs your previous README

| Section | What changed |
|---|---|
| **Features** | Split into Core / Desktop notifications / Email notifications / Archive / Notifications history |
| **Folder structure** | Added `services/notify.py`, `notification_views.py`, `archive_old_tickets.py`, `desktop_notifications.js`, `archived_tickets.html`, new migration files, `media/attachments/replies/` |
| **Application Architecture** | Added sections for Desktop notifications and Ticket archive |
| **Important URLs** | Added `/custom-admin/archive/`, restore, bulk-restore, export-archived, and notification endpoints |
| **Create Python Environment** | Added `media\attachments\replies\` folder to writable list |
| **Auto-archive section** | New section describing the nightly command |
| **Windows Task Scheduler** | Added third task for nightly archive |
| **Troubleshooting** | Added Desktop notifications, Archive page, Auto-archive sections |
| **Operational note** | Now says "three separate processes" instead of two |
| **DB name consistency** | Changed `.env` example and backup commands to use `gplast_ticketsystemdb` (matches the CREATE DATABASE statement) |

Save this as `README.md` at the project root. Nothing else needs to change.