from django.urls import path

from .views import InventarioReporteView


urlpatterns = [
    path('inventario/', InventarioReporteView.as_view(), name='reporte-inventario'),
]
