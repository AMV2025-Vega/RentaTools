from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.compartido.excepciones import ReglaNegocioViolada
from apps.inventario.domain.entities import HerramientaNueva
from apps.inventario.models import Categoria
from apps.usuarios.models import Usuario


class HerramientaNuevaTests(SimpleTestCase):
    def test_precio_debe_ser_positivo(self):
        with self.assertRaises(ReglaNegocioViolada):
            HerramientaNueva(1, 1, "Taladro", "", Decimal("0"))

    def test_nombre_obligatorio(self):
        with self.assertRaises(ReglaNegocioViolada):
            HerramientaNueva(1, 1, "  ", "", Decimal("10"))


class InventarioAPITests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user("dueno", "d@test.com", "Clave-Segura-123")
        self.cat = Categoria.objects.create(nombre="Cat-Test")
        self.api = APIClient()
        self.api.force_authenticate(self.u)

    def _publicar(self, **extra):
        datos = {"categoria_id": self.cat.id, "nombre": "Sierra", "precio_por_dia": "9000.00", **extra}
        return self.api.post("/api/herramientas/", datos, format="json")

    def test_publicar_201_y_listado_publico(self):
        self.assertEqual(self._publicar().status_code, 201)
        r = APIClient().get("/api/herramientas/")
        self.assertEqual((r.status_code, len(r.data)), (200, 1))

    def test_publicar_precio_invalido_400_y_categoria_inexistente_404(self):
        self.assertEqual(self._publicar(precio_por_dia="0").status_code, 400)
        self.assertEqual(self._publicar(categoria_id=99999).status_code, 404)

    def test_publicar_requiere_login(self):
        r = APIClient().post("/api/herramientas/", {}, format="json")
        self.assertIn(r.status_code, (401, 403))

    def test_solo_el_dueno_cambia_estado_y_mantenimiento_sale_del_catalogo(self):
        hid = self._publicar().data["id"]
        otro = Usuario.objects.create_user("otro", "o@test.com", "Clave-Segura-123")
        ajeno = APIClient()
        ajeno.force_authenticate(otro)
        self.assertEqual(ajeno.patch(f"/api/herramientas/{hid}/estado/", {"estado": "MANTENIMIENTO"}, format="json").status_code, 403)
        self.assertEqual(self.api.patch(f"/api/herramientas/{hid}/estado/", {"estado": "MANTENIMIENTO"}, format="json").status_code, 200)
        self.assertEqual(len(APIClient().get("/api/herramientas/").data), 0)
        self.assertEqual(len(self.api.get("/api/herramientas/?mias=1").data), 1)
        self.assertEqual(self.api.patch(f"/api/herramientas/{hid}/estado/", {"estado": "VOLANDO"}, format="json").status_code, 400)

    def test_categorias_iniciales_publicas(self):
        self.assertEqual(APIClient().get("/api/categorias/").status_code, 200)
