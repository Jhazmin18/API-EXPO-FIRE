# serializers.py
from rest_framework import serializers
from .models import Empresa, Contacto
from usuarios.models import Perfil

class ContactoSerializer(serializers.ModelSerializer):
    """Serializer para los contactos de la empresa"""
    class Meta:
        model = Contacto
        fields = [
            'id',
            'nombre',
            'cargo',
            'correo_principal',
            'correo_secundario',
            'telefono_principal',
            'telefono_secundario',
            'domicilio',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ContactoCreacionSerializer(serializers.ModelSerializer):
    """Serializer auxiliar para crear contactos desde empresas."""
    class Meta:
        model = Contacto
        fields = [
            'nombre',
            'cargo',
            'correo_principal',
            'correo_secundario',
            'telefono_principal',
            'telefono_secundario',
            'domicilio',
        ]


class EmpresaSerializer(serializers.ModelSerializer):
    """Serializer principal para empresas."""

    creado_por_nombre = serializers.SerializerMethodField()
    creado_por_email = serializers.EmailField(source='creado_por.email', read_only=True)
    creado_por_rol = serializers.SerializerMethodField()
    contactos = ContactoSerializer(many=True, read_only=True)

    class Meta:
        model = Empresa
        fields = [
            # Campos básicos
            'id',
            'nombre',
            'razon_social',
            'logo',
            'tipo_inmueble',
            'activa',
            'created_at',

            # Datos del técnico creador
            'creado_por',
            'creado_por_nombre',
            'creado_por_email',
            'creado_por_rol',

            # Metrajes
            'metros_cuadrados_totales',
            'perimetro',
            'metros_cuadrados_estacionamiento',
            'cajones_estacionamiento',

            # Evaluación
            'en_establecimiento',
            'datos_quien_refiere',
            'fecha_evaluacion_riesgo',

            # Materiales
            'materiales_combustibles',

            # Contactos
            'contactos',
        ]
        read_only_fields = ['id', 'created_at', 'creado_por']

    def get_creado_por_nombre(self, obj):
        """Nombre completo del técnico que registró la empresa."""
        if obj.creado_por:
            perfil = getattr(obj.creado_por, 'perfil', None)
            if perfil and perfil.nombre_completo:
                return perfil.nombre_completo
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return None

    def get_creado_por_rol(self, obj):
        """Rol del técnico que registró la empresa."""
        if obj.creado_por:
            perfil = getattr(obj.creado_por, 'perfil', None)
            if perfil:
                return {
                    'codigo': perfil.rol,
                    'nombre': perfil.get_rol_display()
                }
        return None


class EmpresaCreacionSerializer(serializers.ModelSerializer):
    """Serializer especial para crear empresa con contactos iniciales"""
    contactos = ContactoCreacionSerializer(many=True, write_only=True)
    
    class Meta:
        model = Empresa
        fields = [
            'nombre',
            'razon_social',
            'logo',
            'tipo_inmueble',
            'activa',
            'creado_por',
            'metros_cuadrados_totales',
            'perimetro',
            'metros_cuadrados_estacionamiento',
            'cajones_estacionamiento',
            'en_establecimiento',
            'datos_quien_refiere',
            'fecha_evaluacion_riesgo',
            'materiales_combustibles',
            'contactos',
        ]
        read_only_fields = ['creado_por']
    
    def create(self, validated_data):
        contactos_data = validated_data.pop('contactos', [])
        
        # Crear la empresa (creado_por se asignará en el viewset)
        empresa = Empresa.objects.create(**validated_data)
        
        # Crear cada contacto asociado
        for contacto_data in contactos_data:
            Contacto.objects.create(
                empresa=empresa,
                **contacto_data
            )
        
        return empresa


class EmpresaResumenSerializer(serializers.Serializer):
    """Serializer para el resumen de empresas"""
    total = serializers.IntegerField()
    activas = serializers.IntegerField()
    inactivas = serializers.IntegerField()
    registros_por_tecnico = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
