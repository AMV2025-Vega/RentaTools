from datetime import datetime
from decimal import Decimal, InvalidOperation


class CalculoError(Exception):
    pass


def calcular_costo_reserva(data):
    if not isinstance(data, dict):
        raise CalculoError("El cuerpo de la petición debe ser un objeto JSON.")

    if "fecha_inicio" not in data or not data["fecha_inicio"]:
        raise CalculoError("El campo 'fecha_inicio' es obligatorio.")

    if "fecha_fin" not in data or not data["fecha_fin"]:
        raise CalculoError("El campo 'fecha_fin' es obligatorio.")

    if "herramientas" not in data:
        raise CalculoError("El campo 'herramientas' es obligatorio.")

    if not isinstance(data["herramientas"], list):
        raise CalculoError("El campo 'herramientas' debe ser una lista.")

    if len(data["herramientas"]) == 0:
        raise CalculoError(
            "La lista de 'herramientas' no puede estar vacía."
        )

    try:
        inicio = datetime.strptime(data["fecha_inicio"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise CalculoError(
            "Formato de 'fecha_inicio' inválido. Debe ser YYYY-MM-DD."
        )

    try:
        fin = datetime.strptime(data["fecha_fin"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise CalculoError(
            "Formato de 'fecha_fin' inválido. Debe ser YYYY-MM-DD."
        )

    if fin < inicio:
        raise CalculoError(
            "La fecha de fin no puede ser anterior a la fecha de inicio."
        )

    dias_totales = (fin - inicio).days + 1

    suma_precios = Decimal("0.00")
    for idx, h in enumerate(data["herramientas"]):
        if not isinstance(h, dict):
            raise CalculoError(
                f"La herramienta en el índice {idx} debe ser un objeto JSON."
            )

        if "precio_por_dia" not in h or h["precio_por_dia"] is None:
            raise CalculoError(
                f"La herramienta en el índice {idx} no contiene 'precio_por_dia'."
            )

        try:
            precio_dec = Decimal(str(h["precio_por_dia"]))
        except (InvalidOperation, TypeError, ValueError):
            raise CalculoError(
                f"El precio_por_dia de la herramienta en el índice {idx} debe ser un número válido."
            )

        if precio_dec < Decimal("0"):
            raise CalculoError(
                f"El precio_por_dia de la herramienta en el índice {idx} no puede ser negativo."
            )

        suma_precios += precio_dec

    costo_total = Decimal(dias_totales) * suma_precios

    return {
        "dias_totales": dias_totales,
        "costo_total": float(costo_total.quantize(Decimal("0.01"))),
        "moneda": "COP",
    }
