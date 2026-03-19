"""
Vistas enfocadas en usuarios.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Perfil
from .serializers import PerfilSerializer, PerfilCreateSerializer


class PerfilDetailView(APIView):
    """Devuelve la información del perfil autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil, _ = Perfil.objects.get_or_create(
            user=request.user,
            defaults={
                'empresa': None,
                'foto_perfil': None,
            }
        )
        serializer = PerfilSerializer(perfil, context={'request': request})
        return Response(serializer.data)


class PerfilViewSet(viewsets.ModelViewSet):
    """
    Listado, detalle y creación de perfiles (usuarios).
    """

    queryset = Perfil.objects.select_related('user', 'empresa').all()
    def get_serializer_class(self):
        if self.action == 'create':
            return PerfilCreateSerializer
        return PerfilSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfil = serializer.save()
        read_serializer = PerfilSerializer(perfil, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
