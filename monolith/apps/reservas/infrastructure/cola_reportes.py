import logging

from celery import current_app

from apps.compartido.excepciones import ServicioNoDisponible
from apps.reservas.application.reportes import ColaReportes, EstadoTarea
from apps.reservas.infrastructure.tareas import generar_reporte_reservas

logger = logging.getLogger(__name__)

_ESTADOS = {"PENDING": "PENDIENTE", "RECEIVED": "PENDIENTE", "STARTED": "EN_CURSO", "RETRY": "EN_CURSO", "SUCCESS": "LISTO", "FAILURE": "FALLIDO"}


class CeleryColaReportes(ColaReportes):
    def solicitar_reporte_reservas(self, cliente_id: int) -> str:
        try:
            return generar_reporte_reservas.delay(cliente_id).id
        except Exception as exc:  # noqa: BLE001 - broker caído, timeout, etc.
            logger.error("No se pudo encolar el reporte: %s", exc)
            raise ServicioNoDisponible("El servicio de reportes no está disponible.", "reportes_no_disponible") from exc

    def consultar(self, tarea_id: str) -> EstadoTarea:
        try:
            r = current_app.AsyncResult(tarea_id)
            estado = _ESTADOS.get(r.state, "PENDIENTE")
            return EstadoTarea(tarea_id, estado, r.result if estado == "LISTO" else None)
        except Exception as exc:  # noqa: BLE001
            logger.error("No se pudo consultar la tarea %s: %s", tarea_id, exc)
            raise ServicioNoDisponible("El servicio de reportes no está disponible.", "reportes_no_disponible") from exc
