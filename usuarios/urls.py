from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EquipoEmpresaView, PerfilViewSet

router = DefaultRouter()
router.register(r'', PerfilViewSet, basename='perfil')

urlpatterns = [
    path('empresa/<int:empresa_id>/equipo/', EquipoEmpresaView.as_view(), name='empresa-equipo'),
    path('', include(router.urls)),
]
