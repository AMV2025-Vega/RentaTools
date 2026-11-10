"""Composition root de Reservas: aquí (y solo aquí) se eligen las implementaciones concretas."""
from django.conf import settings
from django.core.cache import cache

from apps.auditoria.infrastructure.logger import DjangoAuditLogger
from apps.compartido.infraestructura import DjangoTransactionManager, hoy_local
from apps.reservas.application.cotizacion import CotizacionService
from apps.reservas.application.reportes import ReporteService
from apps.reservas.application.services import ReservaService
from apps.reservas.infrastructure.aliado_seguros import AliadoSegurosHttpAdapter
from apps.reservas.infrastructure.catalogo import CatalogoInventarioAdapter
from apps.reservas.infrastructure.cola_reportes import CeleryColaReportes
from apps.reservas.infrastructure.costo import CalculadoraConRespaldo, CalculadoraLocal, CostoHttpAdapter
from apps.reservas.infrastructure.notificadores import NotificadorAsincrono, NotificadorFactory
from apps.reservas.infrastructure.repositories import DjangoReservaRepository
from apps.reservas.infrastructure.tasas_cambio import ConversorConCache, TasaCambioHttpAdapter


def _calculadora_costo() -> CalculadoraConRespaldo:
    return CalculadoraConRespaldo(
        principal=CostoHttpAdapter(settings.COSTO_SERVICE_URL, settings.COSTO_SERVICE_TIMEOUT),
        respaldo=CalculadoraLocal(),
    )


def _notificador():
    """Con Celery activo se encola; si no, se envía en línea (según ENV_TYPE)."""
    if settings.NOTIFICACIONES_ASINCRONAS:
        return NotificadorAsincrono()
    return NotificadorFactory.crear(settings.ENV_TYPE)


def construir_reserva_service() -> ReservaService:
    return ReservaService(
        repo=DjangoReservaRepository(),
        catalogo=CatalogoInventarioAdapter(),
        calculadora=_calculadora_costo(),
        notificador=_notificador(),
        auditor=DjangoAuditLogger(),
        tx=DjangoTransactionManager(),
        reloj=hoy_local,
    )


def construir_cotizacion_service() -> CotizacionService:
    return CotizacionService(
        catalogo=CatalogoInventarioAdapter(),
        calculadora=_calculadora_costo(),
        seguros=AliadoSegurosHttpAdapter(settings.ALIADO_SERVICE_URL, settings.ALIADO_API_KEY, settings.ALIADO_TIMEOUT),
        conversor=ConversorConCache(TasaCambioHttpAdapter(settings.TASAS_CAMBIO_URL, settings.TASAS_CAMBIO_TIMEOUT), cache),
        reloj=hoy_local,
    )


def construir_reporte_service() -> ReporteService:
    return ReporteService(DjangoReservaRepository(), CeleryColaReportes())
