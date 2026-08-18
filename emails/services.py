# emails/services.py
import os
import threading
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from .models import EmailLog


def _send_email_thread(log_id):
    """
    Función que se ejecuta en un hilo secundario fuera de la petición HTTP.
    """
    try:
        log = EmailLog.objects.get(id=log_id)

        msg = EmailMultiAlternatives(
            subject=log.subject,
            body="Habilite la vista HTML para leer este correo.",
            to=[log.recipient]
        )
        msg.attach_alternative(log.body_html, "text/html")

        # Adjuntar archivo si existe
        if log.attachment and os.path.exists(log.attachment.path):
            msg.attach_file(log.attachment.path)

        msg.send()

        # Actualizar estado a ENVIADO
        log.status = 'SENT'
        log.sent_at = timezone.now()
        log.save()

    except EmailLog.DoesNotExist:
        pass
    except Exception as exc:
        # Registrar el error en PostgreSQL
        log.status = 'FAILED'
        log.error_message = str(exc)
        log.save()


def dispatch_email_async(log_id):
    """
    Inicia la ejecución del envío en un nuevo hilo sin bloquear el hilo principal de Django.
    """
    thread = threading.Thread(target=_send_email_thread, args=(log_id,))
    thread.daemon = True  # Permite que el proceso no se bloquee al apagar el servidor
    thread.start()