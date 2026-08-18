from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.template import Template, Context

from .serializers import SendEmailSerializer, EmailStatusSerializer
from .models import EmailLog, EmailTemplate
from .tasks import send_email_async
from .permissions import HasAPIKey
from .services import dispatch_email_async

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

        if data.get('template_code'):
            try:
                template_obj = EmailTemplate.objects.get(code=data['template_code'])
                subject = template_obj.subject
                django_template = Template(template_obj.body_html)
                body_html = django_template.render(Context(data.get('context', {})))
            except EmailTemplate.DoesNotExist:
                return Response(
                    {"error": f"Plantilla '{data['template_code']}' no encontrada."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

        # 1. Guardar log en PostgreSQL (Estado inicial: PENDING)
        log = EmailLog.objects.create(
            recipient=data['recipient'],
            subject=subject,
            body_html=body_html,
            attachment=attachment
        )

        # 2. Despachar el envío en un hilo secundario
        dispatch_email_async(str(log.id))

        # 3. Retornar respuesta inmediata al cliente HTTP
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