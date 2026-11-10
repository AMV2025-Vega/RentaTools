"""
Servicio A PROVEER (Entrega 2): JSON público con información relevante del sistema,
pensado para que otros equipos/servicios lo consuman. Solo lectura y sin datos personales.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Callable


@dataclass(frozen=True)
class CategoriaConteo:
    categoria: str
    herramientas: int


@dataclass(frozen=True)
class ResumenSistema:
    herramientas_activas: int
    precio_promedio_dia: Decimal | None
    por_categoria: list[CategoriaConteo] = field(default_factory=list)
    reservas_total: int = 0
    reservas_por_estado: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EstadisticasPublicas:
    sistema: str
    version: str
    generado_en: datetime
    moneda: str
    resumen: ResumenSistema


class EstadisticasRepository(ABC):
    @abstractmethod
    def resumen(self) -> ResumenSistema: ...


class EstadisticasService:
    def __init__(self, repo: EstadisticasRepository, ahora: Callable[[], datetime]):
        self._repo = repo
        self._ahora = ahora

    def obtener(self) -> EstadisticasPublicas:
        return EstadisticasPublicas("RentaTools", "1.0", self._ahora(), "COP", self._repo.resumen())
