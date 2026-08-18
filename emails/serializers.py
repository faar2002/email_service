from rest_framework import serializers
from .models import EmailLog

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

class SendEmailSerializer(serializers.Serializer):
    recipient = serializers.EmailField()
    subject = serializers.CharField(max_length=255, required=False)
    template_code = serializers.CharField(required=False)
    context = serializers.DictField(required=False, default=dict)
    body_html = serializers.CharField(required=False)
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate_attachment(self, value):
        if value and value.size > MAX_FILE_SIZE_BYTES:
            size_mb = round(value.size / (1024 * 1024), 2)
            raise serializers.ValidationError(
                f"El archivo adjunto supera el límite de 10 MB (Tamaño actual: {size_mb} MB)."
            )
        return value

    def validate(self, data):
        if not data.get('template_code') and not (data.get('subject') and data.get('body_html')):
            raise serializers.ValidationError(
                "Debe proporcionar 'template_code' o la combinación de 'subject' y 'body_html'."
            )
        return data
    
class EmailStatusSerializer(serializers.ModelSerializer):
    tracking_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = EmailLog
        fields = ['tracking_id', 'recipient', 'subject', 'status', 'error_message', 'sent_at', 'created_at']