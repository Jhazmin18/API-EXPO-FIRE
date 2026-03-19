"""
Configuración de URLs para el proyecto Core

El `urlpatterns` incluye:
- Django Admin
- API de extintores
- Rutas de autenticación JWT
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from usuarios.views import PerfilDetailView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    # Perfil del usuario autenticado
    path('api/perfil/', PerfilDetailView.as_view(), name='perfil-detail'),

    # Usuarios (list, detail)
    path('usuarios/', include('usuarios.urls')),

    # API de extintores
    path('', include('extintores.urls')),
    
    # Autenticación JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('empresas/', include('empresas.urls')),
    path('forms/', include('forms.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

