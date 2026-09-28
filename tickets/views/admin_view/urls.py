from django.urls import path
from . import views

app_name = 'admin_view'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('tickets/', views.tickets_page, name='ticket_list'),
    path('tickets/<int:ticket_id>/', views.tickets_page, name='ticket_detail'),

    path('tickets/<int:ticket_id>/comment/',  views.add_comment,     name='add_comment'),
    path('tickets/<int:ticket_id>/priority/', views.change_priority, name='change_priority'),

    path('tickets/<int:pk>/excel/', views.download_ticket_excel, name='download_ticket_excel'),
    path('tickets/<int:pk>/csv/',   views.download_ticket_csv,   name='download_ticket_csv'),

    path('reports/',              views.reports,     name='reports'),
    path('reports/export/csv/',   views.export_csv,  name='export_csv'),
    path('reports/export/xlsx/',  views.export_xlsx, name='export_xlsx'),
]