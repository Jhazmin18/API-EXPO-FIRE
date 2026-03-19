from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FormRunViewSet,
    FormTemplateActivoAPIView,
    FormTemplateListCreateAPIView,
)

router = DefaultRouter()
router.register(r'runs', FormRunViewSet, basename='formrun')

urlpatterns = [
    path('templates/', FormTemplateListCreateAPIView.as_view(), name='formtemplate-list'),
    path('templates/<str:codigo>/activo/', FormTemplateActivoAPIView.as_view(), name='formtemplate-activo'),
    path('', include(router.urls)),
]
