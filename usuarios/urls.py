from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PerfilViewSet

router = DefaultRouter()
router.register(r'', PerfilViewSet, basename='perfil')

urlpatterns = [
    path('', include(router.urls)),
]
