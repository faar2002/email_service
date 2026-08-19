# emails/urls.py
from django.urls import path
from .views import (SendEmailAPIView, 
    EmailStatusAPIView, 
    DashboardMetricsAPIView,
    CreateTemplateAPIView,
    CreateAPIKeyAPIView)

urlpatterns = [
    path('send/', SendEmailAPIView.as_view(), name='send-email'),
    path('status/<uuid:tracking_id>/', EmailStatusAPIView.as_view(), name='email-status'),
    path('metrics/', DashboardMetricsAPIView.as_view(), name='email-metrics'),
    path('templates/create/', CreateTemplateAPIView.as_view(), name='create-template'),
    path('keys/create/', CreateAPIKeyAPIView.as_view(), name='create-key'),
]