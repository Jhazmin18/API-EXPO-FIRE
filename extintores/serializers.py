# serializers.py
"""
Serializadores de la API REST para extintores.

Este módulo define los serializadores de Django REST Framework
que convierten los modelos en JSON y viceversa.
"""
from rest_framework import serializers
from .models import Extintor
from empresas.models import Empresa
from empresas.serializers import EmpresaSerializer
from usuarios.models import Perfil


class ExtintorSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Extintor.
    
    Incluye todos los campos del modelo más los campos calculados
    como estado, días_para_vencer, etc.
    """
    
    # Campos calculados (read-only)
    estado = serializers.ReadOnlyField()
    dias_para_vencer = serializers.ReadOnlyField()
    dias_para_revision = serializers.ReadOnlyField()
    
    empresa = serializers.SerializerMethodField()
    empresa_id = serializers.UUIDField(write_only=True, required=False)
    qr_code_url = serializers.SerializerMethodField()
    
    # --- NUEVOS: Información del creador ---
    creado_por_nombre = serializers.SerializerMethodField()
    creado_por_email = serializers.EmailField(source='creado_por.email', read_only=True)
    creado_por_rol = serializers.SerializerMethodField()
    
    class Meta:
        model = Extintor
        fields = [
            'id',
            'codigo',
            'ubicacion',
            'tipo',
            'capacidad',
            'fecha_fabricacion',
            'fecha_vencimiento',
            'ultima_revision',
            'proxima_revision',
            'observaciones',
            'qr_code',
            'arena',
            'fecha_prueba_hidrostatica',
            'qr_code_url',
            'estado',
            'dias_para_vencer',
            'dias_para_revision',
            'created_at',
            'updated_at',
            'empresa',
            'empresa_id',
            # --- NUEVOS ---
            'creado_por',
            'creado_por_nombre',
            'creado_por_email',
            'creado_por_rol',
        ]
        read_only_fields = ['id', 'qr_code', 'created_at', 'updated_at', 'creado_por']
    
    def get_qr_code_url(self, obj):
        """
        Obtiene la URL completa del QR code.
        """
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
            return obj.qr_code.url
        return None

    def get_empresa(self, obj):
        if obj.empresa:
            serializer = EmpresaSerializer(obj.empresa)
            return serializer.data
        return None
    
    # --- NUEVOS MÉTODOS ---
    def get_creado_por_nombre(self, obj):
        """Obtiene el nombre completo del usuario que creó el extintor"""
        if obj.creado_por:
            perfil = getattr(obj.creado_por, 'perfil', None)
            if perfil:
                return perfil.nombre_completo
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return None
    
    def get_creado_por_rol(self, obj):
        """Obtiene el rol del usuario que creó el extintor"""
        if obj.creado_por:
            perfil = getattr(obj.creado_por, 'perfil', None)
            if perfil:
                return {
                    'codigo': perfil.rol,
                    'nombre': perfil.get_rol_display()
                }
        return None


class ExtintorListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para la lista de extintores.
    
    Solo incluye los campos esenciales para mejorar el rendimiento
    en listados grandes.
    """
    
    estado = serializers.ReadOnlyField()
    empresa = serializers.SerializerMethodField()
    
    # --- NUEVO: Nombre del creador para listados ---
    creado_por_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Extintor
        fields = [
            'id',
            'codigo',
            'ubicacion',
            'tipo',
            'capacidad',
            'fecha_vencimiento',
            'proxima_revision',
            'estado',
            'empresa',
            'arena',
            'fecha_prueba_hidrostatica',
            # --- NUEVO ---
            'creado_por_nombre',
        ]

    def get_empresa(self, obj):
        if obj.empresa:
            return obj.empresa.nombre
        return None
    
    # --- NUEVO MÉTODO ---
    def get_creado_por_nombre(self, obj):
        """Obtiene el nombre del creador para listados"""
        if obj.creado_por:
            perfil = getattr(obj.creado_por, 'perfil', None)
            if perfil:
                return perfil.nombre_completo
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return None


class ExtintorCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para la creación de extintores.
    
    No requiere el campo QR code ya que se genera automáticamente.
    """
    
    class Meta:
        model = Extintor
        fields = [
            'id',
            'codigo',
            'ubicacion',
            'tipo',
            'capacidad',
            'fecha_fabricacion',
            'fecha_vencimiento',
            'ultima_revision',
            'proxima_revision',
            'observaciones',
            'arena',
            'fecha_prueba_hidrostatica',
            'empresa_id',
        ]
        read_only_fields = ['id']
    
    def validate_codigo(self, value):
        """
        Valida que el código sea único.
        """
        if Extintor.objects.filter(codigo=value).exists():
            raise serializers.ValidationError("Ya existe un extintor con este código.")
        return value

    def create(self, validated_data):
        empresa_id = validated_data.pop('empresa_id', None)
        empresa = None
        if empresa_id:
            empresa = Empresa.objects.filter(id=empresa_id).first()
            if not empresa:
                raise serializers.ValidationError({'empresa_id': 'Empresa no encontrada.'})
        
        # El campo creado_por se asignará en el viewset
        extintor = Extintor.objects.create(empresa=empresa, **validated_data)
        return extintor