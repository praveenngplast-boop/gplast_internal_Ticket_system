# GPLAST ERP IT Support Ticket System

A production-grade, full-stack IT & ERP ticketing system built for **GPLAST** using **Django** and **MySQL**, designed with **Oracle-ready database compatibility** for future migration to Dell on-premise servers.

The application allows GPLAST employees to raise IT/ERP support tickets, and system administrators to manage, assign, escalate, and resolve them through a modern, responsive user interface.

---

## 🌟 Core System Features

### 1. Unified Authentication
- Single login screen [login.html](file:///d:/D/Desktop/final_pro/templates/login.html) for both Employees and Admins.
- Automatic role detection:
  - **Employee**: Redirected to Employee Dashboard. Can raise tickets and view own active cases + last 50 closed cases.
  - **Admin**: Redirected to operational Admin Panel. Full control over ticket workflows and system settings.

### 2. Automated Sequential Ticket Numbers
- Format: `GPLAST-YYYYMMDD-0001` (resets daily, padded to 4 digits).
- Generated safely on the server side using transactional logic in [utils.py](file:///d:/D/Desktop/final_pro/tickets/utils.py).

### 3. Comprehensive Forms & Validation
- **Mobile Number Validation**: Restricts input to exactly 10 digits (digits only, no spaces or special characters).
- **Minimum Threshold Validation**: Subject field restricted to 150 characters, and description must be at least 20 characters (both checked client-side via live counters and server-side).
- **Attachment Checker**: Client-side and server-side check for files under 3MB and formats: `pdf, doc, docx, xls, xlsx, png, jpg, jpeg`.
- **Administrative Logging**: Admins can log tickets on behalf of employees and specify reasons (Phone, Walk-in, Manager request, etc.).

### 4. Ticket Status Workflow
Only five allowed states:
1. **Open**: Default state upon ticket creation.
2. **Assigned**: Requires entering the assigned person name (visible to employee).
3. **Hold**: Requires a hold reason (visible on ticket timeline).
4. **Escalated**: Represents cases logged in the ERP vendor portal. Stores `escalated_at` timestamp and an optional Vendor Ticket Number.
5. **Closed**: Requires closing remarks, closed date, and the admin’s signature. Permanently logged (never deleted).

### 5. Personal Data Compliance
- Column list views in the Admin panel exclude personal identifiers (Mobile, Email, Employee ID, Screen Number) to prevent bulk data exposure.
- Detailed views are locked behind a "View" action button.

### 6. Interactive Admin Dashboard (10 Charts)
Utilizes **Chart.js** to render real-time visualizations for:
1. Status Distribution (Doughnut)
2. Unit-wise Tickets (Bar)
3. Department-wise Tickets (Horizontal Bar)
4. Priority Distribution (Pie)
5. Error Type Distribution (Pie)
6. Monthly Ticket Trend (Line)
7. Escalated vs Closed (Bar)
8. Average Resolution Time (hours) per Unit (Bar)
9. Top 10 Reported Issues (Bar)
10. Top Departments by Ticket Count (Bar)

### 7. Excel Report Generator
- Filter reports by Unit, Department, Status, Priority, Assigned Person, Date Ranges, and Vendor Ticket.
- Exports records directly into a designed layout spreadsheet using **openpyxl**.

### 8. Settings & Master Data Management
- Admin-extendable Units and Departments (automatically uppercased on save).
- Interactive toggle buttons to activate or deactivate units and departments.
- Configuration for the Employee support card details and system email notification lists.

### 9. Bootstrap Confirmation Modals
- Intercepts all critical actions (submissions, deactivations, status changes, exports) using custom Bootstrap modals.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- MySQL Server 8.0+

### Step 1: Clone and Initialize Venv
Clone the project directory onto your machine and initialize the virtual environment:
```powershell
# Navigate to workspace
cd d:/D/Desktop/final_pro

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Command Prompt:
.\venv\Scripts\activate.bat
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the root directory (based on `.env.example`):
```ini
# Django Settings
SECRET_KEY=django-insecure-gplast-secret-key-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL Database Settings
DB_NAME=gplast_db
DB_USER=root
DB_PASSWORD=Praxvn@7050
DB_HOST=127.0.0.1
DB_PORT=3306

# Email Settings (Defaults to Console backend, see SMTP section below)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Step 4: Run Migrations and Seed Data
Execute the database setup:
```powershell
# Create MySQL Database (if not exists)
mysql -u root -pPraxvn@7050 -e "CREATE DATABASE IF NOT EXISTS gplast_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Generate and apply migrations
python manage.py makemigrations
python manage.py migrate

# Seed defaults and 10 sample tickets
python manage.py seed_data
```

### Step 5: Start Server
```powershell
python manage.py runserver
```
Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and log in using:
- **Admin**: `admin` / `Admin@1234`
- **Employee**: `employee` / `Emp@1234`

---

## 🚀 Production Database Migration (MySQL ➜ Oracle DB)

To migrate the application database from MySQL to **Oracle DB** on the Dell on-premise server:

### 1. Install Oracle Client Libraries
Oracle DB requires the `oracledb` or `cx_Oracle` python connector. Update `requirements.txt` to include:
```text
oracledb>=2.0.0
```
Run: `pip install oracledb`

### 2. Update Database Settings in `settings.py`
Change the default engine to use Django's built-in Oracle backend:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'GPLAST_SERVICE_NAME',    # Oracle Service Name / SID
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='1521'),
    }
}
```

### 3. Update Environment Variables (`.env`)
```ini
DB_NAME=GPLAST_SERVICE_NAME
DB_USER=GPLAST_SCHEMA_USER
DB_PASSWORD=OracleSecurePassword123
DB_HOST=on-premise-oracle-ip
DB_PORT=1521
```

### 4. Run Migrations on Oracle
Apply migrations to build the tables under the Oracle schema:
```powershell
python manage.py migrate
python manage.py seed_data
```

> **Why this works seamlessly:** The models are defined using database-agnostic ORM fields (`CharField`, `TextField`, `DateTimeField`, `ForeignKey`, `BooleanField`). We avoided MySQL-specific structures (like JSONField or raw SQL dialect queries) ensuring a completely clean Oracle migration.

---

## 📧 Email Alerts Configuration (SMTP)

To enable email alerts for ticket creations and closures:

1. Update `.env` variables to point to your enterprise SMTP mail server:
```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com     # Or smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=support@gplast.com
EMAIL_HOST_PASSWORD=SecureMailPassword123
DEFAULT_FROM_EMAIL=GPLAST Support <support@gplast.com>
```

2. When a ticket is raised or closed, the system will automatically:
   - Send an alert to the employee’s email.
   - Fetch the active emails list from the `AdminNotificationEmail` table and BCC or carbon copy them.

---

## 🔒 Security and Compliance
- **Session Protection**: Passwords are saved with standard PBKDF2 hashing algorithms.
- **SQL Injection Prevention**: Built entirely on Django’s parameterized ORM layer.
- **CSRF Tokens**: Enabled across all submission forms.
- **Data Protection**: Personal contact and error logs are hidden on employee templates and list screens, restricting detail views to authorized admins only.
