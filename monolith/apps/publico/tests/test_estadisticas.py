from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.inventario.models import Categoria, Herramienta
from apps.reservas.models import Reserva
from apps.usuarios.models import Usuario


class EstadisticasPublicasTests(TestCase):
    def test_vacio_y_con_datos_sin_autenticacion(self):
        api = APIClient()  # sin login: es un servicio público
        r = api.get("/api/publico/estadisticas/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["resumen"]["herramientas_activas"], 0)
        self.assertIsNone(r.data["resumen"]["precio_promedio_dia"])
        self.assertEqual(set(r.data["resumen"]["reservas_por_estado"]), {"PENDIENTE_PAGO", "CONFIRMADA", "CANCELADA", "FINALIZADA"})

        d = Usuario.objects.create_user("d", "d@test.com", "Clave-Segura-123")
        c = Usuario.objects.create_user("c", "c@test.com", "Clave-Segura-123")
        cat = Categoria.objects.create(nombre="Zeta")
        h1 = Herramienta.objects.create(propietario=d, categoria=cat, nombre="A", precio_por_dia=Decimal("10000.00"))
        Herramienta.objects.create(propietario=d, categoria=cat, nombre="B", precio_por_dia=Decimal("20000.00"))
        Herramienta.objects.create(propietario=d, categoria=cat, nombre="C", precio_por_dia=Decimal("99999.00"), estado="MANTENIMIENTO")
        Reserva.objects.create(cliente=c, herramienta=h1, fecha_inicio="2026-12-01", fecha_fin="2026-12-02", dias=2, costo_total=Decimal("20000.00"))

        r = api.get("/api/publico/estadisticas/")
        res = r.data["resumen"]
        self.assertEqual((res["herramientas_activas"], res["precio_promedio_dia"]), (2, "15000.00"))
        self.assertEqual(res["por_categoria"][-1], {"categoria": "Zeta", "herramientas": 2})
        self.assertEqual((res["reservas_total"], res["reservas_por_estado"]["PENDIENTE_PAGO"]), (1, 1))
        # No expone datos personales
        self.assertNotIn("d@test.com", str(r.content))
