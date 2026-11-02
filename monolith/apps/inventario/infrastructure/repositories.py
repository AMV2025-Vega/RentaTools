from apps.inventario.application.ports import HerramientaRepository
from apps.inventario.domain.entities import (
    Categoria,
    EstadoHerramienta,
    Herramienta,
    HerramientaNueva,
)
from apps.inventario.models import Categoria as CategoriaModel
from apps.inventario.models import Herramienta as HerramientaModel


def _a_entidad(m: HerramientaModel) -> Herramienta:
    """Mapper ORM -> entidad de dominio (el dominio nunca ve modelos de Django)."""
    return Herramienta(
        id=m.id,
        propietario_id=m.propietario_id,
        categoria_id=m.categoria_id,
        categoria_nombre=m.categoria.nombre,
        nombre=m.nombre,
        descripcion=m.descripcion,
        precio_por_dia=m.precio_por_dia,
        estado=EstadoHerramienta(m.estado),
        foto_url=m.foto_url,
    )


class DjangoHerramientaRepository(HerramientaRepository):
    def crear(self, nueva: HerramientaNueva) -> Herramienta:
        m = HerramientaModel.objects.create(
            propietario_id=nueva.propietario_id,
            categoria_id=nueva.categoria_id,
            nombre=nueva.nombre,
            descripcion=nueva.descripcion,
            precio_por_dia=nueva.precio_por_dia,
            foto_url=nueva.foto_url,
        )
        return _a_entidad(HerramientaModel.objects.select_related("categoria").get(pk=m.pk))

    def obtener(self, herramienta_id: int) -> Herramienta | None:
        m = HerramientaModel.objects.select_related("categoria").filter(pk=herramienta_id).first()
        return _a_entidad(m) if m else None

    def listar(self, categoria_id, propietario_id, solo_activas):
        qs = HerramientaModel.objects.select_related("categoria")
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        if propietario_id:
            qs = qs.filter(propietario_id=propietario_id)
        if solo_activas:
            qs = qs.filter(estado=HerramientaModel.Estado.ACTIVA)
        return [_a_entidad(m) for m in qs]

    def actualizar_estado(self, herramienta_id: int, estado: EstadoHerramienta) -> Herramienta:
        HerramientaModel.objects.filter(pk=herramienta_id).update(estado=estado.value)
        return self.obtener(herramienta_id)

    def categoria_existe(self, categoria_id: int) -> bool:
        return CategoriaModel.objects.filter(pk=categoria_id).exists()

    def listar_categorias(self) -> list[Categoria]:
        return [Categoria(c.id, c.nombre, c.descripcion) for c in CategoriaModel.objects.all()]
