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
    
    # ✅ Accounts
    path('accounts/', include('django.contrib.auth.urls')),
    
    # ✅ Tickets app (custom URLs)
    path('', include('tickets.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)