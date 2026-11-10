"""
Puertos (interfaces) transversales: auditoría, transacciones y actor.

Principio de Inversión de Dependencias (DIP): los servicios de aplicación
dependen de estas abstracciones; las implementaciones concretas (Django ORM,
logging, etc.) viven en `infrastructure/` y se inyectan en el "composition root".
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, ContextManager


@dataclass(frozen=True)
class Solicitante:
    """Usuario autenticado que ejecuta un caso de uso (DTO sin dependencias de Django)."""

    id: int
    nombre: str
    email: str
    idioma: str = ""  # idioma activo del usuario (es/en) para sus notificaciones


@dataclass(frozen=True)
class EventoAuditoria:
    """Hecho relevante que debe quedar registrado de forma inmutable."""

    accion: str  # p. ej. RESERVA_CREADA
    entidad: str  # p. ej. reserva
    resultado: str  # EXITO | RECHAZADO
    actor_id: int | None = None
    entidad_id: str = ""
    detalle: dict[str, Any] = field(default_factory=dict)


class AuditLogger(ABC):
    """Registra eventos de auditoría (append-only)."""

    @abstractmethod
    def registrar(self, evento: EventoAuditoria) -> None: ...


class TransactionManager(ABC):
    """Abstrae el manejo de transacciones y los efectos 'después del commit'."""

    @abstractmethod
    def atomic(self) -> ContextManager: ...

    @abstractmethod
    def on_commit(self, callback: Callable[[], None]) -> None: ...
