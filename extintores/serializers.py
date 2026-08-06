# serializers.py
"""
Serializadores de la API REST para extintores.

Este módulo define los serializadores de Django REST Framework
que convierten los modelos en JSON y viceversa.
"""
from rest_framework import serializers
from .models import Extintor, RevisionExtintor
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


class RevisionExtintorSerializer(serializers.ModelSerializer):
    extintor = serializers.PrimaryKeyRelatedField(read_only=True)
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    scope_type = serializers.CharField(required=False)
    scope_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    estado = serializers.ChoiceField(choices=RevisionExtintor.ESTADO_CHOICES, required=False)
    tipo_servicio = serializers.ChoiceField(choices=RevisionExtintor.TIPO_SERVICIO_CHOICES, required=False)
    respuestas_json = serializers.JSONField(required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    observaciones_por_item = serializers.JSONField(required=False, allow_null=True)
    tecnico_nombre = serializers.SerializerMethodField()
    tecnico_email = serializers.EmailField(source='tecnico.email', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = RevisionExtintor
        fields = [
            'id',
            'extintor',
            'empresa',
            'empresa_nombre',
            'tecnico',
            'tecnico_nombre',
            'tecnico_email',
            'tipo_servicio',
            'scope_type',
            'scope_id',
            'estado',
            'respuestas_json',
            'observaciones',
            'observaciones_por_item',
            'tiene_incidencias',
            'payload_json',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = [
            'id',
            'extintor',
            'empresa',
            'empresa_nombre',
            'tecnico',
            'tecnico_nombre',
            'tecnico_email',
            'tiene_incidencias',
            'payload_json',
            'creado_en',
            'actualizado_en',
        ]

    def get_tecnico_nombre(self, obj):
        if obj.tecnico:
            perfil = getattr(obj.tecnico, 'perfil', None)
            if perfil:
                return perfil.nombre_completo
            return obj.tecnico.get_full_name() or obj.tecnico.username
        return None

    def validate(self, attrs):
        attrs = super().validate(attrs)
        respuestas = attrs.get('respuestas_json') or {}
        if not isinstance(respuestas, dict):
            raise serializers.ValidationError({'respuestas_json': 'Debe ser un objeto JSON.'})
        observaciones_por_item = attrs.get('observaciones_por_item')
        if observaciones_por_item is None:
            observaciones_por_item = {}
        if not isinstance(observaciones_por_item, dict):
            raise serializers.ValidationError(
                {'observaciones_por_item': 'Debe ser un objeto JSON.'}
            )
        extintor = self.context.get('extintor')
        if not extintor:
            raise serializers.ValidationError({'extintor': 'No se pudo resolver el extintor.'})
        scope_type = attrs.get('scope_type')
        if scope_type and scope_type != 'extintor':
            raise serializers.ValidationError({'scope_type': 'Debe ser "extintor".'})
        scope_id = attrs.get('scope_id')
        if scope_id and str(scope_id) != str(extintor.id):
            raise serializers.ValidationError({'scope_id': 'No coincide con el extintor de la URL.'})
        attrs['scope_type'] = 'extintor'
        attrs['scope_id'] = str(extintor.id)
        attrs['respuestas_json'] = respuestas
        attrs['observaciones_por_item'] = observaciones_por_item
        if not attrs.get('observaciones') and isinstance(respuestas.get('observaciones'), str):
            attrs['observaciones'] = respuestas.get('observaciones')
        estado = attrs.get('estado') or RevisionExtintor.ESTADO_COMPLETADO
        observaciones = attrs.get('observaciones') or ''
        tiene_respuestas_negativas = any(
            valor is False for valor in respuestas.values() if isinstance(valor, bool)
        )
        attrs['tiene_incidencias'] = (
            estado == RevisionExtintor.ESTADO_CON_OBSERVACIONES
            or bool(observaciones.strip())
            or bool(observaciones_por_item)
            or tiene_respuestas_negativas
        )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        extintor = self.context.get('extintor')
        if not extintor:
            raise serializers.ValidationError({'extintor': 'No se pudo resolver el extintor.'})

        validated_data['extintor'] = extintor
        validated_data['empresa'] = extintor.empresa
        user = getattr(request, 'user', None) if request else None
        validated_data['tecnico'] = user if user and user.is_authenticated else None
        raw_payload = getattr(request, 'data', {}) if request else {}
        try:
            import copy
            validated_data['payload_json'] = copy.deepcopy(raw_payload)
        except Exception:
            validated_data['payload_json'] = dict(raw_payload) if hasattr(raw_payload, 'items') else raw_payload
        return super().create(validated_data)


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
        revisiones = obj.revisiones.select_related('tecnico', 'empresa').all()
        return RevisionExtintorSerializer(revisiones, many=True).data

    def get_revisiones_total(self, obj):
        return obj.revisiones.count()
    
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
