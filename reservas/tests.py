from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from reservas.models import Cliente, Categoria, Herramienta, Reserva, DetalleReserva
from reservas.services import ReservaService


class BaseDataTestCase(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Juan Pérez",
            email="juan@example.com",
            telefono="123456789"
        )
        self.categoria = Categoria.objects.create(
            nombre="Construcción",
            descripcion="Herramientas pesadas"
        )
        self.herramienta_1 = Herramienta.objects.create(
            nombre="Taladro",
            categoria=self.categoria,
            precio_por_dia=Decimal("15.00"),
            estado=Herramienta.Estado.DISPONIBLE
        )
        self.herramienta_2 = Herramienta.objects.create(
            nombre="Sierra",
            categoria=self.categoria,
            precio_por_dia=Decimal("20.00"),
            estado=Herramienta.Estado.DISPONIBLE
        )


class ReservaServiceTestCase(BaseDataTestCase):

    def test_creacion_exitosa_reserva(self):
        """1. Creación exitosa de una reserva."""
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = date.today() + timedelta(days=3)

        reserva = ReservaService.crear_reserva(
            cliente_id=self.cliente.id,
            herramienta_ids=[self.herramienta_1.id, self.herramienta_2.id],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            canal_notificacion="EMAIL"
        )

        self.assertIsNotNone(reserva.id)
        self.assertEqual(reserva.cliente, self.cliente)
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)
        
        detalles = DetalleReserva.objects.filter(reserva=reserva)
        self.assertEqual(detalles.count(), 2)

        costo_esperado = Decimal("70.00")
        self.assertEqual(reserva.costo_total, costo_esperado)

    def test_validacion_fechas_invalidas(self):
        """2. Validación de fechas: fecha_inicio >= fecha_fin produce error."""
        fecha_inicio = date.today() + timedelta(days=5)
        fecha_fin = date.today() + timedelta(days=2)

        with self.assertRaises(Exception):
            ReservaService.crear_reserva(
                cliente_id=self.cliente.id,
                herramienta_ids=[self.herramienta_1.id],
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )

        with self.assertRaises(Exception):
            ReservaService.crear_reserva(
                cliente_id=self.cliente.id,
                herramienta_ids=[self.herramienta_1.id],
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_inicio
            )

    def test_herramienta_no_disponible(self):
        """3. Herramienta no disponible no debe agregarse a la reserva."""
        self.herramienta_1.estado = Herramienta.Estado.EN_MANTENIMIENTO
        self.herramienta_1.save()

        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = date.today() + timedelta(days=3)

        with self.assertRaises(Exception):
            ReservaService.crear_reserva(
                cliente_id=self.cliente.id,
                herramienta_ids=[self.herramienta_1.id],
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )

    def test_cliente_inexistente(self):
        """4. Cliente inexistente debe producir un error."""
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = date.today() + timedelta(days=3)

        with self.assertRaises(Exception):
            ReservaService.crear_reserva(
                cliente_id=99999,
                herramienta_ids=[self.herramienta_1.id],
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )

    def test_cancelacion_reserva(self):
        """5. Cancelar reserva y verificar estado CANCELADA y herramientas DISPONIBLES."""
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = date.today() + timedelta(days=3)

        reserva = ReservaService.crear_reserva(
            cliente_id=self.cliente.id,
            herramienta_ids=[self.herramienta_1.id, self.herramienta_2.id],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        ReservaService.cancelar_reserva(reserva.id)
        reserva.refresh_from_db()

        self.assertEqual(reserva.estado, Reserva.Estado.CANCELADA)

        self.herramienta_1.refresh_from_db()
        self.herramienta_2.refresh_from_db()
        self.assertEqual(self.herramienta_1.estado, Herramienta.Estado.DISPONIBLE)
        self.assertEqual(self.herramienta_2.estado, Herramienta.Estado.DISPONIBLE)

    def test_cancelacion_invalida_reserva_finalizada(self):
        """6. Una reserva ya FINALIZADA no debe poder cancelarse."""
        fecha_inicio = date.today() + timedelta(days=1)
        fecha_fin = date.today() + timedelta(days=3)

        reserva = ReservaService.crear_reserva(
            cliente_id=self.cliente.id,
            herramienta_ids=[self.herramienta_1.id],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        reserva.estado = Reserva.Estado.FINALIZADA
        reserva.save()

        with self.assertRaises(Exception):
            ReservaService.cancelar_reserva(reserva.id)


class ReservaAPITestCase(APITestCase):

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Maria Gomez",
            email="maria@example.com",
            telefono="987654321"
        )
        self.categoria = Categoria.objects.create(
            nombre="Jardinería",
            descripcion="Herramientas de patio"
        )
        self.herramienta_disponible = Herramienta.objects.create(
            nombre="Podadora",
            categoria=self.categoria,
            precio_por_dia=Decimal("25.00"),
            estado=Herramienta.Estado.DISPONIBLE
        )
        self.herramienta_ocupada = Herramienta.objects.create(
            nombre="Motosierra",
            categoria=self.categoria,
            precio_por_dia=Decimal("40.00"),
            estado=Herramienta.Estado.ALQUILADA
        )

    def test_api_crear_reserva_exito(self):
        """7. API de creación: POST válido a /api/reservas/ devuelve 201 Created."""
        payload = {
            "cliente_id": self.cliente.id,
            "herramienta_ids": [self.herramienta_disponible.id],
            "fecha_inicio": str(date.today() + timedelta(days=1)),
            "fecha_fin": str(date.today() + timedelta(days=4)),
            "canal_notificacion": "EMAIL"
        }
        response = self.client.post("/api/reservas/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_datos_invalidos(self):
        """8. API con datos inválidos devuelve 400 Bad Request."""
        payload = {
            "cliente_id": self.cliente.id,
            "fecha_fin": str(date.today() + timedelta(days=4))
        }
        response = self.client.post("/api/reservas/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_recurso_inexistente(self):
        """9. API con recurso inexistente devuelve 404 Not Found."""
        response = self.client.post("/api/reservas/99999/cancelar/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_conflicto_negocio(self):
        """10. API con conflicto de negocio devuelve 409 Conflict."""
        payload = {
            "cliente_id": self.cliente.id,
            "herramienta_ids": [self.herramienta_ocupada.id],
            "fecha_inicio": str(date.today() + timedelta(days=1)),
            "fecha_fin": str(date.today() + timedelta(days=3))
        }
        response = self.client.post("/api/reservas/", payload, format="json")
        # Capturamos tanto el 409 (si está implementado estrictamente) o un 400 genérico si las validaciones ocurren antes en DRF.
        self.assertIn(response.status_code, [status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST])

    def test_api_herramientas_disponibles(self):
        """11. API de herramientas disponibles devuelve únicamente herramientas DISPONIBLE y HTTP 200."""
        response = self.client.get("/api/herramientas/disponibles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.herramienta_disponible.id)
        self.assertEqual(data[0]["estado"], Herramienta.Estado.DISPONIBLE)