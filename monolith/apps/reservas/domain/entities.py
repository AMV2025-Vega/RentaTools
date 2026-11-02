"""
Entidades y reglas del dominio de Reservas (Python puro, sin Django).
"""
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from apps.reservas.domain.excepciones import EstadoReservaInvalido


class EstadoReserva(str, Enum):
    PENDIENTE_PAGO = "PENDIENTE_PAGO"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    FINALIZADA = "FINALIZADA"


# Estados que ocupan la herramienta (los demás liberan las fechas).
ESTADOS_QUE_BLOQUEAN = (EstadoReserva.PENDIENTE_PAGO, EstadoReserva.CONFIRMADA)


def dias_de_alquiler(fecha_inicio: date, fecha_fin: date) -> int:
    """Regla de negocio: el día de inicio y el de fin cuentan (inicio == fin -> 1 día)."""
    return (fecha_fin - fecha_inicio).days + 1


@dataclass(frozen=True)
class HerramientaReservable:
    """Vista mínima de una herramienta para el módulo de Reservas (anti-corruption)."""

    id: int
    propietario_id: int
    nombre: str
    precio_por_dia: Decimal
    activa: bool


@dataclass(frozen=True)
class ReservaNueva:
    """Resultado del Builder: una reserva ya validada pero aún no persistida."""

    cliente_id: int
    herramienta_id: int
    fecha_inicio: date
    fecha_fin: date

    @property
    def dias(self) -> int:
        return dias_de_alquiler(self.fecha_inicio, self.fecha_fin)


@dataclass(frozen=True)
class RangoOcupado:
    fecha_inicio: date
    fecha_fin: date


@dataclass(frozen=True)
class Reserva:
    id: int
    cliente_id: int
    herramienta_id: int
    fecha_inicio: date
    fecha_fin: date
    dias: int
    costo_total: Decimal
    moneda: str
    estado: EstadoReserva
    creado_en: datetime | None = None

    def cancelar(self) -> "Reserva":
        """Regla de negocio: solo se cancela lo que aún está vigente."""
        if self.estado not in ESTADOS_QUE_BLOQUEAN:
            raise EstadoReservaInvalido(
                f"No se puede cancelar una reserva en estado {self.estado.value}.", "no_se_puede_cancelar"
            )
        return replace(self, estado=EstadoReserva.CANCELADA)
