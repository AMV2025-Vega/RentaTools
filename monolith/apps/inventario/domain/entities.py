"""
Entidades del dominio de Inventario (Python puro, sin Django).
Las validaciones de negocio viven aquí, en el nivel de entidad.
"""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from apps.compartido.excepciones import ReglaNegocioViolada


class EstadoHerramienta(str, Enum):
    ACTIVA = "ACTIVA"
    MANTENIMIENTO = "MANTENIMIENTO"


@dataclass(frozen=True)
class HerramientaNueva:
    """Datos validados para publicar una herramienta."""

    propietario_id: int
    categoria_id: int
    nombre: str
    descripcion: str
    precio_por_dia: Decimal
    foto_url: str = ""

    def __post_init__(self):
        if not self.nombre or not self.nombre.strip():
            raise ReglaNegocioViolada("El nombre de la herramienta es obligatorio.", "nombre_obligatorio")
        if self.precio_por_dia is None or self.precio_por_dia <= Decimal("0"):
            raise ReglaNegocioViolada("El precio por día debe ser mayor que cero.", "precio_invalido")


@dataclass(frozen=True)
class Herramienta:
    id: int
    propietario_id: int
    categoria_id: int
    categoria_nombre: str
    nombre: str
    descripcion: str
    precio_por_dia: Decimal
    estado: EstadoHerramienta
    foto_url: str = ""

    @property
    def esta_activa(self) -> bool:
        return self.estado == EstadoHerramienta.ACTIVA


@dataclass(frozen=True)
class Categoria:
    id: int
    nombre: str
    descripcion: str = ""
