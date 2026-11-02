"""
Patrón creacional BUILDER para la entidad más compleja del sistema: la Reserva.

Construye paso a paso (interfaz fluida) y valida las reglas de negocio ANTES de
producir una `ReservaNueva`. No persiste ni calcula precios: eso corresponde a
repositorio y calculadora (SRP). La fecha de "hoy" se inyecta para poder probarlo.
"""
from datetime import date

from apps.compartido.excepciones import ReglaNegocioViolada
from apps.reservas.domain.entities import HerramientaReservable, ReservaNueva, dias_de_alquiler

MAX_DIAS_RESERVA = 30


class ReservaBuilder:
    def __init__(self, hoy: date):
        self._hoy = hoy
        self._cliente_id: int | None = None
        self._herramienta: HerramientaReservable | None = None
        self._inicio: date | None = None
        self._fin: date | None = None

    def con_cliente(self, cliente_id: int) -> "ReservaBuilder":
        if not cliente_id:
            raise ReglaNegocioViolada("El cliente es obligatorio.", "cliente_obligatorio")
        self._cliente_id = cliente_id
        return self

    def con_herramienta(self, herramienta: HerramientaReservable) -> "ReservaBuilder":
        if herramienta is None:
            raise ReglaNegocioViolada("La herramienta es obligatoria.", "herramienta_obligatoria")
        if not herramienta.activa:
            raise ReglaNegocioViolada(f"La herramienta '{herramienta.nombre}' no está disponible para alquiler.", "herramienta_inactiva")
        if self._cliente_id is not None and herramienta.propietario_id == self._cliente_id:
            raise ReglaNegocioViolada("No puedes reservar tu propia herramienta.", "reserva_propia")
        self._herramienta = herramienta
        return self

    def con_fechas(self, inicio: date, fin: date) -> "ReservaBuilder":
        if inicio is None or fin is None:
            raise ReglaNegocioViolada("Las fechas de inicio y fin son obligatorias.", "fechas_obligatorias")
        if fin < inicio:
            raise ReglaNegocioViolada("La fecha de fin no puede ser anterior a la de inicio.", "fechas_invertidas")
        if inicio < self._hoy:
            raise ReglaNegocioViolada("La fecha de inicio no puede estar en el pasado.", "fecha_pasada")
        if dias_de_alquiler(inicio, fin) > MAX_DIAS_RESERVA:
            raise ReglaNegocioViolada(f"La reserva no puede superar {MAX_DIAS_RESERVA} días.", "reserva_muy_larga")
        self._inicio, self._fin = inicio, fin
        return self

    def build(self) -> ReservaNueva:
        faltantes = [
            nombre
            for nombre, valor in (("cliente", self._cliente_id), ("herramienta", self._herramienta), ("fechas", self._inicio))
            if valor is None
        ]
        if faltantes:
            raise ReglaNegocioViolada(f"Faltan datos para construir la reserva: {', '.join(faltantes)}.", "reserva_incompleta")
        return ReservaNueva(
            cliente_id=self._cliente_id,
            herramienta_id=self._herramienta.id,
            fecha_inicio=self._inicio,
            fecha_fin=self._fin,
        )
