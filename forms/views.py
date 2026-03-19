from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FormRun, FormTemplate
from .serializers import (
    FormRunSerializer,
    FormTemplateSerializer,
    FormTemplateCreateSerializer,
)


class FormTemplateActivoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, codigo):
        empresa_id = request.query_params.get('empresa_id')
        plantilla = (
            FormTemplate.objects.filter(codigo=codigo, activo=True)
            .prefetch_related('preguntas__opciones', 'empresas_permitidas')
            .first()
        )
        if not plantilla:
            return Response(
                {'detail': 'Plantilla activa no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not plantilla.is_available_for(request.user, empresa_id=empresa_id):
            return Response(
                {'detail': 'No tienes permisos para acceder a esta plantilla.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = FormTemplateSerializer(plantilla)
        return Response(serializer.data)


class FormTemplateListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = FormTemplate.objects.all().prefetch_related('preguntas__opciones', 'empresas_permitidas')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FormTemplateCreateSerializer
        return FormTemplateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        disponibles = str(self.request.query_params.get('disponibles', '')).lower()
        if disponibles not in {'1', 'true', 'yes'}:
            return queryset

        empresa_id = self.request.query_params.get('empresa_id')
        allowed_ids = [
            template for template in queryset
            if template.is_available_for(self.request.user, empresa_id=empresa_id)
        ]
        return queryset.filter(id__in=[template.id for template in allowed_ids])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plantilla = serializer.save()
        read_serializer = FormTemplateSerializer(plantilla)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FormRunViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        FormRun.objects.select_related('template', 'empresa', 'tecnico')
        .prefetch_related('template__preguntas')
    )
    serializer_class = FormRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        codigo = params.get('codigo')
        if codigo:
            queryset = queryset.filter(template__codigo=codigo)
        scope_type = params.get('scope_type')
        if scope_type:
            queryset = queryset.filter(scope_type=scope_type)
        scope_id = params.get('scope_id')
        if scope_id:
            queryset = queryset.filter(scope_id=scope_id)
        estado = params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset
