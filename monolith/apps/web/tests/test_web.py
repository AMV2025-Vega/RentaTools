import subprocess, sys
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

RAIZ = Path(__file__).resolve().parents[3]


class PaginasTests(TestCase):
    def test_paginas_publicas_responden_200(self):
        for url in ("/", "/ingresar/", "/registro/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_paginas_privadas_exigen_sesion(self):
        for url in ("/mis-reservas/", "/publicar/"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302)
            self.assertTrue(r["Location"].startswith("/ingresar/?next="))

    def test_detalle_y_estaticos(self):
        self.assertEqual(self.client.get("/herramientas/1/").status_code, 200)
        self.assertContains(self.client.get("/"), "js/catalogo.js")

    def test_redireccion_siguiente_no_permite_sitios_externos(self):
        r = self.client.get("/ingresar/?next=https://malo.example/")
        self.assertContains(r, 'data-siguiente="/"')  # el destino externo se descarta

    def test_paginas_privadas_con_sesion(self):
        get_user_model().objects.create_user("ana", "ana@test.com", "Clave-Segura-123")
        self.client.login(username="ana", password="Clave-Segura-123")
        for url in ("/mis-reservas/", "/publicar/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class IdiomaTests(TestCase):
    def test_por_defecto_es_espanol(self):
        r = self.client.get("/")
        self.assertContains(r, 'lang="es"'); self.assertContains(r, "Mis reservas".replace("Mis reservas", "Catálogo"))

    def test_cambio_de_idioma_a_ingles(self):
        self.client.post("/i18n/setlang/", {"language": "en", "next": "/"})
        r = self.client.get("/")
        self.assertContains(r, 'lang="en"'); self.assertContains(r, "Skip to content"); self.assertNotContains(r, "Saltar al contenido")

    def test_cadenas_js_llegan_traducidas(self):
        r = self.client.get("/", HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(r, "No tools match your search.")

    def test_errores_de_api_se_traducen(self):
        en = APIClient().post("/api/auth/login/", {"username": "x", "password": "y"}, format="json", HTTP_ACCEPT_LANGUAGE="en")
        es = APIClient().post("/api/auth/login/", {"username": "x", "password": "y"}, format="json", HTTP_ACCEPT_LANGUAGE="es")
        self.assertEqual(en.data["error"], "Incorrect username or password.")
        self.assertEqual(es.data["error"], "Usuario o contraseña incorrectos.")

    def test_notificacion_se_renderiza_en_el_idioma_del_usuario(self):
        from apps.reservas.infrastructure.mensajes import renderizar
        ctx = {"nombre": "Ana", "id": 7}
        self.assertEqual(renderizar("reserva_cancelada", ctx, "en")[0], "Booking cancelled")
        self.assertEqual(renderizar("reserva_cancelada", ctx, "es")[0], "Reserva cancelada")
        self.assertIn("was cancelled", renderizar("reserva_cancelada", ctx, "en")[1])

    def test_catalogo_ingles_esta_completo(self):
        """scripts/i18n.py falla si algún texto del código o las plantillas no tiene traducción."""
        r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "i18n.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
