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


class CodigoUnicoPorEmpresaMixin:
    def _resolve_empresa_for_codigo(self):
        if getattr(self, 'instance', None) and getattr(self.instance, 'empresa_id', None):
            return self.instance.empresa

        initial_data = getattr(self, 'initial_data', {}) or {}
        empresa_id = initial_data.get('empresa_id')
        if empresa_id not in (None, ''):
            return Empresa.objects.filter(id=empresa_id).first()

        request = self.context.get('request')
        perfil = getattr(getattr(request, 'user', None), 'perfil', None) if request else None
        if perfil and perfil.empresa_id:
            return perfil.empresa

        return None

    def validate_codigo(self, value):
        empresa = self._resolve_empresa_for_codigo()
        queryset = Extintor.objects.filter(codigo=value)

        if empresa is None:
            queryset = queryset.filter(empresa__isnull=True)
        else:
            queryset = queryset.filter(empresa=empresa)

        if getattr(self, 'instance', None):
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Ya existe un extintor con este código en la empresa seleccionada."
            )
        return value


class ExtintorSerializer(CodigoUnicoPorEmpresaMixin, serializers.ModelSerializer):
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
    empresa_id = serializers.IntegerField(source='empresa.id', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    revisiones = serializers.SerializerMethodField()
    revisiones_total = serializers.SerializerMethodField()
    
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
            'modalidad',
            'clase_fuego',
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
            'revisiones',
            'revisiones_total',
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

    def get_revisiones(self, obj):
        from forms.models import FormRun
        from forms.serializers import FormRunRevisionSerializer

        revisiones = (
            FormRun.objects.filter(
                scope_type=FormRun.SCOPE_EXTINTOR,
                scope_id=str(obj.id),
            )
            .select_related('tecnico', 'template', 'empresa')
            .order_by('-creado_en')
        )
        return FormRunRevisionSerializer(revisiones, many=True).data

    def get_revisiones_total(self, obj):
        from forms.models import FormRun

        return FormRun.objects.filter(
            scope_type=FormRun.SCOPE_EXTINTOR,
            scope_id=str(obj.id),
        ).count()
    
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
    empresa_id = serializers.IntegerField(source='empresa.id', read_only=True)
    
    # --- NUEVO: Nombre del creador para listados ---
    creado_por_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Extintor
        fields = [
            'id',
            'codigo',
            'ubicacion',
            'tipo',
            'modalidad',
            'clase_fuego',
            'capacidad',
            'fecha_vencimiento',
            'proxima_revision',
            'estado',
            'empresa',
            'empresa_id',
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


class ExtintorPublicSerializer(serializers.ModelSerializer):
    """
    Serializador público para la vista accesible desde el QR.
    
    Expone solo datos seguros para visualización externa.
    """

    estado = serializers.ReadOnlyField()
    empresa_nombre = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Extintor
        fields = [
            'id',
            'codigo',
            'ubicacion',
            'tipo',
            'modalidad',
            'clase_fuego',
            'capacidad',
            'fecha_fabricacion',
            'fecha_vencimiento',
            'ultima_revision',
            'proxima_revision',
            'observaciones',
            'arena',
            'fecha_prueba_hidrostatica',
            'estado',
            'empresa_nombre',
            'qr_code_url',
        ]

    def get_empresa_nombre(self, obj):
        if obj.empresa:
            return obj.empresa.nombre
        return None

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
            return obj.qr_code.url
        return None


class ExtintorCreateSerializer(CodigoUnicoPorEmpresaMixin, serializers.ModelSerializer):
    """
    Serializador para la creación de extintores.
    
    No requiere el campo QR code ya que se genera automáticamente.
    """

    empresa_id = serializers.IntegerField(required=False, write_only=True)
    
    class Meta:
        model = Extintor
        fields = [
            'id',
            'codigo',
            'ubicacion',
            'tipo',
            'modalidad',
            'clase_fuego',
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
    
    def create(self, validated_data):
        empresa = validated_data.pop('empresa', None)
        empresa_id = validated_data.pop('empresa_id', None)
        if empresa_id:
            empresa = Empresa.objects.filter(id=empresa_id).first()
            if not empresa:
                raise serializers.ValidationError({'empresa_id': 'Empresa no encontrada.'})
        
        # El campo creado_por se asignará en el viewset
        extintor = Extintor.objects.create(empresa=empresa, **validated_data)
        return extintor
