# GPLAST Internal Ticket System

This is the internal ticketing and support system for GPLAST ERP. It allows for tracking, managing, and resolving support requests from various departments.

## Project Structure

*   **Admin Dashboard:** A comprehensive overview of ticket statistics with interactive charts.
*   **Ticket Management:** Create, view, update, and close support tickets.
*   **User & Department Management:** Configure units, departments, and employee access.
*   **Audit & Reporting:** Track all system changes and export detailed ticket reports.
*   **Notification System:** Real-time updates on new and unread tickets.

## Technologies Used

*   **Backend:** Django
*   **Database:** MySQL
*   **Frontend:**
    *   Django Templates
    *   Bootstrap 5
    *   FontAwesome 6
    *   Chart.js
*   **Deployment:** Whitenoise (for static files)
*   **Configuration:** `python-decouple` (for environment variables)


## Project Structure

### Backend (Django)

```
gplast_internal_Ticket_system/
├── gplast_internal_Ticket_system/   # Main Django project folder
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                  # Project settings
│   ├── urls.py                      # Root URL configuration
│   └── wsgi.py                      # WSGI entry-point
│
├── tickets/                         # Core application for ticket management
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/                  # Database migration files
│   ├── models.py                    # Database models for tickets, history, etc.
│   ├── tests.py
│   └── views.py                     # Application logic and views
│
├── manage.py                        # Django's command-line utility
└── requirements.txt                 # Project dependencies
```

### Frontend (Templates & Static Files)

```
gplast_internal_Ticket_system/
├── static/                          # Static files (CSS, JavaScript, Images)
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── ...
│
├── templates/                       # HTML templates
│   ├── base.html                    # Base template for all pages
│   ├── login.html
│   └── admin_panel/                 # Templates for the admin interface
│       ├── dashboard.html
│       ├── create_ticket.html
│       ├── all_tickets.html
│       ├── ticket_detail.html
│       ├── reports.html
│       ├── audit_log.html
│       ├── settings_index.html
│       ├── units_departments.html
│       ├── dept_employees.html
│       ├── communication.html
│       ├── employees.html
│       ├── credentials.html
│       ├── _notification_items.html # Partial template for notifications
│       └── _ticket_list_modal.html  # Partial template for modal ticket lists
```

## Key Features

*   **Admin Dashboard:** A comprehensive overview of ticket statistics with interactive charts.
*   **Ticket Management:** Create, view, update, and close support tickets.
*   **User & Department Management:** Configure units, departments, and employee access.
*   **Audit & Reporting:** Track all system changes and export detailed ticket reports.
*   **Notification System:** Real-time updates on new and unread tickets.