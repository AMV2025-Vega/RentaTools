"""
Patrón creacional FACTORY para las notificaciones.

`NotificadorFactory.crear(ENV_TYPE)` decide qué implementación usar según el
entorno, sin que el servicio de aplicación lo sepa. Para añadir un canal nuevo
(SMS, push...) se registra una clase: no se modifica código existente (OCP).
"""
import logging

from django.core.mail import send_mail

from apps.reservas.application.ports import Notificador

logger = logging.getLogger(__name__)


class NotificadorConsola(Notificador):
    """Desarrollo: escribe en el log en vez de enviar nada."""

    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> None:
        logger.info("[NOTIFICACION -> %s] %s: %s", destinatario, asunto, mensaje)


class NotificadorEmail(Notificador):
    """Producción: envía correo con el EMAIL_BACKEND configurado (SMTP)."""

    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> None:
        send_mail(asunto, mensaje, None, [destinatario], fail_silently=False)


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
