# emails/models.py
import uuid
import secrets
from django.db import models

class EmailTemplate(models.Model):
    code = models.CharField(max_length=100, unique=True, help_text="Ej: OTP_VALIDATION, WELCOME_USER")
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.subject}"


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('FAILED', 'Fallido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    attachment = models.FileField(upload_to='email_attachments/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} | {self.subject} | {self.status}"

class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nombre del servicio o cliente cliente (ej: App Ventas)")
    key = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            # Genera una clave segura de 32 bytes (64 caracteres hexadecimales)
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'Activa' if self.is_active else 'Inactiva'})"