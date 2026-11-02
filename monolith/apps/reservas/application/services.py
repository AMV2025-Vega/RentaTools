"""
Capa de aplicación (Service Layer) del módulo de Reservas.

`ReservaService` orquesta los casos de uso. No sabe nada de HTTP, de Django ni
de qué implementación concreta de repositorio/notificador/calculadora usa:
recibe todas sus dependencias por constructor (DIP + inyección de dependencias).
"""
import logging
from datetime import date
from typing import Callable

from apps.compartido.excepciones import DominioError, NoEncontrado, Prohibido
from apps.compartido.puertos import AuditLogger, EventoAuditoria, Solicitante, TransactionManager
from apps.reservas.application.ports import (
    CalculadoraCosto,
    CatalogoHerramientas,
    Notificador,
    ReservaRepository,
)
from apps.reservas.domain.entities import RangoOcupado, Reserva
from apps.reservas.domain.reserva_builder import ReservaBuilder

logger = logging.getLogger(__name__)


class ReservaService:
    def __init__(
        self,
        repo: ReservaRepository,
        catalogo: CatalogoHerramientas,
        calculadora: CalculadoraCosto,
        notificador: Notificador,
        auditor: AuditLogger,
        tx: TransactionManager,
        reloj: Callable[[], date],
    ):
        self._repo = repo
        self._catalogo = catalogo
        self._calculadora = calculadora
        self._notificador = notificador
        self._auditor = auditor
        self._tx = tx
        self._reloj = reloj

    # ------------------------------------------------------------------ crear
    def crear_reserva(self, solicitante: Solicitante, herramienta_id: int, fecha_inicio: date, fecha_fin: date) -> Reserva:
        """Caso de uso: reservar una herramienta para un rango de fechas."""
        try:
            return self._crear(solicitante, herramienta_id, fecha_inicio, fecha_fin)
        except DominioError as exc:
            # La transacción ya fue revertida: el rechazo se audita aparte.
            self._auditar_rechazo(
                "RESERVA_RECHAZADA",
                solicitante.id,
                "",
                exc,
                {"herramienta_id": herramienta_id, "fecha_inicio": str(fecha_inicio), "fecha_fin": str(fecha_fin)},
            )
            raise

    def _crear(self, solicitante, herramienta_id, fecha_inicio, fecha_fin) -> Reserva:
        herramienta = self._catalogo.obtener(herramienta_id)
        if herramienta is None:
            raise NoEncontrado(f"No existe la herramienta {herramienta_id}.", "herramienta_no_encontrada")

        # 1) Builder: construye y valida la reserva (sin tocar la BD).
        nueva = (
            ReservaBuilder(hoy=self._reloj())
            .con_cliente(solicitante.id)
            .con_herramienta(herramienta)
            .con_fechas(fecha_inicio, fecha_fin)
            .build()
        )

        # 2) Costo: lo calcula el microservicio (con respaldo local) a través del puerto.
        costo = self._calculadora.calcular(nueva.fecha_inicio, nueva.fecha_fin, [herramienta.precio_por_dia])

        # 3) Persistencia + auditoría, atómicas. La BD garantiza que no haya solapes.
        with self._tx.atomic():
            reserva = self._repo.crear(nueva, costo)
            self._auditor.registrar(
                EventoAuditoria(
                    accion="RESERVA_CREADA",
                    entidad="reserva",
                    entidad_id=str(reserva.id),
                    resultado="EXITO",
                    actor_id=solicitante.id,
                    detalle={
                        "herramienta_id": herramienta.id,
                        "fecha_inicio": str(reserva.fecha_inicio),
                        "fecha_fin": str(reserva.fecha_fin),
                        "dias": reserva.dias,
                        "costo_total": str(reserva.costo_total),
                        "moneda": reserva.moneda,
                    },
                )
            )
            # 4) La notificación sale SOLO si la transacción hizo commit.
            self._tx.on_commit(
                lambda: self._notificar(
                    solicitante,
                    "Reserva registrada",
                    f"Hola {solicitante.nombre}, tu reserva #{reserva.id} de '{herramienta.nombre}' "
                    f"({reserva.fecha_inicio} a {reserva.fecha_fin}) quedó pendiente de pago por "
                    f"{reserva.costo_total} {reserva.moneda}.",
                )
            )
        return reserva

    # --------------------------------------------------------------- cancelar
    def cancelar_reserva(self, solicitante: Solicitante, reserva_id: int) -> Reserva:
        try:
            with self._tx.atomic():
                reserva = self._repo.obtener(reserva_id, bloquear=True)
                if reserva is None:
                    raise NoEncontrado(f"No existe la reserva {reserva_id}.", "reserva_no_encontrada")
                if reserva.cliente_id != solicitante.id:
                    raise Prohibido("Solo quien hizo la reserva puede cancelarla.", "no_es_el_cliente")
                cancelada = self._repo.guardar_estado(reserva.cancelar())
                self._auditor.registrar(
                    EventoAuditoria(
                        accion="RESERVA_CANCELADA",
                        entidad="reserva",
                        entidad_id=str(reserva.id),
                        resultado="EXITO",
                        actor_id=solicitante.id,
                        detalle={"estado_anterior": reserva.estado.value},
                    )
                )
                self._tx.on_commit(
                    lambda: self._notificar(solicitante, "Reserva cancelada", f"Tu reserva #{reserva.id} fue cancelada.")
                )
            return cancelada
        except DominioError as exc:
            self._auditar_rechazo("RESERVA_CANCELACION_RECHAZADA", solicitante.id, str(reserva_id), exc, {})
            raise

    # --------------------------------------------------------------- consultas
    def listar_mis_reservas(self, solicitante: Solicitante) -> list[Reserva]:
        return self._repo.listar_por_cliente(solicitante.id)

    def ocupacion(self, herramienta_id: int) -> list[RangoOcupado]:
        """Rangos de fechas ya tomados (para que el frontend los deshabilite)."""
        if self._catalogo.obtener(herramienta_id) is None:
            raise NoEncontrado(f"No existe la herramienta {herramienta_id}.", "herramienta_no_encontrada")
        return self._repo.listar_ocupacion(herramienta_id, self._reloj())

    # ---------------------------------------------------------------- helpers
    def _notificar(self, solicitante: Solicitante, asunto: str, mensaje: str) -> None:
        """Un fallo al notificar nunca debe deshacer ni romper una reserva ya confirmada."""
        try:
            self._notificador.enviar(solicitante.email, asunto, mensaje)
        except Exception:  # noqa: BLE001 - best effort; en la Entrega 2 pasa a Celery con reintentos
            logger.exception("No se pudo enviar la notificación '%s' a %s", asunto, solicitante.email)

    def _auditar_rechazo(self, accion: str, actor_id: int, entidad_id: str, exc: DominioError, detalle: dict) -> None:
        try:
            self._auditor.registrar(
                EventoAuditoria(
                    accion=accion,
                    entidad="reserva",
                    entidad_id=entidad_id,
                    resultado="RECHAZADO",
                    actor_id=actor_id,
                    detalle={**detalle, "motivo": exc.codigo, "mensaje": exc.mensaje},
                )
            )
        except Exception:  # noqa: BLE001
            logger.exception("No se pudo auditar el rechazo %s", accion)
