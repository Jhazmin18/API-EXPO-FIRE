"""
Serializadores para el dominio de usuarios.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Perfil
from empresas.models import Empresa
from empresas.serializers import EmpresaSerializer

User = get_user_model()


class PerfilSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    foto_perfil = serializers.ImageField(required=False, allow_null=True)
    nombre_completo = serializers.CharField(read_only=True)

    rol = serializers.ChoiceField(
        choices=Perfil.ROLE_CHOICES,
        default=Perfil.ROLE_ANALISTA,
        required=False,
        help_text='Rol del usuario dentro del sistema'
    )

    empresa = EmpresaSerializer(read_only=True)

    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
            read_only_fields = fields

    class Meta:
        model = Perfil
        fields = [
            'id',
            'user',
            'username',
            'email',
            'nombre_completo',
            'empresa',
            'foto_perfil',
            'rol',
            'telefono',
            'domicilio',
            'requiere_cambio_password',
            'reset_password_solicitado_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'username',
            'email',
            'requiere_cambio_password',
            'reset_password_solicitado_at',
            'created_at',
            'updated_at',
            'empresa',
        ]

    def get_user(self, obj):
        serializer = self.UserSerializer(obj.user, context=self.context)
        return serializer.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.foto_perfil:
            request = self.context.get('request')
            data['foto_perfil'] = (
                request.build_absolute_uri(instance.foto_perfil.url)
                if request
                else instance.foto_perfil.url
            )
        else:
            data['foto_perfil'] = None
        return data


class PerfilCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    rol = serializers.ChoiceField(
        choices=Perfil.ROLE_CHOICES,
        default=Perfil.ROLE_ANALISTA,
    )
    empresa_id = serializers.IntegerField(required=False)
    foto_perfil = serializers.ImageField(required=False, allow_null=True)
    telefono = serializers.CharField(required=False, allow_blank=True, max_length=30)
    domicilio = serializers.CharField(required=False, allow_blank=True, max_length=250)

    def validate(self, attrs):
        request = self.context.get('request')
        perfil_solicitante = getattr(request.user, 'perfil', None) if request else None

        if request and request.user.is_superuser:
            return attrs

        if perfil_solicitante and perfil_solicitante.rol == Perfil.ROLE_SUPERADMIN:
            return attrs

        if perfil_solicitante and perfil_solicitante.rol == Perfil.ROLE_ADMIN_EMPRESA:
            if attrs['rol'] not in [Perfil.ROLE_SUPERVISOR, Perfil.ROLE_ANALISTA]:
                raise serializers.ValidationError({
                    'rol': 'ADMIN_EMPRESA solo puede crear supervisores y analistas.'
                })
            if not perfil_solicitante.empresa_id:
                raise serializers.ValidationError({
                    'empresa_id': 'El administrador no tiene una empresa asignada.'
                })

            empresa_id = attrs.get('empresa_id')
            if empresa_id and empresa_id != perfil_solicitante.empresa_id:
                raise serializers.ValidationError({
                    'empresa_id': 'Solo puedes crear usuarios para tu propia empresa.'
                })

            attrs['empresa_id'] = perfil_solicitante.empresa_id
            return attrs

        raise serializers.ValidationError('No tienes permiso para crear usuarios.')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este username.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo electrónico.")
        return value

    def validate_empresa_id(self, value):
        empresa = Empresa.objects.filter(id=value).first()
        if not empresa:
            raise serializers.ValidationError("Empresa no encontrada.")
        return value

    def create(self, validated_data):
        empresa_id = validated_data.pop('empresa_id', None)
        foto = validated_data.pop('foto_perfil', None)
        telefono = validated_data.pop('telefono', '')
        domicilio = validated_data.pop('domicilio', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        empresa = None
        if empresa_id:
            empresa = Empresa.objects.get(id=empresa_id)
        perfil = Perfil.objects.create(
            user=user,
            rol=validated_data['rol'],
            empresa=empresa,
            foto_perfil=foto,
            telefono=telefono,
            domicilio=domicilio,
        )
        return perfil


class SolicitarResetPasswordSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=False, allow_blank=True)


class CambiarMiPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True, min_length=8)

    def validate_password_actual(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def validate_password_nueva(self, value):
        validate_password(value, self.context['request'].user)
        return value


class SolicitarOlvidePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmarOlvidePasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden.'
            })

        validate_password(attrs['password'])
        return attrs
