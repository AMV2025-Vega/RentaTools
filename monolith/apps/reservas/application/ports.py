"""
Puertos del módulo de Reservas (DIP). Los define el consumidor (este módulo);
las implementaciones concretas viven en infrastructure/.
"""
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from apps.reservas.domain.costo import ResultadoCosto
from apps.reservas.domain.entities import (
    EstadoReserva,
    HerramientaReservable,
    RangoOcupado,
    Reserva,
    ReservaNueva,
)


class ServicioExternoError(Exception):
    """Falla de un servicio externo (red, timeout, respuesta inválida)."""


class ReservaRepository(ABC):
    @abstractmethod
    def crear(self, nueva: ReservaNueva, costo: ResultadoCosto) -> Reserva:
        """Persiste. Debe lanzar ConflictoDisponibilidad si las fechas se solapan."""

    @abstractmethod
    def obtener(self, reserva_id: int, bloquear: bool = False) -> Reserva | None: ...

    @abstractmethod
    def guardar_estado(self, reserva: Reserva) -> Reserva: ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> list[Reserva]: ...

    @abstractmethod
    def listar_ocupacion(self, herramienta_id: int, desde: date) -> list[RangoOcupado]: ...


class CatalogoHerramientas(ABC):
    @abstractmethod
    def obtener(self, herramienta_id: int) -> HerramientaReservable | None: ...


class CalculadoraCosto(ABC):
    @abstractmethod
    def calcular(self, fecha_inicio: date, fecha_fin: date, precios_por_dia: list[Decimal]) -> ResultadoCosto:
        """Puede lanzar ServicioExternoError si la implementación depende de un servicio remoto."""


class Notificador(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, asunto: str, mensaje: str) -> None: ...


__all__ = [
    "ServicioExternoError",
    "ReservaRepository",
    "CatalogoHerramientas",
    "CalculadoraCosto",
    "Notificador",
    "EstadoReserva",
]
