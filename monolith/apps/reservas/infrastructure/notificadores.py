"""
Patrón creacional FACTORY para las notificaciones (+ Decorator asíncrono).

`NotificadorFactory.crear(ENV_TYPE)` decide qué implementación usar según el
entorno, sin que el servicio de aplicación lo sepa. Para añadir un canal nuevo
(SMS, push...) se registra una clase: no se modifica código existente (OCP).

`NotificadorAsincrono` envuelve el envío en una tarea Celery: la petición HTTP no
espera al correo y el worker reintenta con espera exponencial si el proveedor falla.
"""
import logging

from django.core.mail import send_mail

from apps.reservas.application.ports import Notificador
from apps.reservas.infrastructure.mensajes import renderizar

logger = logging.getLogger(__name__)


class NotificadorConsola(Notificador):
    """Desarrollo: escribe en el log en vez de enviar nada."""

    def enviar(self, destinatario: str, plantilla: str, contexto: dict, idioma: str = "") -> None:
        asunto, mensaje = renderizar(plantilla, contexto, idioma)
        logger.info("[NOTIFICACION -> %s] %s: %s", destinatario, asunto, mensaje)


class NotificadorEmail(Notificador):
    """Producción: envía correo con el EMAIL_BACKEND configurado (SMTP)."""

    def enviar(self, destinatario: str, plantilla: str, contexto: dict, idioma: str = "") -> None:
        asunto, mensaje = renderizar(plantilla, contexto, idioma)
        send_mail(asunto, mensaje, None, [destinatario], fail_silently=False)


class NotificadorAsincrono(Notificador):
    """Decorator: encola la notificación en Redis; la envía el worker de Celery."""

    def enviar(self, destinatario: str, plantilla: str, contexto: dict, idioma: str = "") -> None:
        from apps.reservas.infrastructure.tareas import enviar_notificacion  # import tardío: evita ciclo

        enviar_notificacion.delay(destinatario, plantilla, contexto, idioma)


class NotificadorFactory:
    _registro: dict[str, type[Notificador]] = {
        "development": NotificadorConsola,
        "production": NotificadorEmail,
    }

    @classmethod
    def registrar(cls, env_type: str, clase: type[Notificador]) -> None:
        cls._registro[env_type.lower()] = clase

    @classmethod
    def crear(cls, env_type: str) -> Notificador:
        try:
            return cls._registro[env_type.strip().lower()]()
        except KeyError:
            validos = ", ".join(sorted(cls._registro))
            raise ValueError(f"ENV_TYPE '{env_type}' no soportado. Valores válidos: {validos}.") from None
