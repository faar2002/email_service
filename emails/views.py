from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt  
from django.utils.decorators import method_decorator  
from django.conf import settings
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.db.models import Count
from django.db import models
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .serializers import SendEmailSerializer, EmailStatusSerializer
from .models import EmailLog, EmailTemplate, APIKey
from .permissions import HasAPIKey
from .services import dispatch_email_async

def custom_login_view(request):
    """
    Vista de inicio de sesión personalizada para el Dashboard.
    """
    if request.user.is_authenticated:
        return redirect('full-dashboard')

    error_message = None

    if request.method == 'POST':
        # En vistas estándar HTML de Django se usa request.POST
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)

        if user is not None:
            login(request, user)
            return redirect('full-dashboard')
        else:
            error_message = "Usuario o contraseña incorrectos."

    return render(request, 'login.html', {'error_message': error_message})


def custom_logout_view(request):
    """
    Cierra la sesión y redirige al login.
    """
    logout(request)
    return redirect('login')

@login_required(login_url='/login/')
def full_dashboard_view(request):
    """
    Dashboard General protegido por inicio de sesión.
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
        # Páginas independientes para cada pestaña
        logs_page = request.query_params.get('logs_page', 1)
        tpl_page = request.query_params.get('tpl_page', 1)
        keys_page = request.query_params.get('keys_page', 1)
        page_size = 10

        # 1. Estadísticas
        stats = EmailLog.objects.aggregate(
            total=Count('id'),
            sent=Count('id', filter=models.Q(status='SENT')),
            failed=Count('id', filter=models.Q(status='FAILED')),
            pending=Count('id', filter=models.Q(status='PENDING')),
        )

        # 2. Paginación Email Logs
        logs_qs = EmailLog.objects.all().order_by('-created_at')
        logs_paginator = Paginator(logs_qs, page_size)
        logs_obj = logs_paginator.get_page(logs_page)

        # 3. Paginación Plantillas
        tpl_qs = EmailTemplate.objects.all().order_by('-created_at')
        tpl_paginator = Paginator(tpl_qs, page_size)
        tpl_obj = tpl_paginator.get_page(tpl_page)

        # 4. Paginación API Keys
        keys_qs = APIKey.objects.all().order_by('-created_at')
        keys_paginator = Paginator(keys_qs, page_size)
        keys_obj = keys_paginator.get_page(keys_page)

        return Response({
            'stats': stats,
            'logs': [
                {
                    "tracking_id": str(l.id),
                    "recipient": l.recipient,
                    "subject": l.subject,
                    "body_html": l.body_html,
                    "status": l.status,
                    "error_message": l.error_message,
                    "created_at": l.created_at.isoformat()
                } for l in logs_obj.object_list
            ],
            'logs_pagination': {
                'current_page': logs_obj.number,
                'total_pages': logs_paginator.num_pages,
                'has_next': logs_obj.has_next(),
                'has_previous': logs_obj.has_previous(),
                'total_records': logs_paginator.count
            },
            'templates': [
                {
                    "id": t.id,
                    "code": t.code,
                    "subject": t.subject,
                    "body_html": t.body_html,
                    "created_at": t.created_at.isoformat()
                } for t in tpl_obj.object_list
            ],
            'templates_pagination': {
                'current_page': tpl_obj.number,
                'total_pages': tpl_paginator.num_pages,
                'has_next': tpl_obj.has_next(),
                'has_previous': tpl_obj.has_previous(),
                'total_records': tpl_paginator.count
            },
            'api_keys': [
                {
                    "id": str(k.id),  # <-- Convertir explícitamente a string (Soporta UUID y CharField)
                    "name": k.name,
                    "key": k.key,
                    "is_active": k.is_active,
                    "created_at": k.created_at.isoformat()
                } for k in keys_obj.object_list
            ],
            'keys_pagination': {
                'current_page': keys_obj.number,
                'total_pages': keys_paginator.num_pages,
                'has_next': keys_obj.has_next(),
                'has_previous': keys_obj.has_previous(),
                'total_records': keys_paginator.count
            }
        }, status=status.HTTP_200_OK)

class UpdateTemplateAPIView(APIView):
    authentication_classes = []
    permission_classes = [HasAPIKey]

    def put(self, request, template_id):
        try:
            template = EmailTemplate.objects.get(id=template_id)
        except EmailTemplate.DoesNotExist:
            return Response({"error": "Plantilla no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        template.subject = request.data.get('subject', template.subject)
        template.body_html = request.data.get('body_html', template.body_html)
        template.save()

        return Response({"message": "Plantilla actualizada exitosamente."}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ToggleAPIKeyAPIView(APIView):
    authentication_classes = []
    permission_classes = [HasAPIKey]

    def patch(self, request, key_id):
        try:
            api_key = APIKey.objects.get(id=key_id)
        except APIKey.DoesNotExist:
            return Response(
                {"error": f"API Key con ID {key_id} no encontrada."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Alternar el estado activo / inactivo
        api_key.is_active = not api_key.is_active
        api_key.save()

        return Response({
            "message": f"API Key '{api_key.name}' {'activada' if api_key.is_active else 'desactivada'} con éxito.",
            "is_active": api_key.is_active
        }, status=status.HTTP_200_OK)
    
@xframe_options_sameorigin    
@login_required(login_url='/login/')
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