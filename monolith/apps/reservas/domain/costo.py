from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable


@dataclass(frozen=True)
class ResultadoCosto:
    dias: int
    total: Decimal
    moneda: str = "COP"


def calcular_costo(dias: int, precios_por_dia: Iterable[Decimal], moneda: str = "COP") -> ResultadoCosto:
    """Política de costo estándar: días × suma de tarifas diarias, redondeo comercial a 2 decimales."""
    total = (Decimal(dias) * sum((Decimal(p) for p in precios_por_dia), Decimal("0"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return ResultadoCosto(dias=dias, total=total, moneda=moneda)
