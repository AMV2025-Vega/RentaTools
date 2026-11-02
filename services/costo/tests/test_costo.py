import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def payload(**extra):
    base = {"fecha_inicio": "2026-11-05", "fecha_fin": "2026-11-07", "herramientas": [{"precio_por_dia": "12000.00"}]}
    return {**base, **extra}


def test_calcula_costo(client):
    r = client.post("/api/v2/reservas/costo/", json=payload())
    assert r.status_code == 200
    assert r.get_json() == {"dias_totales": 3, "costo_total": 36000.0, "moneda": "COP"}


def test_suma_varias_herramientas(client):
    r = client.post("/api/v2/reservas/costo/", json=payload(herramientas=[{"precio_por_dia": 10000}, {"precio_por_dia": "5000.50"}]))
    assert r.get_json()["costo_total"] == 45001.5


@pytest.mark.parametrize(
    "cuerpo",
    [
        payload(fecha_fin="2026-11-01"),
        payload(fecha_inicio="05/11/2026"),
        payload(herramientas=[]),
        payload(herramientas=[{"precio_por_dia": -1}]),
        payload(herramientas=[{}]),
        {},
    ],
)
def test_entradas_invalidas_devuelven_400_json(client, cuerpo):
    r = client.post("/api/v2/reservas/costo/", json=cuerpo)
    assert r.status_code == 400
    assert "message" in r.get_json()


def test_sin_json_es_400_y_health_ok(client):
    assert client.post("/api/v2/reservas/costo/", data="x").status_code == 400
    assert client.get("/health").get_json()["estado"] == "ok"
