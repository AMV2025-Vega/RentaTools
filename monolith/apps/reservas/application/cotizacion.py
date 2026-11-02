"""
Caso de uso: cotizar un alquiler SIN reservar. Combina tres fuentes y degrada con elegancia:

  costo del alquiler  -> microservicio Flask de costos (con respaldo local)
  seguro opcional     -> servicio del ALIADO            (si falla: se omite y se avisa)
  total en USD        -> API de TERCEROS de tasas        (si falla: se omite y se avisa)
"""
import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable

from apps.compartido.excepciones import NoEncontrado, ReglaNegocioViolada
from apps.reservas.application.ports import (
    CalculadoraCosto,
    CatalogoHerramientas,
    ConversorMoneda,
    ServicioExternoError,
    ServicioSeguros,
)
from apps.reservas.domain.cotizacion import Cotizacion
from apps.reservas.domain.reglas import validar_rango_fechas

logger = logging.getLogger(__name__)
CENT = Decimal("0.01")


class CotizacionService:
    def __init__(
        self,
        catalogo: CatalogoHerramientas,
        calculadora: CalculadoraCosto,
        seguros: ServicioSeguros,
        conversor: ConversorMoneda,
        reloj: Callable[[], date],
    ):
        self._catalogo = catalogo
        self._calculadora = calculadora
        self._seguros = seguros
        self._conversor = conversor
        self._reloj = reloj

    def cotizar(self, herramienta_id: int, fecha_inicio: date, fecha_fin: date) -> Cotizacion:
        herramienta = self._catalogo.obtener(herramienta_id)
        if herramienta is None:
            raise NoEncontrado(f"No existe la herramienta {herramienta_id}.", "herramienta_no_encontrada")
        if not herramienta.activa:
            raise ReglaNegocioViolada(f"La herramienta '{herramienta.nombre}' no está disponible para alquiler.", "herramienta_inactiva")
        validar_rango_fechas(fecha_inicio, fecha_fin, self._reloj())

        costo = self._calculadora.calcular(fecha_inicio, fecha_fin, [herramienta.precio_por_dia])
        avisos: list[str] = []

        seguro = None
        try:
            seguro = self._seguros.cotizar(costo.total, costo.dias, herramienta.categoria)
        except ServicioExternoError as exc:
            logger.warning("Cotización sin seguro (aliado no disponible): %s", exc)
            avisos.append("seguro_no_disponible")

        total = costo.total + (seguro.prima if seguro else Decimal("0"))

        total_usd = cop_por_usd = fecha_tasa = None
        try:
            tasa = self._conversor.obtener_tasa(costo.moneda, "USD")
            total_usd = (total * tasa.tasa).quantize(CENT, rounding=ROUND_HALF_UP)
            cop_por_usd = (Decimal(1) / tasa.tasa).quantize(CENT, rounding=ROUND_HALF_UP)
            fecha_tasa = tasa.actualizada_en
        except ServicioExternoError as exc:
            logger.warning("Cotización sin conversión a USD (API de tasas no disponible): %s", exc)
            avisos.append("conversion_no_disponible")

        return Cotizacion(
            herramienta_id=herramienta.id,
            herramienta_nombre=herramienta.nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            dias=costo.dias,
            costo_alquiler=costo.total,
            moneda=costo.moneda,
            seguro=seguro,
            total=total,
            total_usd=total_usd,
            cop_por_usd=cop_por_usd,
            tasa_actualizada_en=fecha_tasa,
            avisos=tuple(avisos),
        )
