# emails/permissions.py
from rest_framework import permissions
from .models import APIKey

class HasAPIKey(permissions.BasePermission):
    """
    Permiso personalizado que verifica si la petición incluye un encabezado 'X-API-KEY' válido.
    """
    def has_permission(self, request, view):
        # Leer el encabezado X-API-KEY de la petición HTTP
        api_key_header = request.headers.get('X-API-KEY')

        if not api_key_header:
            return False

        # Validar si existe en la base de datos y está activa
        return APIKey.objects.filter(key=api_key_header, is_active=True).exists()