from django.urls import path

from apps.reservas.presentation.views import CotizacionAPIView, OcupacionHerramientaAPIView, ReservaCancelarAPIView, ReservasAPIView

urlpatterns = [
    path("cotizaciones/", CotizacionAPIView.as_view(), name="cotizacion"),
    path("reservas/", ReservasAPIView.as_view(), name="reservas"),
    path("reservas/<int:pk>/cancelar/", ReservaCancelarAPIView.as_view(), name="reserva-cancelar"),
    path("herramientas/<int:pk>/ocupacion/", OcupacionHerramientaAPIView.as_view(), name="herramienta-ocupacion"),
]
