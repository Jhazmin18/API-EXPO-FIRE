# views.py
"""
Vistas de la API REST para extintores.

Este módulo define los ViewSets que manejan las peticiones HTTP
para la gestión de extintores.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from .models import Extintor
from empresas.models import Empresa
from .serializers import (
    ExtintorSerializer,
    ExtintorListSerializer,
    ExtintorCreateSerializer,
)


class ExtintorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar extintores.
    
    Endpoints:
        - GET /extintores/ - Lista todos los extintores
        - POST /extintores/ - Crea un nuevo extintor
        - GET /extintores/{id}/ - Detalle de un extintor
        - PUT /extintores/{id}/ - Actualiza un extintor
        - PATCH /extintores/{id}/ - Actualización parcial
        - DELETE /extintores/{id}/ - Elimina un extintor
        - GET /extintores/por_codigo/{codigo}/ - Busca por código
    """
    
    queryset = Extintor.objects.all()
    serializer_class = ExtintorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo', 'ubicacion', 'tipo']
    ordering_fields = ['codigo', 'ubicacion', 'fecha_vencimiento', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Retorna el serializador apropiado según la acción.
        """
        if self.action == 'list':
            return ExtintorListSerializer
        elif self.action == 'create':
            return ExtintorCreateSerializer
        return ExtintorSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa = self.request.query_params.get('empresa')
        if empresa:
            queryset = queryset.filter(
                Q(empresa__id=empresa) | Q(empresa__nombre__iexact=empresa)
            )
        
        # --- NUEVO: Filtrar por creador ---
        creado_por = self.request.query_params.get('creado_por')
        if creado_por:
            queryset = queryset.filter(creado_por_id=creado_por)
        
        return queryset

    def get_permissions(self):
        """
        Define permisos según la acción.
        
        - por_codigo: Público (para QR scanner)
        - Resto: Requiere autenticación
        """
        if self.action == 'por_codigo':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    # --- NUEVO: Perform create para asignar creado_por ---
    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario autenticado como creador del extintor.
        """
        serializer.save(creado_por=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='por-codigo/(?P<codigo>[^/.]+)')
    def por_codigo(self, request, codigo=None):
        """
        Obtiene un extintor por su código.
        
        Este endpoint es público y se usa cuando se escanea un QR.
        
        Args:
            codigo: Código del extintor
            
        Returns:
            JSON con la información del extintor
        """
        extintor = get_object_or_404(Extintor, codigo=codigo)
        serializer = self.get_serializer(extintor)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='kpis')
    def kpis(self, request):
        """
        KPI demo: totales y porcentajes clave por estado y empresa.
        """
        extintores = self.get_queryset()
        total = extintores.count()
        estados = {'verde': 0, 'amarillo': 0, 'rojo': 0}
        empresas = {}
        
        for ext in extintores:
            estados[ext.estado] += 1
            if ext.empresa:
                empresas.setdefault(ext.empresa.nombre, 0)
                empresas[ext.empresa.nombre] += 1

        def pct(value):
            return round((value / total) * 100, 1) if total else 0

        data = {
            'total_extintores': total,
            'por_estado': {
                estado: {
                    'cantidad': count,
                    'porcentaje': pct(count),
                }
                for estado, count in estados.items()
            },
            'empresas_activas': empresas,
        }
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        """
        Obtiene estadísticas generales de los extintores.
        
        Returns:
            JSON con estadísticas (total, por estado, por tipo)
        """
        extintores = self.get_queryset()
        
        # Contar por estado
        estados = {'verde': 0, 'amarillo': 0, 'rojo': 0}
        for extintor in extintores:
            estados[extintor.estado] += 1
        
        # Contar por tipo
        tipos = {}
        for extintor in extintores:
            tipo = extintor.get_tipo_display()
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        data = {
            'total': extintores.count(),
            'por_estado': estados,
            'por_tipo': tipos,
        }
        
        return Response(data)

    @action(detail=False, methods=['post'], url_path='impresionmasiva')
    def impresionmasiva(self, request):
        """Genera un ZIP con las etiquetas PNG de múltiples extintores."""
        ids = request.data.get('ids')
        if not isinstance(ids, list) or not ids:
            return Response(
                {'detail': 'Debe enviar una lista de IDs en el cuerpo JSON bajo la llave "ids".'},
                status=400,
            )

        queryset = self.get_queryset().filter(id__in=ids)
        encontrados = {str(ext.id) for ext in queryset}
        faltantes = [ext_id for ext_id in ids if ext_id not in encontrados]

        if faltantes:
            return Response(
                {'detail': 'No se encontraron todos los extintores solicitados.', 'faltantes': faltantes},
                status=404,
            )

        archivo_zip = BytesIO()
        with ZipFile(archivo_zip, 'w', ZIP_DEFLATED) as zipfile:
            for extintor in queryset:
                etiqueta = extintor.obtener_etiqueta_png()
                nombre_archivo = f"{extintor.codigo}.png"
                zipfile.writestr(nombre_archivo, etiqueta.getvalue())
        archivo_zip.seek(0)

        response = HttpResponse(archivo_zip.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="etiquetas_extintores.zip"'
        return response

    @action(detail=True, methods=['get'], url_path='etiqueta')
    def etiqueta(self, request, pk=None):
        """
        Devuelve la etiqueta QR (PNG) lista para imprimir.
        """
        extintor = self.get_object()
        buffer = extintor.obtener_etiqueta_png()
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    
    # --- NUEVO: Endpoint para ver mis extintores registrados ---
    @action(detail=False, methods=['get'], url_path='mis-registros')
    def mis_registros(self, request):
        """
        Endpoint: GET /extintores/mis-registros/
        
        Devuelve los extintores registrados por el usuario actualmente autenticado.
        Requiere autenticación.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Se requiere autenticación'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        extintores = self.queryset.filter(creado_por=request.user)
        serializer = self.get_serializer(extintores, many=True)
        
        return Response({
            'total': extintores.count(),
            'resultados': serializer.data
        })