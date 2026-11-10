"""Tareas Celery (el worker las ejecuta fuera del ciclo petición/respuesta)."""
from celery import shared_task
from django.conf import settings

from apps.reservas.infrastructure.notificadores import NotificadorFactory


@shared_task(
    name="reservas.enviar_notificacion",
    autoretry_for=(Exception,),
    retry_backoff=True,  # 1 s, 2 s, 4 s... entre reintentos
    retry_backoff_max=60,
    retry_kwargs={"max_retries": 3},
)
def enviar_notificacion(destinatario: str, plantilla: str, contexto: dict, idioma: str = "") -> None:
    """Envía con la implementación REAL (consola/SMTP) elegida por la Factory según ENV_TYPE."""
    NotificadorFactory.crear(settings.ENV_TYPE).enviar(destinatario, plantilla, contexto, idioma)


@shared_task(name="reservas.generar_reporte_reservas")
def generar_reporte_reservas(cliente_id: int) -> dict:
    """Genera el CSV de las reservas de un cliente (proceso de fondo)."""
    from apps.reservas.composition import construir_reporte_service  # import tardío: evita ciclo

    return construir_reporte_service().generar_csv(cliente_id)
