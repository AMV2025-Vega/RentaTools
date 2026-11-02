"""Pruebas de integración de la API con PostgreSQL real (incluye el ExclusionConstraint)."""
import threading
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.auditoria.models import RegistroAuditoria
from apps.inventario.models import Categoria, Herramienta
from apps.reservas.application.ports import ServicioExternoError
from apps.reservas.models import Reserva
from apps.usuarios.models import Usuario


def fecha(dias):
    return (timezone.localdate() + timedelta(days=dias)).isoformat()


def crear_escenario():
    dueno = Usuario.objects.create_user("dueno", "dueno@test.com", "Clave-Segura-123")
    cliente = Usuario.objects.create_user("cliente", "cliente@test.com", "Clave-Segura-123")
    otro = Usuario.objects.create_user("otro", "otro@test.com", "Clave-Segura-123")
    categoria = Categoria.objects.create(nombre="Test")
    herramienta = Herramienta.objects.create(
        propietario=dueno, categoria=categoria, nombre="Taladro", precio_por_dia=Decimal("12000.00")
    )
    return dueno, cliente, otro, herramienta


@mock.patch(
    "apps.reservas.infrastructure.costo.CostoHttpAdapter.calcular",
    side_effect=ServicioExternoError("sin microservicio en tests"),
)
class ReservasAPITests(TestCase):
    def setUp(self):
        self.dueno, self.cliente, self.otro, self.herramienta = crear_escenario()
        self.api = APIClient()
        self.api.force_authenticate(self.cliente)

    def _post(self, inicio, fin, herramienta_id=None, client=None):
        return (client or self.api).post(
            "/api/reservas/",
            {"herramienta_id": herramienta_id or self.herramienta.id, "fecha_inicio": fecha(inicio), "fecha_fin": fecha(fin)},
            format="json",
        )

    def test_201_crea_reserva_con_costo_y_auditoria(self, _m):
        r = self._post(5, 7)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["dias"], 3)
        self.assertEqual(r.data["costo_total"], "36000.00")
        self.assertEqual(r.data["estado"], "PENDIENTE_PAGO")
        self.assertTrue(RegistroAuditoria.objects.filter(accion="RESERVA_CREADA", actor_id=self.cliente.id).exists())

    def test_400_formato_de_fecha_invalido(self, _m):
        r = self.api.post("/api/reservas/", {"herramienta_id": 1, "fecha_inicio": "hoy", "fecha_fin": "mañana"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_400_regla_de_negocio_fecha_pasada(self, _m):
        r = self._post(-3, -1)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["codigo"], "fecha_pasada")
        self.assertTrue(RegistroAuditoria.objects.filter(accion="RESERVA_RECHAZADA", resultado="RECHAZADO").exists())

    def test_404_herramienta_inexistente(self, _m):
        self.assertEqual(self._post(5, 6, herramienta_id=99999).status_code, 404)

    def test_409_fechas_solapadas(self, _m):
        self.assertEqual(self._post(5, 8).status_code, 201)
        otro = APIClient()
        otro.force_authenticate(self.otro)
        r = self._post(7, 10, client=otro)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["codigo"], "herramienta_no_disponible")
        self.assertEqual(Reserva.objects.count(), 1)

    def test_fechas_contiguas_no_chocan_y_canceladas_liberan(self, _m):
        self.assertEqual(self._post(5, 8).status_code, 201)
        self.assertEqual(self._post(9, 10).status_code, 201)  # día siguiente: ok
        rid = Reserva.objects.order_by("id").first().id
        self.assertEqual(self.api.post(f"/api/reservas/{rid}/cancelar/").status_code, 200)
        self.assertEqual(self._post(5, 8).status_code, 201)  # liberadas por la cancelación

    def test_403_sin_autenticar(self, _m):
        self.assertIn(self._post(5, 6, client=APIClient()).status_code, (401, 403))

    def test_cancelar_403_otro_usuario_404_inexistente_409_doble(self, _m):
        rid = self._post(5, 6).data["id"]
        otro = APIClient()
        otro.force_authenticate(self.otro)
        self.assertEqual(otro.post(f"/api/reservas/{rid}/cancelar/").status_code, 403)
        self.assertEqual(self.api.post("/api/reservas/99999/cancelar/").status_code, 404)
        self.assertEqual(self.api.post(f"/api/reservas/{rid}/cancelar/").status_code, 200)
        self.assertEqual(self.api.post(f"/api/reservas/{rid}/cancelar/").status_code, 409)

    def test_no_puedes_reservar_tu_propia_herramienta(self, _m):
        propio = APIClient()
        propio.force_authenticate(self.dueno)
        self.assertEqual(self._post(5, 6, client=propio).status_code, 400)

    def test_ocupacion_publica_y_mis_reservas(self, _m):
        self._post(5, 6)
        r = APIClient().get(f"/api/herramientas/{self.herramienta.id}/ocupacion/")
        self.assertEqual((r.status_code, len(r.data)), (200, 1))
        self.assertEqual(len(self.api.get("/api/reservas/").data), 1)


@mock.patch("apps.reservas.infrastructure.costo.CostoHttpAdapter.calcular", side_effect=ServicioExternoError("x"))
class ConcurrenciaTests(TransactionTestCase):
    """Dos peticiones simultáneas por las mismas fechas: la BD deja pasar solo una."""

    def test_solo_una_de_dos_reservas_simultaneas_gana(self, _m):
        _, cliente, otro, herramienta = crear_escenario()
        barrera, resultados = threading.Barrier(2), []

        def reservar(usuario):
            try:
                api = APIClient()
                api.force_authenticate(usuario)
                barrera.wait(timeout=5)
                r = api.post(
                    "/api/reservas/",
                    {"herramienta_id": herramienta.id, "fecha_inicio": fecha(10), "fecha_fin": fecha(12)},
                    format="json",
                )
                resultados.append(r.status_code)
            finally:
                connection.close()

        hilos = [threading.Thread(target=reservar, args=(u,)) for u in (cliente, otro)]
        [h.start() for h in hilos]
        [h.join(timeout=20) for h in hilos]
        self.assertEqual(sorted(resultados), [201, 409])
        self.assertEqual(Reserva.objects.count(), 1)
