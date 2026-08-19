from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.db.models import Count
from django.db import models
from django.shortcuts import render

from .serializers import SendEmailSerializer, EmailStatusSerializer
from .models import EmailLog, EmailTemplate, APIKey
from .permissions import HasAPIKey
from .services import dispatch_email_async

def full_dashboard_view(request):
    """
    Renderiza el Dashboard inyectando la API Key por defecto si existe.
    """
    default_key = getattr(settings, 'DEFAULT_DASHBOARD_API_KEY', '')
    
    return render(request, 'dashboard_full.html', {
        'default_api_key': default_key
    })

class CreateTemplateAPIView(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        code = request.data.get('code')
        subject = request.data.get('subject')
        body_html = request.data.get('body_html')

        if not code or not subject or not body_html:
            return Response(
                {"error": "Todos los campos (code, subject, body_html) son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if EmailTemplate.objects.filter(code=code).exists():
            return Response(
                {"error": f"Ya existe una plantilla con el código '{code}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        template = EmailTemplate.objects.create(
            code=code,
            subject=subject,
            body_html=body_html
        )

        return Response({
            "message": "Plantilla creada exitosamente.",
            "code": template.code
        }, status=status.HTTP_201_CREATED)


class CreateAPIKeyAPIView(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        name = request.data.get('name')

        if not name:
            return Response(
                {"error": "El nombre de la aplicación o sistema es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crea el registro; la clave de 64 caracteres se genera automáticamente en el save()
        api_key = APIKey.objects.create(name=name)

        return Response({
            "message": "API Key generada exitosamente.",
            "name": api_key.name,
            "key": api_key.key  # Se retorna completa solo al momento de la creación
        }, status=status.HTTP_201_CREATED)

class DashboardMetricsAPIView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request):
        stats = EmailLog.objects.aggregate(
            total=Count('id'),
            sent=Count('id', filter=models.Q(status='SENT')),
            failed=Count('id', filter=models.Q(status='FAILED')),
            pending=Count('id', filter=models.Q(status='PENDING')),
        )

        # Incluimos body_html en los logs
        logs = EmailLog.objects.all().order_by('-created_at')[:20]
        logs_data = [
            {
                "tracking_id": str(l.id),
                "recipient": l.recipient,
                "subject": l.subject,
                "body_html": l.body_html,
                "status": l.status,
                "error_message": l.error_message,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]

        # Incluimos body_html en las plantillas
        templates_qs = EmailTemplate.objects.all().order_by('-created_at')
        templates_data = [
            {
                "id": t.id,
                "code": t.code,
                "subject": t.subject,
                "body_html": t.body_html,
                "created_at": t.created_at.isoformat()
            }
            for t in templates_qs
        ]

        keys_qs = APIKey.objects.all().order_by('-created_at')
        keys_data = [
            {
                "id": k.id,
                "name": k.name,
                "key": k.key,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat()
            }
            for k in keys_qs
        ]

        return Response({
            'stats': stats,
            'logs': logs_data,
            'templates': templates_data,
            'api_keys': keys_data,
        }, status=status.HTTP_200_OK)
    
def dashboard_view(request):
    """
    Renderiza la interfaz gráfica del Dashboard.
    """
    return render(request, 'dashboard.html')

class SendEmailAPIView(APIView):
    permission_classes = [HasAPIKey]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject = data.get('subject')
        body_html = data.get('body_html')
        attachment = data.get('attachment')

        # Procesar si viene un código de plantilla registrada en PostgreSQL
        if data.get('template_code'):
            try:
                template_obj = EmailTemplate.objects.get(code=data['template_code'])
                context_data = Context(data.get('context', {}))

                # Renderizar las variables {{ ... }} en el ASUNTO
                subject_template = Template(template_obj.subject)
                subject = subject_template.render(context_data)

                # Renderizar las variables {{ ... }} en el CUERPO HTML
                body_template = Template(template_obj.body_html)
                body_html = body_template.render(context_data)

            except EmailTemplate.DoesNotExist:
                return Response(
                    {"error": f"Plantilla '{data['template_code']}' no encontrada."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

        # 1. Guardar log en PostgreSQL con el asunto y cuerpo renderizados
        log = EmailLog.objects.create(
            recipient=data['recipient'],
            subject=subject,
            body_html=body_html,
            attachment=attachment
        )

        # 2. Despachar el envío en hilo secundario
        dispatch_email_async(str(log.id))

        return Response(
            {
                "message": "Solicitud de correo recibida.",
                "tracking_id": str(log.id)
            }, 
            status=status.HTTP_202_ACCEPTED
        )

class EmailStatusAPIView(APIView):
    permission_classes = [HasAPIKey]  # Misma protección mediante X-API-KEY

    def get(self, request, tracking_id):
        # Busca el registro por el UUID; si no existe, retorna 404 Not Found
        log = get_object_or_404(EmailLog, id=tracking_id)
        serializer = EmailStatusSerializer(log)
        return Response(serializer.data, status=status.HTTP_200_OK)