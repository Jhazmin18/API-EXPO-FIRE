"""
Configuración de URLs de la API.

Define los endpoints de la API usando Django REST Framework routers.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExtintorViewSet

# Crear el router y registrar ViewSets
router = DefaultRouter()
router.register(r'extintores', ExtintorViewSet, basename='extintor')

# URLs de la API
urlpatterns = [
    path('', include(router.urls)),
]

