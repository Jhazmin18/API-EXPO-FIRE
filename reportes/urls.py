from django.urls import path

from .views import InventarioReporteView, LogExtintoresView, LogUsuariosView


urlpatterns = [
    path('inventario/', InventarioReporteView.as_view(), name='reporte-inventario'),
    path('log-usuarios/', LogUsuariosView.as_view(), name='log-usuarios'),
    path('log-extintores/', LogExtintoresView.as_view(), name='log-extintores'),
]
