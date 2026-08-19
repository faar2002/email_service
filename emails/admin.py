from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import admin
from django.contrib import messages
from django.utils.safestring import mark_safe
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
    readonly_fields = ('id', 'created_at', 'sent_at', 'error_message', 'preview_body_html')
    fields = ('id', 'recipient', 'subject', 'status', 'error_message', 'created_at', 'sent_at', 'preview_body_html')
    actions = [retry_failed_emails]

    @admin.display(description="Previsualización del Correo")
    def preview_body_html(self, obj):
        if obj.body_html:
            # Renderiza el código HTML dentro de un contenedor seguro con borde de lectura
            return mark_safe(
                f'<div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:20px; max-width:650px;">'
                f'{obj.body_html}'
                f'</div>'
            )
        return "Sin contenido HTML"

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'subject', 'created_at')
    search_fields = ('code', 'subject')
    readonly_fields = ('preview_template_html',)
    fields = ('code', 'subject', 'body_html', 'preview_template_html')

    @admin.display(description="Previsualización de la Plantilla")
    def preview_template_html(self, obj):
        if obj.body_html:
            return mark_safe(
                f'<div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:20px; max-width:650px;">'
                f'{obj.body_html}'
                f'</div>'
            )
        return "Sin código HTML"


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'is_active', 'created_at')
    readonly_fields = ('key',)  # Evita modificar la clave generada manualmente