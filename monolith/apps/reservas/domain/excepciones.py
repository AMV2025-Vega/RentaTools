from apps.compartido.excepciones import Conflicto


class ConflictoDisponibilidad(Conflicto):
    """La herramienta ya está reservada en ese rango de fechas -> HTTP 409."""

    codigo = "herramienta_no_disponible"


class EstadoReservaInvalido(Conflicto):
    """La transición de estado solicitada no es válida desde el estado actual -> HTTP 409."""

    codigo = "estado_reserva_invalido"
