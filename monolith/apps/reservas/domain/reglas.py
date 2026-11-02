"""Reglas de negocio de Reservas reutilizables por varios casos de uso (Python puro)."""
from datetime import date

from apps.compartido.excepciones import ReglaNegocioViolada
from apps.reservas.domain.entities import dias_de_alquiler

MAX_DIAS_RESERVA = 30


def validar_rango_fechas(inicio: date, fin: date, hoy: date) -> None:
    """Única fuente de verdad de las reglas de fechas (reserva real y cotización)."""
    if inicio is None or fin is None:
        raise ReglaNegocioViolada("Las fechas de inicio y fin son obligatorias.", "fechas_obligatorias")
    if fin < inicio:
        raise ReglaNegocioViolada("La fecha de fin no puede ser anterior a la de inicio.", "fechas_invertidas")
    if inicio < hoy:
        raise ReglaNegocioViolada("La fecha de inicio no puede estar en el pasado.", "fecha_pasada")
    if dias_de_alquiler(inicio, fin) > MAX_DIAS_RESERVA:
        raise ReglaNegocioViolada(f"La reserva no puede superar {MAX_DIAS_RESERVA} días.", "reserva_muy_larga")
