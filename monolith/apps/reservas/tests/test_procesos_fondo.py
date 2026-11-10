"""Celery: notificaciones asíncronas, reintentos y reportes en segundo plano."""
import csv
import io
from datetime import date
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from apps.compartido.excepciones import Prohibido, ServicioNoDisponible
from apps.compartido.puertos import Solicitante
from apps.reservas.application.reportes import ColaReportes, EstadoTarea, ReporteService
from apps.reservas.domain.entities import EstadoReserva, Reserva
from apps.reservas.infrastructure.mensajes import renderizar
from apps.reservas.infrastructure.notificadores import NotificadorAsincrono
from apps.reservas.infrastructure.tareas import enviar_notificacion, generar_reporte_reservas

CLIENTE = Solicitante(2, "Ana", "ana@test.com")


class MensajesTests(SimpleTestCase):
    def test_renderiza_con_contexto(self):
        asunto, cuerpo = renderizar("reserva_creada", {"nombre": "Ana", "id": "5", "herramienta": "Taladro", "inicio": "a", "fin": "b", "total": "1", "moneda": "COP"})
        self.assertEqual(asunto, "Reserva registrada")
        self.assertIn("Ana", cuerpo)
        self.assertIn("#5", cuerpo)


class NotificadorAsincronoTests(SimpleTestCase):
    @mock.patch("apps.reservas.infrastructure.tareas.enviar_notificacion.delay")
    def test_encola_en_lugar_de_enviar(self, delay):
        NotificadorAsincrono().enviar("a@b.c", "reserva_cancelada", {"nombre": "A", "id": "1"}, "es")
        delay.assert_called_once_with("a@b.c", "reserva_cancelada", {"nombre": "A", "id": "1"}, "es")

    @override_settings(ENV_TYPE="development", CELERY_TASK_ALWAYS_EAGER=True)
    def test_la_tarea_envia_con_la_factory(self):
        with self.assertLogs("apps.reservas.infrastructure.notificadores", "INFO") as logs:
            enviar_notificacion.apply(args=["a@b.c", "reserva_cancelada", {"nombre": "Ana", "id": "9"}, "es"]).get()
        self.assertIn("Reserva cancelada", logs.output[0])

    @override_settings(ENV_TYPE="production")
    @mock.patch("apps.reservas.infrastructure.notificadores.send_mail")
    def test_la_tarea_reintenta_si_el_proveedor_falla(self, send_mail):
        send_mail.side_effect = [ConnectionError("smtp"), 1]
        with mock.patch.object(enviar_notificacion, "retry", side_effect=Exception("reintento")) as retry:
            res = enviar_notificacion.apply(args=["a@b.c", "reserva_cancelada", {"nombre": "A", "id": "1"}, "es"])
        self.assertTrue(res.failed() or retry.called)


class ColaFake(ColaReportes):
    def __init__(self, estado=None, falla=False):
        self.estado, self.falla = estado, falla

    def solicitar_reporte_reservas(self, cliente_id):
        if self.falla:
            raise ServicioNoDisponible("sin broker")
        return "11111111-1111-1111-1111-111111111111"

    def consultar(self, tarea_id):
        return self.estado or EstadoTarea(tarea_id, "PENDIENTE")


class RepoFake:
    def listar_por_cliente(self, cliente_id):
        return [Reserva(1, cliente_id, 7, date(2026, 11, 5), date(2026, 11, 6), 2, Decimal("24000.00"), "COP", EstadoReserva.PENDIENTE_PAGO)]


class ReporteServiceTests(SimpleTestCase):
    def test_csv(self):
        r = ReporteService(RepoFake(), ColaFake()).generar_csv(2)
        filas = list(csv.reader(io.StringIO(r["contenido"])))
        self.assertEqual((r["filas"], filas[0][0], filas[1][:2]), (1, "id", ["1", "7"]))
        self.assertEqual(r["cliente_id"], 2)

    def test_no_entrega_el_reporte_de_otro_usuario(self):
        otro = EstadoTarea("t", "LISTO", {"cliente_id": 99, "contenido": "x"})
        with self.assertRaises(Prohibido):
            ReporteService(RepoFake(), ColaFake(otro)).consultar(CLIENTE, "t")
        propio = EstadoTarea("t", "LISTO", {"cliente_id": 2, "contenido": "x"})
        self.assertEqual(ReporteService(RepoFake(), ColaFake(propio)).consultar(CLIENTE, "t").estado, "LISTO")


class ReportesAPITests(TestCase):
    def setUp(self):
        from apps.usuarios.models import Usuario

        self.u = Usuario.objects.create_user("ana", "ana@test.com", "Clave-Segura-123")
        self.api = APIClient()
        self.api.force_authenticate(self.u)

    def test_tarea_genera_csv_del_usuario(self):
        r = generar_reporte_reservas.apply(args=[self.u.id]).get()
        self.assertEqual((r["cliente_id"], r["filas"]), (self.u.id, 0))

    @mock.patch("apps.reservas.composition.CeleryColaReportes", return_value=ColaFake())
    def test_202_y_polling(self, _cola):
        r = self.api.post("/api/reportes/reservas/")
        self.assertEqual((r.status_code, r.data["estado"]), (202, "PENDIENTE"))
        g = self.api.get(f"/api/reportes/{r.data['tarea_id']}/")
        self.assertEqual((g.status_code, g.data["estado"]), (200, "PENDIENTE"))

    @mock.patch("apps.reservas.composition.CeleryColaReportes", return_value=ColaFake(falla=True))
    def test_503_si_no_hay_broker(self, _cola):
        self.assertEqual(self.api.post("/api/reportes/reservas/").status_code, 503)

    def test_requiere_login(self):
        self.assertIn(APIClient().post("/api/reportes/reservas/").status_code, (401, 403))
