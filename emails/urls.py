# emails/urls.py
from django.urls import path
from .views import SendEmailAPIView, EmailStatusAPIView

urlpatterns = [
    path('send/', SendEmailAPIView.as_view(), name='send-email'),
    path('status/<uuid:tracking_id>/', EmailStatusAPIView.as_view(), name='email-status'),
]