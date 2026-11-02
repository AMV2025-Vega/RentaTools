"""
Calculadoras de costo (implementaciones del puerto CalculadoraCosto).

Patrón ADAPTER + estrategia Strangler:
  - CostoHttpAdapter: traduce nuestro puerto al contrato HTTP del microservicio Flask.
  - CalculadoraLocal: la regla original que vivía en el monolito (respaldo).
  - CalculadoraConRespaldo: usa el microservicio y, si falla, cae al cálculo local
    (resiliencia: la caída del servicio de costos no tumba las reservas).
"""
import logging
from datetime import date
from decimal import Decimal, InvalidOperation

import requests

from apps.reservas.application.ports import CalculadoraCosto, ServicioExternoError
from apps.reservas.domain.costo import ResultadoCosto, calcular_costo
from apps.reservas.domain.entities import dias_de_alquiler

logger = logging.getLogger(__name__)


class CalculadoraLocal(CalculadoraCosto):
    def calcular(self, fecha_inicio: date, fecha_fin: date, precios_por_dia: list[Decimal]) -> ResultadoCosto:
        return calcular_costo(dias_de_alquiler(fecha_inicio, fecha_fin), precios_por_dia)


class CostoHttpAdapter(CalculadoraCosto):
    def __init__(self, url: str, timeout: float = 3.0):
        self._url = url
        self._timeout = timeout

    def calcular(self, fecha_inicio: date, fecha_fin: date, precios_por_dia: list[Decimal]) -> ResultadoCosto:
        payload = {
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "herramientas": [{"precio_por_dia": str(p)} for p in precios_por_dia],
        }
        try:
            respuesta = requests.post(self._url, json=payload, timeout=self._timeout)
        except requests.RequestException as exc:
            raise ServicioExternoError(f"Servicio de costo inaccesible: {exc}") from exc

        if respuesta.status_code != 200:
            raise ServicioExternoError(f"Servicio de costo respondió {respuesta.status_code}: {respuesta.text[:200]}")
        try:
            datos = respuesta.json()
            return ResultadoCosto(
                dias=int(datos["dias_totales"]),
                total=Decimal(str(datos["costo_total"])).quantize(Decimal("0.01")),
                moneda=str(datos.get("moneda", "COP")),
            )
        except (ValueError, KeyError, InvalidOperation, TypeError) as exc:
            raise ServicioExternoError("Respuesta inválida del servicio de costo.") from exc


class CalculadoraConRespaldo(CalculadoraCosto):
    def __init__(self, principal: CalculadoraCosto, respaldo: CalculadoraCosto):
        self._principal = principal
        self._respaldo = respaldo

    def calcular(self, fecha_inicio: date, fecha_fin: date, precios_por_dia: list[Decimal]) -> ResultadoCosto:
        try:
            return self._principal.calcular(fecha_inicio, fecha_fin, precios_por_dia)
        except ServicioExternoError as exc:
            logger.warning("Usando cálculo local de costo (respaldo): %s", exc)
            return self._respaldo.calcular(fecha_inicio, fecha_fin, precios_por_dia)
