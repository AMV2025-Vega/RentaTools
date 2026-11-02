from abc import ABC, abstractmethod

from apps.inventario.domain.entities import (
    Categoria,
    EstadoHerramienta,
    Herramienta,
    HerramientaNueva,
)


class HerramientaRepository(ABC):
    @abstractmethod
    def crear(self, nueva: HerramientaNueva) -> Herramienta: ...

    @abstractmethod
    def obtener(self, herramienta_id: int) -> Herramienta | None: ...

    @abstractmethod
    def listar(self, categoria_id: int | None, propietario_id: int | None, solo_activas: bool) -> list[Herramienta]: ...

    @abstractmethod
    def actualizar_estado(self, herramienta_id: int, estado: EstadoHerramienta) -> Herramienta: ...

    @abstractmethod
    def categoria_existe(self, categoria_id: int) -> bool: ...

    @abstractmethod
    def listar_categorias(self) -> list[Categoria]: ...
