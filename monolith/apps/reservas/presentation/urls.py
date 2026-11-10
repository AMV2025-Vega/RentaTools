from django.urls import path

from apps.reservas.presentation.views import (
    CotizacionAPIView,
    OcupacionHerramientaAPIView,
    ReporteEstadoAPIView,
    ReporteReservasAPIView,
    ReservaCancelarAPIView,
    ReservasAPIView,
)

urlpatterns = [
    path("reportes/reservas/", ReporteReservasAPIView.as_view(), name="reporte-reservas"),
    path("reportes/<uuid:tarea_id>/", ReporteEstadoAPIView.as_view(), name="reporte-estado"),
    path("cotizaciones/", CotizacionAPIView.as_view(), name="cotizacion"),
    path("reservas/", ReservasAPIView.as_view(), name="reservas"),
    path("reservas/<int:pk>/cancelar/", ReservaCancelarAPIView.as_view(), name="reserva-cancelar"),
    path("herramientas/<int:pk>/ocupacion/", OcupacionHerramientaAPIView.as_view(), name="herramienta-ocupacion"),
]
