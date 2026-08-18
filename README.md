# ✉️ Servicio Centralizado de Correo Electrónico (Django REST API)

Un microservicio desacoplado y de alto rendimiento construido con **Django REST Framework** y **PostgreSQL** para gestionar el envío asíncrono de correos electrónicos (HTML, plantillas dinámicas y archivos adjuntos) para múltiples aplicaciones y servicios.

---

## 🚀 Características Principales

- **Arquitectura Asíncrona (Non-blocking):** Despacho de correos en segundo plano utilizando hilos (`threading`), ofreciendo respuestas inmediatas (`202 Accepted`).
- **Soporte para Adjuntos:** Recepción y validación de documentos/archivos de hasta **10 MB** (`multipart/form-data`).
- **Plantillas Dinámicas:** Renderizado de plantillas HTML almacenadas en la base de datos con contexto JSON configurable.
- **Trazabilidad y Logs:** Registro completo de cada envío (`PENDING`, `SENT`, `FAILED`) y almacenamiento de mensajes de error de Google SMTP.
- **Autenticación por API Key:** Protección de endpoints mediante encabezado HTTP `X-API-KEY`.
- **Configuración por Ambientes:** Entornos totalmente segregados (`local`, `qa`, `prod`) usando `django-environ`.

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Framework Web:** Django / Django REST Framework (DRF)
- **Base de Datos:** PostgreSQL
- **Proveedor SMTP:** Google / Gmail SMTP
- **Autenticación:** Personalizada basada en modelo `APIKey`

---

## 📂 Estructura del Proyecto

```text
email_service/
├── core/
│   ├── settings/
│   │   ├── base.py       # Configuración compartida
│   │   ├── local.py      # Entorno de desarrollo local
│   │   ├── qa.py         # Entorno de pruebas
│   │   └── prod.py       # Entorno de producción
│   ├── urls.py
│   └── wsgi.py
├── emails/
│   ├── models.py         # Modelos EmailLog, EmailTemplate y APIKey
│   ├── permissions.py    # Clase HasAPIKey para DRF
│   ├── serializers.py    # Validaciones y limites de adjuntos
│   ├── services.py       # Despacho asíncrono con threading
│   ├── views.py          # APIViews para envío y status
│   └── urls.py
├── media/                # Almacenamiento temporal de adjuntos
├── .env                  # Variables de entorno (No commitear)
├── manage.py
└── requirements.txt
⚙️ Configuración e Instalación1. Clonar el repositorio y crear el entorno virtualBashgit clone [https://github.com/tu-usuario/email-service.git](https://github.com/tu-usuario/email-service.git)
cd email-service

python -m venv venv
source venv/bin/activate  # En Linux/macOS
# venv\Scripts\activate   # En Windows
2. Instalar dependenciasBashpip install -r requirements.txt
3. Configurar variables de entorno (.env)Crea un archivo .env en la raíz del proyecto basándote en el siguiente ejemplo:Fragmento de código# Configuración del Entorno
DJANGO_SETTINGS_MODULE=core.settings.local
DJANGO_SECRET_KEY=tu_clave_secreta_local

# Base de Datos PostgreSQL
DATABASE_URL=postgres://postgres:postgres@localhost:5432/email_db_local

# Configuración Google SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion_16_caracteres
DEFAULT_FROM_EMAIL=Servicio de Correos <tu_correo@gmail.com>
4. Ejecutar migraciones y crear superusuarioBashpython manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
5. Iniciar el servidor de desarrolloBashpython manage.py runserver --settings=core.settings.local
🔑 Gestión de API KeysPara autorizar a otros microservicios a consumir la API:Accede al panel de administración en http://127.0.0.1:8000/admin/.Ve a la sección API Keys y crea un nuevo registro para el servicio consumidor (ej: Servicio Usuarios).Copia la key hexadecimal de 64 caracteres generada automáticamente.📋 Referencia de la APITodos los endpoints requieren el encabezado HTTP: X-API-KEY: <tu_api_key>1. Enviar Correo ElectrónicoURL: /api/v1/emails/send/Méndodo: POSTContent-Type: multipart/form-data o application/jsonParámetros:CampoTipoRequeridoDescripciónrecipientstringSíCorreo electrónico de destino.subjectstringCondicionalAsunto del correo (obligatorio si no usa plantilla).body_htmlstringCondicionalCuerpo del correo en HTML (obligatorio si no usa plantilla).template_codestringCondicionalCódigo de la plantilla registrada en la BD.contextjsonNoDiccionario de variables para renderizar en la plantilla.attachmentfileNoArchivo adjunto (máximo 10 MB).Ejemplo de Petición (cURL):Bashcurl -X POST [http://127.0.0.1:8000/api/v1/emails/send/](http://127.0.0.1:8000/api/v1/emails/send/) \
  -H "X-API-KEY: e7b2a194f83c091d...tu_api_key" \
  -F "recipient=usuario@ejemplo.com" \
  -F "subject=Factura de Compra" \
  -F "body_html=<h1>Adjunto comprobante</h1>" \
  -F "attachment=@/ruta/factura.pdf"
Respuesta Exitosa (HTTP 202 Accepted):JSON{
  "message": "Solicitud de correo recibida.",
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000"
}
2. Consultar Estado del EnvíoURL: /api/v1/emails/status/<uuid:tracking_id>/Método: GETRespuesta Exitosa (HTTP 200 OK):JSON{
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipient": "usuario@ejemplo.com",
  "subject": "Factura de Compra",
  "status": "SENT",
  "error_message": null,
  "sent_at": "2026-08-18T18:30:00Z",
  "created_at": "2026-08-18T18:29:58Z"
}
🛠️ Reintentos desde el Panel de AdministraciónSi un envío falla (por ejemplo, debido a desconexión SMTP temporal):Ingresa al Django Admin en /admin/emails/emaillog/.Filtra por el estado FAILED.Selecciona los registros afectados y ejecuta la acción masiva: "Reintentar envío de correos seleccionados (Solo FAILED)".
<ElicitationsGroup message="¿Deseas agregar alguna otra sección al README o pasar al despliegue?">

  <Elicitation label="Configurar Docker y Docker Compose para este servicio" query="¿Cómo configurar Docker y Docker Compose para este servicio de correo en Django con PostgreSQL diferenciando ambientes sin Celery ni Redis?"/>

  <Elicitation label="Crear una librería cliente de Python para consumir el servicio" query="¿Cómo crear un paquete o módulo cliente de Python para consumir fácilmente este servicio de correo desde otros proyectos Django?"/>

</ElicitationsGroup>