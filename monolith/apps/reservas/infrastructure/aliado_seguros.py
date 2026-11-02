"""
ADAPTER del servicio ALIADO de seguros.

Traduce nuestro puerto `ServicioSeguros` al contrato HTTP publicado por el aliado
(docs/contrato-aliado.md). Si el aliado cambia su JSON, solo cambia este archivo.
"""
from decimal import Decimal, InvalidOperation

import requests

from apps.reservas.application.ports import ServicioExternoError, ServicioSeguros
from apps.reservas.domain.cotizacion import CotizacionSeguro


class AliadoSegurosHttpAdapter(ServicioSeguros):
    def __init__(self, base_url: str, api_key: str = "", timeout: float = 3.0):
        self._url = f"{base_url.rstrip('/')}/seguros/cotizar"
        self._headers = {"X-API-Key": api_key} if api_key else {}
        self._timeout = timeout

    def cotizar(self, valor_alquiler: Decimal, dias: int, categoria: str) -> CotizacionSeguro:
        payload = {"valor_alquiler": str(valor_alquiler), "dias": dias, "categoria": categoria, "moneda": "COP"}
        try:
            r = requests.post(self._url, json=payload, headers=self._headers, timeout=self._timeout)
        except requests.RequestException as exc:
            raise ServicioExternoError(f"Aliado de seguros inaccesible: {exc}") from exc
        if r.status_code != 200:
            raise ServicioExternoError(f"Aliado de seguros respondió {r.status_code}: {r.text[:200]}")
        try:
            d = r.json()
            return CotizacionSeguro(
                aseguradora=str(d["aseguradora"]),
                prima=Decimal(str(d["prima"])),
                cobertura_maxima=Decimal(str(d["cobertura_maxima"])),
                moneda=str(d.get("moneda", "COP")),
            )
        except (ValueError, KeyError, InvalidOperation, TypeError) as exc:
            raise ServicioExternoError("Respuesta inválida del aliado de seguros.") from exc
