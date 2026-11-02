"""Objetos de valor de la cotización (Python puro)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CotizacionSeguro:
    aseguradora: str
    prima: Decimal
    cobertura_maxima: Decimal
    moneda: str


@dataclass(frozen=True)
class TasaCambio:
    de: str
    a: str
    tasa: Decimal  # unidades de `a` por 1 unidad de `de`
    actualizada_en: str


@dataclass(frozen=True)
class Cotizacion:
    herramienta_id: int
    herramienta_nombre: str
    fecha_inicio: date
    fecha_fin: date
    dias: int
    costo_alquiler: Decimal
    moneda: str
    seguro: CotizacionSeguro | None
    total: Decimal  # alquiler (+ prima si hay seguro)
    total_usd: Decimal | None
    cop_por_usd: Decimal | None
    tasa_actualizada_en: str | None
    avisos: tuple[str, ...] = ()
