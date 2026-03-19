"""
Serializadores para el dominio de usuarios.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Perfil
from empresas.models import Empresa
from empresas.serializers import EmpresaSerializer

User = get_user_model()


class PerfilSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    foto_perfil = serializers.SerializerMethodField()
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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'username', 'email', 'created_at', 'updated_at', 'empresa']

    def get_foto_perfil(self, obj):
        """
        Retorna la URL absoluta para la foto de perfil cuando existe.
        """
        if not obj.foto_perfil:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.foto_perfil.url)
        return obj.foto_perfil.url

    def get_user(self, obj):
        serializer = self.UserSerializer(obj.user, context=self.context)
        return serializer.data


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
