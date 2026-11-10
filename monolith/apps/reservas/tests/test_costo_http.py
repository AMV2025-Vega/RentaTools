"""El Adapter HTTP traduce el contrato del microservicio Flask a nuestro puerto."""
from datetime import date
from decimal import Decimal
from unittest import mock

import requests
from django.test import SimpleTestCase

from apps.reservas.application.ports import ServicioExternoError
from apps.reservas.infrastructure.costo import CostoHttpAdapter


def _resp(status, json_data=None):
    r = mock.Mock(status_code=status, text="x")
    r.json.return_value = json_data
    return r


class CostoHttpAdapterTests(SimpleTestCase):
    def setUp(self):
        self.adapter = CostoHttpAdapter("http://costo:5000/api/v2/reservas/costo/", 1)

    @mock.patch("apps.reservas.infrastructure.costo.requests.post")
    def test_respuesta_ok(self, post):
        post.return_value = _resp(200, {"dias_totales": 3, "costo_total": 36000.0, "moneda": "COP"})
        r = self.adapter.calcular(date(2026, 11, 5), date(2026, 11, 7), [Decimal("12000.00")])
        self.assertEqual((r.dias, r.total), (3, Decimal("36000.00")))
        enviado = post.call_args.kwargs["json"]
        self.assertEqual(enviado["herramientas"], [{"precio_por_dia": "12000.00"}])

    @mock.patch("apps.reservas.infrastructure.costo.requests.post")
    def test_errores_se_traducen_a_servicio_externo_error(self, post):
        for efecto in (requests.Timeout("t"), _resp(500), _resp(400, {"message": "mal"}), _resp(200, {"x": 1})):
            post.side_effect = efecto if isinstance(efecto, Exception) else None
            if not isinstance(efecto, Exception):
                post.return_value = efecto
            with self.assertRaises(ServicioExternoError):
                self.adapter.calcular(date(2026, 11, 5), date(2026, 11, 7), [Decimal("1")])
