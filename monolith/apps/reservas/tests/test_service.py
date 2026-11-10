"""
Pruebas del Service Layer con dobles de prueba (fakes): demuestran que el
servicio depende de abstracciones y se puede probar sin Django ni base de datos.
"""
from contextlib import nullcontext
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from apps.compartido.excepciones import NoEncontrado, Prohibido, ReglaNegocioViolada
from apps.compartido.puertos import AuditLogger, Solicitante, TransactionManager
from apps.reservas.application.ports import (
    CalculadoraCosto,
    CatalogoHerramientas,
    Notificador,
    ReservaRepository,
    ServicioExternoError,
)
from apps.reservas.application.services import ReservaService
from apps.reservas.domain.costo import ResultadoCosto
from apps.reservas.domain.entities import EstadoReserva, HerramientaReservable, Reserva
from apps.reservas.domain.excepciones import ConflictoDisponibilidad
from apps.reservas.infrastructure.costo import CalculadoraConRespaldo, CalculadoraLocal
from apps.reservas.infrastructure.notificadores import NotificadorConsola, NotificadorEmail, NotificadorFactory

HOY = date(2026, 11, 1)
CLIENTE = Solicitante(id=2, nombre="Ana", email="ana@test.com")


class RepoFake(ReservaRepository):
    def __init__(self, conflicto=False):
        self.conflicto, self.reservas = conflicto, {}

    def crear(self, nueva, costo):
        if self.conflicto:
            raise ConflictoDisponibilidad("ocupada")
        r = Reserva(len(self.reservas) + 1, nueva.cliente_id, nueva.herramienta_id, nueva.fecha_inicio, nueva.fecha_fin,
                    costo.dias, costo.total, costo.moneda, EstadoReserva.PENDIENTE_PAGO)
        self.reservas[r.id] = r
        return r

    def obtener(self, reserva_id, bloquear=False):
        return self.reservas.get(reserva_id)

    def guardar_estado(self, reserva):
        self.reservas[reserva.id] = reserva
        return reserva

    def listar_por_cliente(self, cliente_id):
        return [r for r in self.reservas.values() if r.cliente_id == cliente_id]

    def listar_ocupacion(self, herramienta_id, desde):
        return []


class CatalogoFake(CatalogoHerramientas):
    def obtener(self, herramienta_id):
        if herramienta_id == 7:
            return HerramientaReservable(7, 1, "Taladro", Decimal("10000.00"), True)
        return None


class CalculadoraFake(CalculadoraCosto):
    def calcular(self, fecha_inicio, fecha_fin, precios_por_dia):
        return ResultadoCosto(dias=2, total=Decimal("20000.00"))


class NotificadorFake(Notificador):
    def __init__(self, falla=False):
        self.enviados, self.falla = [], falla

    def enviar(self, destinatario, plantilla, contexto, idioma=""):
        if self.falla:
            raise RuntimeError("smtp caído")
        self.enviados.append((destinatario, plantilla))


class AuditorFake(AuditLogger):
    def __init__(self):
        self.eventos = []

    def registrar(self, evento):
        self.eventos.append(evento)


class TxFake(TransactionManager):
    """Acumula los callbacks y los ejecuta al salir del bloque sin error (simula commit)."""

    def __init__(self):
        self._pend = []

    def atomic(self):
        tx = self

        class _Ctx:
            def __enter__(self_inner):
                return None

            def __exit__(self_inner, tipo, *_):
                if tipo is None:
                    for cb in tx._pend:
                        cb()
                tx._pend = []
                return False

        return _Ctx()

    def on_commit(self, callback):
        self._pend.append(callback)


def servicio(repo=None, notificador=None):
    repo, notificador = repo or RepoFake(), notificador or NotificadorFake()
    auditor = AuditorFake()
    svc = ReservaService(repo, CatalogoFake(), CalculadoraFake(), notificador, auditor, TxFake(), lambda: HOY)
    return svc, repo, notificador, auditor


class ReservaServiceTests(SimpleTestCase):
    def test_crear_ok_persiste_audita_y_notifica(self):
        svc, repo, notif, aud = servicio()
        r = svc.crear_reserva(CLIENTE, 7, date(2026, 11, 5), date(2026, 11, 6))
        self.assertEqual(r.costo_total, Decimal("20000.00"))
        self.assertEqual([e.accion for e in aud.eventos], ["RESERVA_CREADA"])
        self.assertEqual(notif.enviados, [("ana@test.com", "reserva_creada")])

    def test_herramienta_inexistente_es_404_y_se_audita_el_rechazo(self):
        svc, _, notif, aud = servicio()
        with self.assertRaises(NoEncontrado):
            svc.crear_reserva(CLIENTE, 999, date(2026, 11, 5), date(2026, 11, 6))
        self.assertEqual(aud.eventos[0].accion, "RESERVA_RECHAZADA")
        self.assertEqual(aud.eventos[0].resultado, "RECHAZADO")
        self.assertEqual(notif.enviados, [])

    def test_regla_de_negocio_violada_no_persiste_ni_notifica(self):
        svc, repo, notif, aud = servicio()
        with self.assertRaises(ReglaNegocioViolada):
            svc.crear_reserva(CLIENTE, 7, date(2026, 10, 1), date(2026, 10, 2))
        self.assertEqual((repo.reservas, notif.enviados), ({}, []))
        self.assertEqual(aud.eventos[0].detalle["motivo"], "fecha_pasada")

    def test_conflicto_de_fechas_se_propaga_y_audita(self):
        svc, _, notif, aud = servicio(repo=RepoFake(conflicto=True))
        with self.assertRaises(ConflictoDisponibilidad):
            svc.crear_reserva(CLIENTE, 7, date(2026, 11, 5), date(2026, 11, 6))
        self.assertEqual(aud.eventos[-1].detalle["motivo"], "herramienta_no_disponible")
        self.assertEqual(notif.enviados, [])

    def test_fallo_del_notificador_no_rompe_la_reserva(self):
        svc, repo, _, _ = servicio(notificador=NotificadorFake(falla=True))
        r = svc.crear_reserva(CLIENTE, 7, date(2026, 11, 5), date(2026, 11, 6))
        self.assertIn(r.id, repo.reservas)

    def test_cancelar_solo_por_el_cliente(self):
        svc, *_ = servicio()
        r = svc.crear_reserva(CLIENTE, 7, date(2026, 11, 5), date(2026, 11, 6))
        with self.assertRaises(Prohibido):
            svc.cancelar_reserva(Solicitante(99, "Otro", "o@test.com"), r.id)
        self.assertEqual(svc.cancelar_reserva(CLIENTE, r.id).estado, EstadoReserva.CANCELADA)

    def test_cancelar_inexistente_es_404(self):
        svc, *_ = servicio()
        with self.assertRaises(NoEncontrado):
            svc.cancelar_reserva(CLIENTE, 12345)


class FactoryYAdapterTests(SimpleTestCase):
    def test_factory_elige_segun_entorno(self):
        self.assertIsInstance(NotificadorFactory.crear("development"), NotificadorConsola)
        self.assertIsInstance(NotificadorFactory.crear("PRODUCTION"), NotificadorEmail)
        with self.assertRaises(ValueError):
            NotificadorFactory.crear("marte")

    def test_respaldo_local_cuando_el_microservicio_falla(self):
        class Caido(CalculadoraCosto):
            def calcular(self, *a):
                raise ServicioExternoError("timeout")

        calc = CalculadoraConRespaldo(Caido(), CalculadoraLocal())
        r = calc.calcular(date(2026, 11, 5), date(2026, 11, 7), [Decimal("10000.00")])
        self.assertEqual((r.dias, r.total), (3, Decimal("30000.00")))
