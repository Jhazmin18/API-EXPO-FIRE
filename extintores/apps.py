"""
Configuración de la app API
"""
from django.apps import AppConfig


class ExtintoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'extintores'
    verbose_name = 'API de Extintores'

