# emails/tasks.py
import os
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from .models import EmailLog

@shared_task(bind=True, max_retries=3)
def send_email_async(self, log_id):
    try:
        log = EmailLog.objects.get(id=log_id)
        
        msg = EmailMultiAlternatives(
            subject=log.subject,
            body="Habilite la vista HTML para leer este correo.",
            to=[log.recipient]
        )
        msg.attach_alternative(log.body_html, "text/html")

        # Verificar y adjuntar archivo si existe
        if log.attachment and os.path.exists(log.attachment.path):
            msg.attach_file(log.attachment.path)

        msg.send()

        log.status = 'SENT'
        log.sent_at = timezone.now()
        log.save()
    except EmailLog.DoesNotExist:
        pass
    except Exception as exc:
        log.status = 'FAILED'
        log.error_message = str(exc)
        log.save()
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))