from django.urls import path

from apps.inventario.presentation.views import (
    CategoriasAPIView,
    HerramientaDetalleAPIView,
    HerramientaEstadoAPIView,
    HerramientasAPIView,
)

urlpatterns = [
    path("categorias/", CategoriasAPIView.as_view(), name="categorias"),
    path("herramientas/", HerramientasAPIView.as_view(), name="herramientas"),
    path("herramientas/<int:pk>/", HerramientaDetalleAPIView.as_view(), name="herramienta-detalle"),
    path("herramientas/<int:pk>/estado/", HerramientaEstadoAPIView.as_view(), name="herramienta-estado"),
]
