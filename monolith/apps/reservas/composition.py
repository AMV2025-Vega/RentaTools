"""Composition root de Reservas: aquí (y solo aquí) se eligen las implementaciones concretas."""
from django.conf import settings

from apps.auditoria.infrastructure.logger import DjangoAuditLogger
from apps.compartido.infraestructura import DjangoTransactionManager, hoy_local
from apps.reservas.application.services import ReservaService
from apps.reservas.infrastructure.catalogo import CatalogoInventarioAdapter
from apps.reservas.infrastructure.costo import CalculadoraConRespaldo, CalculadoraLocal, CostoHttpAdapter
from apps.reservas.infrastructure.notificadores import NotificadorFactory
from apps.reservas.infrastructure.repositories import DjangoReservaRepository


def construir_reserva_service() -> ReservaService:
    return ReservaService(
        repo=DjangoReservaRepository(),
        catalogo=CatalogoInventarioAdapter(),
        calculadora=CalculadoraConRespaldo(
            principal=CostoHttpAdapter(settings.COSTO_SERVICE_URL, settings.COSTO_SERVICE_TIMEOUT),
            respaldo=CalculadoraLocal(),
        ),
        notificador=NotificadorFactory.crear(settings.ENV_TYPE),
        auditor=DjangoAuditLogger(),
        tx=DjangoTransactionManager(),
        reloj=hoy_local,
    )
