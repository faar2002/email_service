from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import admin
from django.contrib import messages
from .models import EmailTemplate, EmailLog, APIKey
from .services import dispatch_email_async

@admin.action(description="Reintentar envío de correos seleccionados (Solo FAILED)")
def retry_failed_emails(modeladmin, request, queryset):
    failed_emails = queryset.filter(status='FAILED')
    count = failed_emails.count()

    if count == 0:
        modeladmin.message_user(
            request, 
            "No se seleccionó ningún correo en estado 'FAILED'.", 
            level=messages.WARNING
        )
        return

    for log in failed_emails:
        log.status = 'PENDING'
        log.error_message = None
        log.save()
        dispatch_email_async(str(log.id))

    modeladmin.message_user(
        request, 
        f"Se han re-encolado exitosamente {count} correo(s) para su envío.", 
        level=messages.SUCCESS
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'status', 'created_at', 'sent_at')
    list_filter = ('status', 'created_at')
    search_fields = ('recipient', 'subject', 'id')
    readonly_fields = ('id', 'created_at', 'sent_at', 'error_message')
    actions = [retry_failed_emails]

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'subject', 'created_at')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'is_active', 'created_at')
    readonly_fields = ('key',)  # Evita modificar la clave generada manualmente