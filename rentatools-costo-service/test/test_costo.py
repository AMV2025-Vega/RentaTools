import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_request_valido(client):
    payload = {
        "fecha_inicio": "2026-10-01",
        "fecha_fin": "2026-10-05",
        "herramientas": [
            {"id": 1, "precio_por_dia": 25.50},
            {"id": 2, "precio_por_dia": 10.00},
        ],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["dias_totales"] == 5
    assert data["costo_total"] == 177.50
    assert data["moneda"] == "COP"


def test_json_ausente(client):
    response = client.post(
        "/api/v2/reservas/costo/",
        data="no json data",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert data["code"] == 400


def test_campo_requerido_ausente(client):
    payload = {
        "fecha_inicio": "2026-10-01",
        "herramientas": [{"id": 1, "precio_por_dia": 25.50}],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 400
    assert "fecha_fin" in response.get_json()["message"]


def test_herramientas_vacia(client):
    payload = {
        "fecha_inicio": "2026-10-01",
        "fecha_fin": "2026-10-05",
        "herramientas": [],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 400
    assert "vacía" in response.get_json()["message"]


def test_precio_negativo(client):
    payload = {
        "fecha_inicio": "2026-10-01",
        "fecha_fin": "2026-10-05",
        "herramientas": [{"id": 1, "precio_por_dia": -10.00}],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 400
    assert "negativo" in response.get_json()["message"]


def test_precio_invalido(client):
    payload = {
        "fecha_inicio": "2026-10-01",
        "fecha_fin": "2026-10-05",
        "herramientas": [{"id": 1, "precio_por_dia": "abc"}],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 400
    assert "número válido" in response.get_json()["message"]


def test_fecha_invalida(client):
    payload = {
        "fecha_inicio": "01-10-2026",
        "fecha_fin": "2026-10-05",
        "herramientas": [{"id": 1, "precio_por_dia": 10.00}],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 400
    assert "inválido" in response.get_json()["message"]


def test_fechas_inconsistentes(client):
    payload = {
        "fecha_inicio": "2026-10-05",
        "fecha_fin": "2026-10-01",
        "herramientas": [{"id": 1, "precio_por_dia": 10.00}],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 400
    assert "anterior" in response.get_json()["message"]


def test_error_interno_500(client, monkeypatch):
    def mock_calcular(*args, **kwargs):
        raise RuntimeError("Error inesperado en motor de cálculo")

    monkeypatch.setattr("app.routes.calcular_costo_reserva", mock_calcular)

    payload = {
        "fecha_inicio": "2026-10-01",
        "fecha_fin": "2026-10-05",
        "herramientas": [{"id": 1, "precio_por_dia": 10.00}],
    }
    response = client.post("/api/v2/reservas/costo/", json=payload)
    assert response.status_code == 500
    data = response.get_json()
    assert data["status"] == "error"
    assert data["code"] == 500
    assert (
        data["message"] == "Ocurrió un error inesperado al procesar el cálculo."
    )