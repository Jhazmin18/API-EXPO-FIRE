# dashboard/urls.py
from django.urls import path
from .views import (
    SuperAdminKPIsView,
    RiesgoEmpresasView,
    ActividadRecienteView,
    AlertasOperativasView
)

urlpatterns = [
    path('superadmin/kpis/', SuperAdminKPIsView.as_view(), name='superadmin-kpis'),
    path('superadmin/riesgo-empresas/', RiesgoEmpresasView.as_view(), name='riesgo-empresas'),
    path('superadmin/actividad/', ActividadRecienteView.as_view(), name='actividad-reciente'),
    path('superadmin/alertas/', AlertasOperativasView.as_view(), name='alertas-operativas'),
]