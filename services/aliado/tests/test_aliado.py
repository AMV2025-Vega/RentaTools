import pytest

from app import create_app

URL = "/api/v1/seguros/cotizar"


@pytest.fixture()
def client():
    return create_app().test_client()


def test_cotiza_con_categoria_conocida(client):
    r = client.post(URL, json={"valor_alquiler": "36000.00", "dias": 3, "categoria": "Construcción"})
    assert r.status_code == 200
    # max(2000, 36000*0.06=2160) + 500*3 = 3660
    assert r.get_json() == {
        "aseguradora": "AseguraTools S.A.S. (simulada)",
        "prima": "3660.00",
        "cobertura_maxima": "720000.00",
        "moneda": "COP",
        "tasa_aplicada": "0.06",
    }


def test_prima_minima_y_categoria_desconocida(client):
    r = client.post(URL, json={"valor_alquiler": 10000, "dias": 1, "categoria": "Otra"})
    assert r.get_json()["prima"] == "2500.00"  # max(2000, 500) + 500
    assert r.get_json()["tasa_aplicada"] == "0.05"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"dias": 2},
        {"valor_alquiler": 1000},
        {"valor_alquiler": "abc", "dias": 2},
        {"valor_alquiler": 0, "dias": 2},
        {"valor_alquiler": 1000, "dias": 0},
        {"valor_alquiler": 1000, "dias": 31},
        {"valor_alquiler": 1000, "dias": True},
        {"valor_alquiler": 1000, "dias": 2, "moneda": "USD"},
    ],
)
def test_entradas_invalidas_400(client, cuerpo):
    r = client.post(URL, json=cuerpo)
    assert r.status_code == 400
    assert r.get_json()["error"] == "solicitud_invalida"


def test_api_key(monkeypatch):
    monkeypatch.setenv("ALIADO_API_KEY", "secreta")
    c = create_app().test_client()
    cuerpo = {"valor_alquiler": 1000, "dias": 1}
    assert c.post(URL, json=cuerpo).status_code == 401
    assert c.post(URL, json=cuerpo, headers={"X-API-Key": "mala"}).status_code == 401
    assert c.post(URL, json=cuerpo, headers={"X-API-Key": "secreta"}).status_code == 200
    assert c.get("/health").status_code == 200  # el health no exige clave
