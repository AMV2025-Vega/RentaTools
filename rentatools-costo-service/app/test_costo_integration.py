from unittest.mock import Mock, patch
from django.test import TestCase
import requests
from reservas.services import (
    CostoServiceError,
    CostoServiceValidationError,
    solicitar_calculo_costo,
)


class CostoServiceIntegrationTest(TestCase):

    @patch("reservas.services.requests.post")
    def test_solicitar_calculo_exitoso(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dias_totales": 5,
            "costo_total": 177.50,
            "moneda": "COP",
        }
        mock_post.return_value = mock_response

        res = solicitar_calculo_costo(
            "2026-10-01",
            "2026-10-05",
            [{"id": 1, "precio_por_dia": 25.50}],
        )
        self.assertEqual(res["dias_totales"], 5)
        self.assertEqual(res["costo_total"], 177.50)

    @patch("reservas.services.requests.post")
    def test_solicitar_calculo_error_400(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "status": "error",
            "code": 400,
            "message": "Fechas inválidas",
        }
        mock_post.return_value = mock_response

        with self.assertRaises(CostoServiceValidationError):
            solicitar_calculo_costo(
                "2026-10-05",
                "2026-10-01",
                [{"id": 1, "precio_por_dia": 25.50}],
            )

    @patch("reservas.services.requests.post")
    def test_solicitar_calculo_error_conexion(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException(
            "Connection refused"
        )

        with self.assertRaises(CostoServiceError):
            solicitar_calculo_costo(
                "2026-10-01",
                "2026-10-05",
                [{"id": 1, "precio_por_dia": 25.50}],
            )