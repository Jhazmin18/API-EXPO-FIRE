# views.py
from rest_framework import viewsets, status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

from .models import Empresa, Contacto
from .serializers import (
    EmpresaSerializer, 
    EmpresaCreacionSerializer, 
    EmpresaResumenSerializer,
    ContactoSerializer
)
from usuarios.models import Perfil

User = get_user_model()


class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar empresas.
    
    Endpoints:
    - GET /empresas/ - Listar todas las empresas
    - POST /empresas/ - Crear una nueva empresa (requiere autenticación)
    - GET /empresas/{id}/ - Ver detalle de una empresa
    - PUT/PATCH /empresas/{id}/ - Actualizar una empresa
    - DELETE /empresas/{id}/ - Eliminar una empresa
    - GET /empresas/resumen/ - Ver resumen de empresas (total, activas, inactivas)
    - GET /empresas/mis-registros/ - Ver empresas registradas por el técnico actual
    - POST /empresas/{id}/agregar-contacto/ - Agregar contacto adicional a una empresa
    - POST /empresas/{id}/borrar/ - Marcar una empresa como borrada sin eliminarla
    """
    
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        perfil = getattr(user, 'perfil', None)
        if user.is_superuser or (perfil and perfil.rol == Perfil.ROLE_SUPERADMIN):
            return queryset

        empresa_id = getattr(perfil, 'empresa_id', None)
        if empresa_id:
            return queryset.filter(id=empresa_id)

        return queryset.none()
    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """
        Endpoint: GET /empresas/resumen/
        
        Devuelve un resumen de empresas:
        - Total de empresas
        - Empresas activas
        - Empresas inactivas
        - (Opcional para admins) Registros por técnico
        """
        queryset = self.get_queryset()
        perfil = getattr(request.user, 'perfil', None)

        # Los filtros por querystring solo se permiten dentro del universo
        # que el usuario ya tiene autorizado a ver.
        tecnico_id = request.query_params.get('tecnico_id')
        creado_por_id = request.query_params.get('creado_por_id')

        if tecnico_id:
            queryset = queryset.filter(creado_por_id=tecnico_id)

        if creado_por_id:
            queryset = queryset.filter(creado_por_id=creado_por_id)
        
        # Conteos básicos
        total = queryset.count()
        activas = queryset.filter(activa=True).count()
        inactivas = queryset.filter(activa=False).count()
        
        data = {
            'total': total,
            'activas': activas,
            'inactivas': inactivas,
        }
        
        # Solo el superadmin ve el desglose global por técnico.
        if perfil and perfil.rol == Perfil.ROLE_SUPERADMIN:
            registros_por_tecnico = []

            for user in User.objects.filter(empresas_creadas__isnull=False).distinct():
                count = user.empresas_creadas.count()
                perfil_user = getattr(user, 'perfil', None)

                registros_por_tecnico.append({
                    'tecnico_id': user.id,
                    'nombre': perfil_user.nombre_completo if perfil_user else user.username,
                    'email': user.email,
                    'total_registros': count,
                    'activas': user.empresas_creadas.filter(activa=True).count(),
                    'inactivas': user.empresas_creadas.filter(activa=False).count(),
                })

            data['registros_por_tecnico'] = registros_por_tecnico
        
        serializer = EmpresaResumenSerializer(data)
        return Response(serializer.data)
    
    
    def get_serializer_class(self):
        """Retorna diferentes serializers según la acción"""
        if self.action == 'create':
            return EmpresaCreacionSerializer
        return EmpresaSerializer
    
    def get_permissions(self):
        """Define permisos según la acción"""
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        Fija el técnico autenticado como creador de la empresa.
        """
        serializer.save(creado_por=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        empresa = serializer.instance
        response_serializer = EmpresaSerializer(
            empresa,
            context=self.get_serializer_context(),
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
   
    @action(detail=False, methods=['get'], url_path='mis-registros')
    def mis_registros(self, request):
        """
        Endpoint: GET /empresas/mis-registros/
        
        Devuelve las empresas registradas por el técnico actualmente autenticado.
        Requiere autenticación.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Se requiere autenticación'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        empresas = self.get_queryset().filter(creado_por=request.user)
        serializer = self.get_serializer(empresas, many=True)
        
        return Response({
            'total': empresas.count(),
            'resultados': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='agregar-contacto')
    def agregar_contacto(self, request, pk=None):
        """
        Endpoint: POST /empresas/{id}/agregar-contacto/
        
        Agrega un contacto adicional a una empresa existente.
        """
        empresa = self.get_object()
        serializer = ContactoSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(empresa=empresa)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='borrar')
    def borrar(self, request, pk=None):
        """
        Endpoint: POST /empresas/{id}/borrar/

        Marca la empresa como BORRADA para ocultarla del frontend sin
        eliminar el registro de la base de datos.
        """
        empresa = self.get_object()

        perfil = getattr(request.user, 'perfil', None)
        if not (
            request.user.is_superuser
            or (perfil and perfil.rol == Perfil.ROLE_SUPERADMIN)
            or (perfil and perfil.empresa_id == empresa.id and perfil.rol == Perfil.ROLE_ADMIN_EMPRESA)
        ):
            raise PermissionDenied('No tienes permiso para borrar esta empresa.')

        if empresa.estatus == 'BORRADA':
            return Response({
                'detail': 'La empresa ya estaba marcada como borrada.',
                'empresa_id': str(empresa.id),
                'estatus': empresa.estatus,
            })

        empresa.estatus = 'BORRADA'
        empresa.save(update_fields=['estatus'])

        return Response({
            'detail': 'Empresa marcada como borrada correctamente.',
            'empresa_id': str(empresa.id),
            'estatus': empresa.estatus,
        }, status=status.HTTP_200_OK)


class ContactoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar contactos de empresas.
    
    Endpoints:
    - GET /contactos/ - Listar todos los contactos
    - GET /contactos/?empresa_id=1 - Filtrar contactos por empresa
    - POST /contactos/ - Crear un nuevo contacto
    - GET /contactos/{id}/ - Ver detalle de un contacto
    - PUT/PATCH /contactos/{id}/ - Actualizar un contacto
    - DELETE /contactos/{id}/ - Eliminar un contacto
    """
    
    queryset = Contacto.objects.select_related('empresa').all()
    serializer_class = ContactoSerializer

    def perform_create(self, serializer):
        empresa_id = self.kwargs.get('empresa_pk') or self.request.data.get('empresa_id')
        user = self.request.user
        perfil = getattr(user, 'perfil', None)

        if user.is_superuser or (perfil and perfil.rol == Perfil.ROLE_SUPERADMIN):
            if not empresa_id:
                raise PermissionDenied('Debes indicar la empresa para crear el contacto.')

            empresa = Empresa.objects.get(id=empresa_id)
            serializer.save(empresa=empresa)
            return

        empresa_permitida_id = getattr(perfil, 'empresa_id', None)
        if not empresa_permitida_id:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        if empresa_id and str(empresa_id) != str(empresa_permitida_id):
            raise PermissionDenied('No puedes crear contactos para otra empresa.')

        empresa = Empresa.objects.get(id=empresa_permitida_id)
        serializer.save(empresa=empresa)
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra contactos por empresa si se proporciona el parámetro"""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        perfil = getattr(user, 'perfil', None)
        if not (user.is_superuser or (perfil and perfil.rol == Perfil.ROLE_SUPERADMIN)):
            empresa_id_permitida = getattr(perfil, 'empresa_id', None)
            if empresa_id_permitida:
                queryset = queryset.filter(empresa_id=empresa_id_permitida)
            else:
                return queryset.none()

        empresa_id = (
            self.kwargs.get('empresa_pk')
            or self.request.query_params.get('empresa_id')
        )
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        return queryset
