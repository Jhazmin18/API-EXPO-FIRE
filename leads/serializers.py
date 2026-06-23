from rest_framework import serializers

from .models import Lead


class LeadCreateSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=180)
    empresa = serializers.CharField(max_length=180)
    correo = serializers.EmailField()
    telefono = serializers.CharField(max_length=40)
    servicio = serializers.CharField(max_length=160)
    mensaje = serializers.CharField(required=False, allow_blank=True)
    captchaToken = serializers.CharField(write_only=True)


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id',
            'nombre',
            'empresa',
            'correo',
            'telefono',
            'servicio',
            'mensaje',
            'email_enviado',
            'created_at',
        ]
        read_only_fields = fields
