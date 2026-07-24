from django.contrib import admin as django_admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from tickets import views as ticket_views # Import views to redirect root

urlpatterns = [
    # Redirect base URL to role-based dashboard/redirect
    path('', ticket_views.role_redirect, name='root_redirect'),

    # Custom Login
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    # Standard Admin Site (Superuser only) at /django-admin/
    path('django-admin/', django_admin.site.urls),
    
    # Tickets App URLs
    path('', include('tickets.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
