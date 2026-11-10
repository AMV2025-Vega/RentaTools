from decimal import Decimal

from django.db.models import Avg, Count

from apps.inventario.models import Herramienta
from apps.publico.application.services import CategoriaConteo, EstadisticasRepository, ResumenSistema
from apps.reservas.models import Reserva


class DjangoEstadisticasRepository(EstadisticasRepository):
    """Modelo de LECTURA (reporting). Si los módulos se extraen, este repo pasa a agregar sus APIs."""

    def resumen(self) -> ResumenSistema:
        activas = Herramienta.objects.filter(estado=Herramienta.Estado.ACTIVA)
        promedio = activas.aggregate(p=Avg("precio_por_dia"))["p"]
        por_categoria = [
            CategoriaConteo(f["categoria__nombre"], f["n"])
            for f in activas.values("categoria__nombre").annotate(n=Count("id")).order_by("categoria__nombre")
        ]
        por_estado = {e.value: 0 for e in Reserva.Estado}  # todos los estados, aunque sea con 0
        for f in Reserva.objects.values("estado").annotate(n=Count("id")):
            por_estado[f["estado"]] = f["n"]
        return ResumenSistema(
            herramientas_activas=activas.count(),
            precio_promedio_dia=promedio.quantize(Decimal("0.01")) if promedio is not None else None,
            por_categoria=por_categoria,
            reservas_total=sum(por_estado.values()),
            reservas_por_estado=por_estado,
        )
