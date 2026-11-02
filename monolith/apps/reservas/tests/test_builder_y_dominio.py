"""Pruebas unitarias PURAS del dominio (sin base de datos)."""
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from apps.compartido.excepciones import ReglaNegocioViolada
from apps.reservas.domain.costo import calcular_costo
from apps.reservas.domain.entities import EstadoReserva, HerramientaReservable, Reserva
from apps.reservas.domain.excepciones import EstadoReservaInvalido
from apps.reservas.domain.reserva_builder import MAX_DIAS_RESERVA, ReservaBuilder

HOY = date(2026, 11, 1)
HERRAMIENTA = HerramientaReservable(id=7, propietario_id=1, nombre="Taladro", precio_por_dia=Decimal("12000.00"), activa=True)


def builder():
    return ReservaBuilder(hoy=HOY).con_cliente(2)


class ReservaBuilderTests(SimpleTestCase):
    def test_construye_reserva_valida(self):
        r = builder().con_herramienta(HERRAMIENTA).con_fechas(date(2026, 11, 5), date(2026, 11, 7)).build()
        self.assertEqual((r.cliente_id, r.herramienta_id, r.dias), (2, 7, 3))

    def test_un_solo_dia_cuenta_como_uno(self):
        r = builder().con_herramienta(HERRAMIENTA).con_fechas(date(2026, 11, 5), date(2026, 11, 5)).build()
        self.assertEqual(r.dias, 1)

    def test_rechaza_fecha_en_el_pasado(self):
        with self.assertRaises(ReglaNegocioViolada) as ctx:
            builder().con_fechas(date(2026, 10, 1), date(2026, 10, 2))
        self.assertEqual(ctx.exception.codigo, "fecha_pasada")

    def test_rechaza_fechas_invertidas(self):
        with self.assertRaises(ReglaNegocioViolada) as ctx:
            builder().con_fechas(date(2026, 11, 9), date(2026, 11, 8))
        self.assertEqual(ctx.exception.codigo, "fechas_invertidas")

    def test_rechaza_reservas_demasiado_largas(self):
        with self.assertRaises(ReglaNegocioViolada):
            builder().con_fechas(date(2026, 11, 2), date(2026, 12, 31))
        self.assertEqual(MAX_DIAS_RESERVA, 30)

    def test_rechaza_herramienta_inactiva(self):
        inactiva = HerramientaReservable(7, 1, "Taladro", Decimal("1"), activa=False)
        with self.assertRaises(ReglaNegocioViolada):
            builder().con_herramienta(inactiva)

    def test_rechaza_reservar_la_propia_herramienta(self):
        with self.assertRaises(ReglaNegocioViolada) as ctx:
            ReservaBuilder(hoy=HOY).con_cliente(1).con_herramienta(HERRAMIENTA)
        self.assertEqual(ctx.exception.codigo, "reserva_propia")

    def test_build_incompleto_falla(self):
        with self.assertRaises(ReglaNegocioViolada) as ctx:
            builder().build()
        self.assertEqual(ctx.exception.codigo, "reserva_incompleta")


class CostoYEstadosTests(SimpleTestCase):
    def test_costo_estandar(self):
        r = calcular_costo(3, [Decimal("12000.00"), Decimal("8000.50")])
        self.assertEqual(r.total, Decimal("60001.50"))

    def _reserva(self, estado):
        return Reserva(1, 2, 7, date(2026, 11, 5), date(2026, 11, 6), 2, Decimal("1"), "COP", estado)

    def test_cancelar_pendiente_o_confirmada(self):
        for e in (EstadoReserva.PENDIENTE_PAGO, EstadoReserva.CONFIRMADA):
            self.assertEqual(self._reserva(e).cancelar().estado, EstadoReserva.CANCELADA)

    def test_no_se_cancela_dos_veces_ni_una_finalizada(self):
        for e in (EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA):
            with self.assertRaises(EstadoReservaInvalido):
                self._reserva(e).cancelar()
