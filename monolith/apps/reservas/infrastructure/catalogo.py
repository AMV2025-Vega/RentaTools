"""
Adaptador hacia el módulo Inventario. Reservas NO importa los modelos de
Inventario: usa su servicio público. Si Inventario pasa a ser un microservicio,
solo se reemplaza este archivo por un cliente HTTP.
"""
from apps.compartido.excepciones import NoEncontrado
from apps.inventario.composition import construir_herramienta_service
from apps.reservas.application.ports import CatalogoHerramientas
from apps.reservas.domain.entities import HerramientaReservable


class CatalogoInventarioAdapter(CatalogoHerramientas):
    def obtener(self, herramienta_id: int) -> HerramientaReservable | None:
        try:
            h = construir_herramienta_service().obtener(herramienta_id)
        except NoEncontrado:
            return None
        return HerramientaReservable(
            id=h.id,
            propietario_id=h.propietario_id,
            nombre=h.nombre,
            precio_por_dia=h.precio_por_dia,
            activa=h.esta_activa,
        )
