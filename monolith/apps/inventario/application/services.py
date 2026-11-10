from decimal import Decimal

from apps.compartido.excepciones import NoEncontrado, Prohibido, ReglaNegocioViolada
from apps.compartido.puertos import AuditLogger, EventoAuditoria, TransactionManager
from apps.inventario.application.ports import HerramientaRepository
from apps.inventario.domain.entities import (
    Categoria,
    EstadoHerramienta,
    Herramienta,
    HerramientaNueva,
)


class HerramientaService:
    """
    Casos de uso del catálogo. Es también la API pública del módulo para otros
    módulos (p. ej. Reservas consulta `obtener`): si Inventario se extrae a un
    microservicio, solo cambia el adaptador que usa Reservas, no esta clase.
    """

    def __init__(self, repo: HerramientaRepository, auditor: AuditLogger, tx: TransactionManager):
        self._repo = repo
        self._auditor = auditor
        self._tx = tx

    def publicar(
        self,
        propietario_id: int,
        categoria_id: int,
        nombre: str,
        descripcion: str,
        precio_por_dia: Decimal,
        foto_url: str = "",
    ) -> Herramienta:
        if not self._repo.categoria_existe(categoria_id):
            raise NoEncontrado(f"No existe la categoría {categoria_id}.", "categoria_no_encontrada")
        nueva = HerramientaNueva(propietario_id, categoria_id, nombre.strip(), descripcion, precio_por_dia, foto_url)
        with self._tx.atomic():
            herramienta = self._repo.crear(nueva)
            self._auditor.registrar(
                EventoAuditoria(
                    accion="HERRAMIENTA_PUBLICADA",
                    entidad="herramienta",
                    entidad_id=str(herramienta.id),
                    resultado="EXITO",
                    actor_id=propietario_id,
                    detalle={"precio_por_dia": str(precio_por_dia)},
                )
            )
        return herramienta

    def obtener(self, herramienta_id: int) -> Herramienta:
        herramienta = self._repo.obtener(herramienta_id)
        if herramienta is None:
            raise NoEncontrado(f"No existe la herramienta {herramienta_id}.", "herramienta_no_encontrada")
        return herramienta

    def listar(self, categoria_id: int | None = None, propietario_id: int | None = None, solo_activas: bool = True) -> list[Herramienta]:
        return self._repo.listar(categoria_id, propietario_id, solo_activas)

    def listar_categorias(self) -> list[Categoria]:
        return self._repo.listar_categorias()

    def cambiar_estado(self, actor_id: int, herramienta_id: int, nuevo_estado: str) -> Herramienta:
        try:
            estado = EstadoHerramienta(nuevo_estado)
        except ValueError as exc:
            raise ReglaNegocioViolada("Estado de herramienta no válido.", "estado_invalido") from exc
        herramienta = self.obtener(herramienta_id)
        if herramienta.propietario_id != actor_id:
            raise Prohibido("Solo el propietario puede cambiar el estado de la herramienta.", "no_es_propietario")
        with self._tx.atomic():
            actualizada = self._repo.actualizar_estado(herramienta_id, estado)
            self._auditor.registrar(
                EventoAuditoria(
                    accion="HERRAMIENTA_ESTADO_CAMBIADO",
                    entidad="herramienta",
                    entidad_id=str(herramienta_id),
                    resultado="EXITO",
                    actor_id=actor_id,
                    detalle={"de": herramienta.estado.value, "a": estado.value},
                )
            )
        return actualizada
