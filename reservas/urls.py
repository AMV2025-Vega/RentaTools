from django.urls import path
from reservas.views import (
    HerramientasDisponiblesAPIView,
    ReservaCrearAPIView,
    ReservaCancelarAPIView
)

urlpatterns = [
    path('herramientas/disponibles/', HerramientasDisponiblesAPIView.as_view(), name='herramientas-disponibles'),
    path('reservas/', ReservaCrearAPIView.as_view(), name='reserva-crear'),
    path('reservas/<int:pk>/cancelar/', ReservaCancelarAPIView.as_view(), name='reserva-cancelar'),
]