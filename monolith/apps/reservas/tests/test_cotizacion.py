"""Cotización: servicio con fakes, adapters con requests simulado y API de punta a punta."""
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import requests
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.compartido.excepciones import NoEncontrado, ReglaNegocioViolada
from apps.reservas.application.cotizacion import CotizacionService
from apps.reservas.application.ports import (
    CalculadoraCosto,
    CatalogoHerramientas,
    ConversorMoneda,
    ServicioExternoError,
    ServicioSeguros,
)
from apps.reservas.domain.costo import ResultadoCosto
from apps.reservas.domain.cotizacion import CotizacionSeguro, TasaCambio
from apps.reservas.domain.entities import HerramientaReservable
from apps.reservas.infrastructure.aliado_seguros import AliadoSegurosHttpAdapter
from apps.reservas.infrastructure.tasas_cambio import ConversorConCache, TasaCambioHttpAdapter

HOY = date(2026, 11, 1)


class CatalogoFake(CatalogoHerramientas):
    def obtener(self, herramienta_id):
        if herramienta_id == 7:
            return HerramientaReservable(7, 1, "Taladro", Decimal("12000.00"), True, "Construcción")
        if herramienta_id == 8:
            return HerramientaReservable(8, 1, "Sierra", Decimal("9000.00"), False, "Carpintería")
        return None


class CalcFake(CalculadoraCosto):
    def calcular(self, i, f, precios):
        return ResultadoCosto(dias=3, total=Decimal("36000.00"))


class SegurosFake(ServicioSeguros):
    def __init__(self, falla=False):
        self.falla, self.llamadas = falla, []

    def cotizar(self, valor, dias, categoria):
        self.llamadas.append((valor, dias, categoria))
        if self.falla:
            raise ServicioExternoError("aliado caído")
        return CotizacionSeguro("Aseg", Decimal("3660.00"), Decimal("720000.00"), "COP")


class FxFake(ConversorMoneda):
    def __init__(self, falla=False):
        self.falla = falla

    def obtener_tasa(self, de, a):
        if self.falla:
            raise ServicioExternoError("tasas caídas")
        return TasaCambio(de, a, Decimal("0.00025"), "Sat, 31 Oct 2026 00:00:01 +0000")


def servicio(seguros=None, fx=None):
    return CotizacionService(CatalogoFake(), CalcFake(), seguros or SegurosFake(), fx or FxFake(), lambda: HOY)


class CotizacionServiceTests(SimpleTestCase):
    def test_cotizacion_completa(self):
        seguros = SegurosFake()
        c = servicio(seguros).cotizar(7, date(2026, 11, 5), date(2026, 11, 7))
        self.assertEqual(c.costo_alquiler, Decimal("36000.00"))
        self.assertEqual(c.total, Decimal("39660.00"))
        self.assertEqual(c.total_usd, Decimal("9.92"))  # 39660 * 0.00025
        self.assertEqual(c.cop_por_usd, Decimal("4000.00"))
        self.assertEqual(c.avisos, ())
        self.assertEqual(seguros.llamadas, [(Decimal("36000.00"), 3, "Construcción")])

    def test_aliado_caido_degrada_sin_seguro(self):
        c = servicio(seguros=SegurosFake(falla=True)).cotizar(7, date(2026, 11, 5), date(2026, 11, 7))
        self.assertIsNone(c.seguro)
        self.assertEqual(c.total, Decimal("36000.00"))
        self.assertEqual(c.avisos, ("seguro_no_disponible",))

    def test_tasas_caidas_degrada_sin_usd(self):
        c = servicio(fx=FxFake(falla=True)).cotizar(7, date(2026, 11, 5), date(2026, 11, 7))
        self.assertIsNone(c.total_usd)
        self.assertEqual(c.avisos, ("conversion_no_disponible",))

    def test_ambos_caidos_sigue_cotizando_el_alquiler(self):
        c = servicio(SegurosFake(True), FxFake(True)).cotizar(7, date(2026, 11, 5), date(2026, 11, 7))
        self.assertEqual((c.total, c.avisos), (Decimal("36000.00"), ("seguro_no_disponible", "conversion_no_disponible")))

    def test_reglas(self):
        with self.assertRaises(NoEncontrado):
            servicio().cotizar(99, date(2026, 11, 5), date(2026, 11, 7))
        with self.assertRaises(ReglaNegocioViolada):
            servicio().cotizar(8, date(2026, 11, 5), date(2026, 11, 7))  # inactiva
        with self.assertRaises(ReglaNegocioViolada):
            servicio().cotizar(7, date(2026, 10, 1), date(2026, 10, 2))  # pasado


def _resp(status, data=None):
    r = mock.Mock(status_code=status, text="x")
    r.json.return_value = data
    return r


class AdaptersTests(SimpleTestCase):
    @mock.patch("apps.reservas.infrastructure.aliado_seguros.requests.post")
    def test_aliado_ok_envia_api_key_y_mapea(self, post):
        post.return_value = _resp(200, {"aseguradora": "A", "prima": "3660.00", "cobertura_maxima": "720000.00", "moneda": "COP"})
        s = AliadoSegurosHttpAdapter("http://aliado:5001/api/v1/", "k", 2).cotizar(Decimal("36000.00"), 3, "Construcción")
        self.assertEqual((s.prima, s.cobertura_maxima), (Decimal("3660.00"), Decimal("720000.00")))
        self.assertEqual(post.call_args.args[0], "http://aliado:5001/api/v1/seguros/cotizar")
        self.assertEqual(post.call_args.kwargs["headers"], {"X-API-Key": "k"})
        self.assertEqual(post.call_args.kwargs["json"]["valor_alquiler"], "36000.00")

    @mock.patch("apps.reservas.infrastructure.aliado_seguros.requests.post")
    def test_aliado_errores(self, post):
        for efecto in (requests.Timeout("t"), _resp(401), _resp(500), _resp(200, {"x": 1})):
            if isinstance(efecto, Exception):
                post.side_effect = efecto
            else:
                post.side_effect, post.return_value = None, efecto
            with self.assertRaises(ServicioExternoError):
                AliadoSegurosHttpAdapter("http://a/api/v1").cotizar(Decimal("1"), 1, "")

    @mock.patch("apps.reservas.infrastructure.tasas_cambio.requests.get")
    def test_tasas_ok(self, get):
        get.return_value = _resp(200, {"result": "success", "time_last_update_utc": "hoy", "rates": {"USD": 0.00026, "COP": 1}})
        t = TasaCambioHttpAdapter().obtener_tasa("COP", "USD")
        self.assertEqual((t.tasa, t.actualizada_en), (Decimal("0.00026"), "hoy"))
        self.assertIn("/latest/COP", get.call_args.args[0])

    @mock.patch("apps.reservas.infrastructure.tasas_cambio.requests.get")
    def test_tasas_errores(self, get):
        for efecto in (requests.Timeout("t"), _resp(429), _resp(200, {"result": "error", "error-type": "x"}), _resp(200, {"result": "success", "rates": {}})):
            if isinstance(efecto, Exception):
                get.side_effect = efecto
            else:
                get.side_effect, get.return_value = None, efecto
            with self.assertRaises(ServicioExternoError):
                TasaCambioHttpAdapter().obtener_tasa("COP", "USD")


class CacheDict:
    def __init__(self):
        self.d = {}

    def get(self, k):
        return self.d.get(k)

    def set(self, k, v, ttl=None):
        self.d[k] = v


class ConversorConCacheTests(SimpleTestCase):
    def test_usa_cache_fresca_y_respaldo_obsoleto(self):
        delegado = mock.Mock(spec=ConversorMoneda)
        delegado.obtener_tasa.return_value = TasaCambio("COP", "USD", Decimal("0.00025"), "t0")
        reloj = [1000.0]
        c = ConversorConCache(delegado, CacheDict(), ttl_fresco=100, reloj=lambda: reloj[0])

        c.obtener_tasa("COP", "USD")
        c.obtener_tasa("COP", "USD")
        self.assertEqual(delegado.obtener_tasa.call_count, 1)  # segunda vez: caché fresca

        reloj[0] += 500  # caché vencida y el tercero cae -> última tasa conocida
        delegado.obtener_tasa.side_effect = ServicioExternoError("429")
        self.assertEqual(c.obtener_tasa("COP", "USD").tasa, Decimal("0.00025"))

    def test_sin_cache_y_tercero_caido_propaga(self):
        delegado = mock.Mock(spec=ConversorMoneda)
        delegado.obtener_tasa.side_effect = ServicioExternoError("caído")
        with self.assertRaises(ServicioExternoError):
            ConversorConCache(delegado, CacheDict()).obtener_tasa("COP", "USD")


class CotizacionAPITests(TestCase):
    def setUp(self):
        from apps.inventario.models import Categoria, Herramienta
        from apps.usuarios.models import Usuario

        cache.clear()
        u = Usuario.objects.create_user("d", "d@test.com", "Clave-Segura-123")
        c = Categoria.objects.create(nombre="Construcción-T")
        self.h = Herramienta.objects.create(propietario=u, categoria=c, nombre="Taladro", precio_por_dia=Decimal("12000.00"))

    def _get(self, **q):
        base = {
            "herramienta_id": self.h.id,
            "fecha_inicio": (timezone.localdate() + timedelta(days=5)).isoformat(),
            "fecha_fin": (timezone.localdate() + timedelta(days=7)).isoformat(),
        }
        return APIClient().get("/api/cotizaciones/", {**base, **q})

    @mock.patch("apps.reservas.infrastructure.tasas_cambio.TasaCambioHttpAdapter.obtener_tasa")
    @mock.patch("apps.reservas.infrastructure.aliado_seguros.AliadoSegurosHttpAdapter.cotizar")
    @mock.patch("apps.reservas.infrastructure.costo.CostoHttpAdapter.calcular", side_effect=ServicioExternoError("x"))
    def test_200_publica_con_aliado_y_usd(self, _c, seguros, tasa):
        seguros.return_value = CotizacionSeguro("Aseg", Decimal("3660.00"), Decimal("720000.00"), "COP")
        tasa.return_value = TasaCambio("COP", "USD", Decimal("0.00025"), "hoy")
        r = self._get()
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["total"], "39660.00")
        self.assertEqual(r.data["total_usd"], "9.92")
        self.assertEqual(r.data["seguro"]["prima"], "3660.00")
        self.assertEqual(r.data["atribucion"]["url"], "https://www.exchangerate-api.com")

    @mock.patch("apps.reservas.infrastructure.tasas_cambio.TasaCambioHttpAdapter.obtener_tasa", side_effect=ServicioExternoError("x"))
    @mock.patch("apps.reservas.infrastructure.aliado_seguros.AliadoSegurosHttpAdapter.cotizar", side_effect=ServicioExternoError("x"))
    @mock.patch("apps.reservas.infrastructure.costo.CostoHttpAdapter.calcular", side_effect=ServicioExternoError("x"))
    def test_200_degradada_cuando_todo_externo_falla(self, *_):
        r = self._get()
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.data["total"], r.data["seguro"], r.data["total_usd"], r.data["atribucion"]), ("36000.00", None, None, None))
        self.assertEqual(r.data["avisos"], ["seguro_no_disponible", "conversion_no_disponible"])

    def test_400_y_404(self):
        self.assertEqual(self._get(fecha_inicio="x").status_code, 400)
        self.assertEqual(self._get(fecha_inicio=(timezone.localdate() - timedelta(days=3)).isoformat()).status_code, 400)
        self.assertEqual(self._get(herramienta_id=99999).status_code, 404)
