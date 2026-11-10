"""
ADAPTER de la API de TERCEROS de tasas de cambio (ExchangeRate-API, acceso abierto, sin llave).

  GET https://open.er-api.com/v6/latest/{BASE}  ->  {"result": "success", "rates": {...}, ...}

Las tasas se actualizan 1 vez al día y la API limita peticiones (HTTP 429), por eso
`ConversorConCache` guarda la tasa y, si el tercero falla, sirve la última conocida.
"""
import logging
import time
from decimal import Decimal, InvalidOperation

import requests

from apps.reservas.application.ports import ConversorMoneda, ServicioExternoError
from apps.reservas.domain.cotizacion import TasaCambio

logger = logging.getLogger(__name__)


class TasaCambioHttpAdapter(ConversorMoneda):
    def __init__(self, url_plantilla: str = "https://open.er-api.com/v6/latest/{base}", timeout: float = 3.0):
        self._url = url_plantilla
        self._timeout = timeout

    def obtener_tasa(self, de: str, a: str) -> TasaCambio:
        try:
            r = requests.get(self._url.format(base=de), timeout=self._timeout)
        except requests.RequestException as exc:
            raise ServicioExternoError(f"API de tasas inaccesible: {exc}") from exc
        if r.status_code != 200:
            raise ServicioExternoError(f"API de tasas respondió {r.status_code}")
        try:
            d = r.json()
            if d.get("result") != "success":
                raise ServicioExternoError(f"API de tasas devolvió error: {d.get('error-type')}")
            tasa = Decimal(str(d["rates"][a]))
            if tasa <= 0:
                raise ValueError("tasa no positiva")
            return TasaCambio(de=de, a=a, tasa=tasa, actualizada_en=str(d.get("time_last_update_utc", "")))
        except ServicioExternoError:
            raise
        except (ValueError, KeyError, InvalidOperation, TypeError, AttributeError) as exc:
            raise ServicioExternoError("Respuesta inválida de la API de tasas.") from exc


class ConversorConCache(ConversorMoneda):
    """Decorator: caché con vigencia corta + respaldo con la última tasa conocida."""

    def __init__(self, delegado: ConversorMoneda, cache, ttl_fresco: int = 6 * 3600, ttl_respaldo: int = 7 * 24 * 3600, reloj=time.time):
        self._delegado, self._cache = delegado, cache
        self._ttl_fresco, self._ttl_respaldo, self._reloj = ttl_fresco, ttl_respaldo, reloj

    def obtener_tasa(self, de: str, a: str) -> TasaCambio:
        clave = f"fx:{de}:{a}"
        guardado = self._cache.get(clave)
        if guardado and self._reloj() - guardado["guardado_en"] < self._ttl_fresco:
            return self._a_tasa(de, a, guardado)
        try:
            tasa = self._delegado.obtener_tasa(de, a)
        except ServicioExternoError:
            if guardado:
                logger.warning("API de tasas caída: usando la última tasa conocida (%s->%s).", de, a)
                return self._a_tasa(de, a, guardado)
            raise
        self._cache.set(
            clave,
            {"tasa": str(tasa.tasa), "actualizada_en": tasa.actualizada_en, "guardado_en": self._reloj()},
            self._ttl_respaldo,
        )
        return tasa

    @staticmethod
    def _a_tasa(de, a, g) -> TasaCambio:
        return TasaCambio(de=de, a=a, tasa=Decimal(g["tasa"]), actualizada_en=g["actualizada_en"])
