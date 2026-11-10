"""Lógica de cotización del seguro (determinista, para poder probarla)."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

ASEGURADORA = "AseguraTools S.A.S. (simulada)"
MONEDA = "COP"
TASA_POR_CATEGORIA = {
    "construcción": Decimal("0.06"),
    "jardinería": Decimal("0.05"),
    "electricidad": Decimal("0.07"),
    "carpintería": Decimal("0.04"),
    "limpieza": Decimal("0.03"),
}
TASA_POR_DEFECTO = Decimal("0.05")
PRIMA_MINIMA = Decimal("2000.00")
RECARGO_POR_DIA = Decimal("500.00")
MAX_DIAS = 30
CENT = Decimal("0.01")


class CotizacionError(Exception):
    pass


def _dinero(valor) -> Decimal:
    try:
        d = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise CotizacionError("'valor_alquiler' debe ser un número válido.") from None
    if not d.is_finite() or d <= 0:
        raise CotizacionError("'valor_alquiler' debe ser mayor que cero.")
    return d


def cotizar_seguro(data) -> dict:
    if not isinstance(data, dict):
        raise CotizacionError("El cuerpo debe ser un objeto JSON.")
    if "valor_alquiler" not in data:
        raise CotizacionError("El campo 'valor_alquiler' es obligatorio.")
    if "dias" not in data:
        raise CotizacionError("El campo 'dias' es obligatorio.")

    valor = _dinero(data["valor_alquiler"])
    dias = data["dias"]
    if isinstance(dias, bool) or not isinstance(dias, int) or not 1 <= dias <= MAX_DIAS:
        raise CotizacionError(f"'dias' debe ser un entero entre 1 y {MAX_DIAS}.")
    if data.get("moneda", MONEDA) != MONEDA:
        raise CotizacionError(f"Solo se admite la moneda {MONEDA}.")

    categoria = str(data.get("categoria") or "").strip()
    tasa = TASA_POR_CATEGORIA.get(categoria.lower(), TASA_POR_DEFECTO)

    prima = (max(PRIMA_MINIMA, valor * tasa) + RECARGO_POR_DIA * dias).quantize(CENT, rounding=ROUND_HALF_UP)
    cobertura = max(valor * 20, Decimal("200000.00")).quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "aseguradora": ASEGURADORA,
        "prima": str(prima),
        "cobertura_maxima": str(cobertura),
        "moneda": MONEDA,
        "tasa_aplicada": str(tasa),
    }
