from django.urls import path

from apps.reservas.presentation.views import OcupacionHerramientaAPIView, ReservaCancelarAPIView, ReservasAPIView

urlpatterns = [
    path("reservas/", ReservasAPIView.as_view(), name="reservas"),
    path("reservas/<int:pk>/cancelar/", ReservaCancelarAPIView.as_view(), name="reserva-cancelar"),
    path("herramientas/<int:pk>/ocupacion/", OcupacionHerramientaAPIView.as_view(), name="herramienta-ocupacion"),
]
