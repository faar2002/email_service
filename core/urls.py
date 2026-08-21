from django.contrib import admin
from django.urls import path, include
from emails.views import (
    full_dashboard_view, 
    dashboard_view, 
    custom_login_view, 
    custom_logout_view
)

urlpatterns = [
    # Autenticación Personalizada
    path('login/', custom_login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),

    # Rutas de Dashboards Protegidos
    path('dashboard/', full_dashboard_view, name='full-dashboard'),
    path('dashboard/sender/', dashboard_view, name='sender-dashboard'),

    path('admin/', admin.site.urls),
    path('api/v1/emails/', include('emails.urls')),
]