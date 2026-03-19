# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
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
    """
    
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
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
        # Filtros opcionales
        tecnico_id = request.query_params.get('tecnico_id')
        creado_por_id = request.query_params.get('creado_por_id')
        
        queryset = Empresa.objects.all()
        
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
        
        # Si es superadmin, agregar resumen por técnico
        if request.user.is_authenticated:
            perfil = getattr(request.user, 'perfil', None)
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
        if self.action in ['list', 'retrieve', 'resumen']:
            # Lectura pública
            permission_classes = [AllowAny]
        else:
            # Escritura requiere autenticación
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        Fija el técnico autenticado como creador de la empresa.
        """
        serializer.save(creado_por=self.request.user)
    
   
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
        
        empresas = self.queryset.filter(creado_por=request.user)
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
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra contactos por empresa si se proporciona el parámetro"""
        queryset = super().get_queryset()
        empresa_id = self.request.query_params.get('empresa_id')
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        return queryset
