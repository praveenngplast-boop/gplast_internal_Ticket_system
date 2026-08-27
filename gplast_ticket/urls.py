# gplast_ticket/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tickets.views import role_redirect

urlpatterns = [
    # ✅ Django admin (stays at /admin/)
    path('admin/', admin.site.urls),
    
    # ✅ Root redirect
    path('', role_redirect, name='root_redirect'),
    
    # ✅ Accounts (login, logout, password reset)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # ✅ Tickets app (all custom URLs including admin, employee, unit_head)
    path('', include('tickets.urls')),
]

# ✅ Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)