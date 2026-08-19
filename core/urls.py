from django.contrib import admin
from django.urls import path, include
from emails.views import dashboard_view, full_dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', full_dashboard_view, name='full-dashboard'), # <-- Nuevo Dashboard completo
    path('dashboard/sender/', dashboard_view, name='sender-dashboard'), # Mantener el anterior
    path('api/v1/emails/', include('emails.urls')),
]