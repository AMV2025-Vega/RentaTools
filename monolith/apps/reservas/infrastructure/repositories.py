from datetime import date

from django.db import IntegrityError, transaction

from apps.reservas.application.ports import ReservaRepository
from apps.reservas.domain.costo import ResultadoCosto
from apps.reservas.domain.entities import (
    ESTADOS_QUE_BLOQUEAN,
    EstadoReserva,
    RangoOcupado,
    Reserva,
    ReservaNueva,
)
from apps.reservas.domain.excepciones import ConflictoDisponibilidad
from apps.reservas.models import Reserva as ReservaModel

NOMBRE_CONSTRAINT_SOLAPE = "reserva_sin_solape"


def _a_entidad(m: ReservaModel) -> Reserva:
    """Mapper ORM -> entidad de dominio."""
    return Reserva(
        id=m.id,
        cliente_id=m.cliente_id,
        herramienta_id=m.herramienta_id,
        fecha_inicio=m.fecha_inicio,
        fecha_fin=m.fecha_fin,
        dias=m.dias,
        costo_total=m.costo_total,
        moneda=m.moneda,
        estado=EstadoReserva(m.estado),
        creado_en=m.creado_en,
    )


def _es_violacion_de_solape(exc: IntegrityError) -> bool:
    diag = getattr(exc.__cause__, "diag", None)
    return getattr(diag, "constraint_name", None) == NOMBRE_CONSTRAINT_SOLAPE


class DjangoReservaRepository(ReservaRepository):
    def crear(self, nueva: ReservaNueva, costo: ResultadoCosto) -> Reserva:
        try:
            # Savepoint propio: permite traducir el error sin invalidar la transacción externa.
            with transaction.atomic():
                m = ReservaModel.objects.create(
                    cliente_id=nueva.cliente_id,
                    herramienta_id=nueva.herramienta_id,
                    fecha_inicio=nueva.fecha_inicio,
                    fecha_fin=nueva.fecha_fin,
                    dias=costo.dias,
                    costo_total=costo.total,
                    moneda=costo.moneda,
                    estado=EstadoReserva.PENDIENTE_PAGO.value,
                )
        except IntegrityError as exc:
            if _es_violacion_de_solape(exc):
                raise ConflictoDisponibilidad(
                    "La herramienta ya está reservada en alguna de esas fechas.", "herramienta_no_disponible"
                ) from exc
            raise
        return _a_entidad(m)

    def obtener(self, reserva_id: int, bloquear: bool = False) -> Reserva | None:
        qs = ReservaModel.objects.select_for_update() if bloquear else ReservaModel.objects
        m = qs.filter(pk=reserva_id).first()
        return _a_entidad(m) if m else None

    def guardar_estado(self, reserva: Reserva) -> Reserva:
        ReservaModel.objects.filter(pk=reserva.id).update(estado=reserva.estado.value)
        return self.obtener(reserva.id)

    def listar_por_cliente(self, cliente_id: int) -> list[Reserva]:
        return [_a_entidad(m) for m in ReservaModel.objects.filter(cliente_id=cliente_id)]

    def listar_ocupacion(self, herramienta_id: int, desde: date) -> list[RangoOcupado]:
        qs = ReservaModel.objects.filter(
            herramienta_id=herramienta_id,
            estado__in=[e.value for e in ESTADOS_QUE_BLOQUEAN],
            fecha_fin__gte=desde,
        ).order_by("fecha_inicio")
        return [RangoOcupado(m.fecha_inicio, m.fecha_fin) for m in qs]
