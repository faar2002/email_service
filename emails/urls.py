# emails/urls.py
from django.urls import path
from .views import (
    SendEmailAPIView, 
    EmailStatusAPIView, 
    DashboardMetricsAPIView,
    CreateTemplateAPIView,
    CreateAPIKeyAPIView,
    UpdateTemplateAPIView,
    ToggleAPIKeyAPIView
)

urlpatterns = [
    path('send/', SendEmailAPIView.as_view(), name='send-email'),
    path('status/<uuid:tracking_id>/', EmailStatusAPIView.as_view(), name='email-status'),
    path('metrics/', DashboardMetricsAPIView.as_view(), name='email-metrics'),
    path('templates/create/', CreateTemplateAPIView.as_view(), name='create-template'),
    path('templates/<int:template_id>/update/', UpdateTemplateAPIView.as_view(), name='update-template'),
    path('keys/create/', CreateAPIKeyAPIView.as_view(), name='create-key'),
    path('keys/<str:key_id>/toggle/', ToggleAPIKeyAPIView.as_view(), name='toggle-key')
]