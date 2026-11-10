from django.test import TestCase
from rest_framework.test import APIClient


class AuthAPITests(TestCase):
    DATOS = {"username": "ana", "email": "ana@test.com", "password": "Clave-Segura-123"}

    def test_registro_login_perfil_logout(self):
        api = APIClient()
        self.assertEqual(api.post("/api/auth/registro/", self.DATOS, format="json").status_code, 201)
        self.assertEqual(api.post("/api/auth/login/", {"username": "ana", "password": "Clave-Segura-123"}, format="json").status_code, 200)
        self.assertEqual(api.get("/api/auth/yo/").data["email"], "ana@test.com")
        self.assertEqual(api.post("/api/auth/logout/").status_code, 204)
        self.assertIn(api.get("/api/auth/yo/").status_code, (401, 403))

    def test_duplicados_409_y_password_debil_400(self):
        api = APIClient()
        api.post("/api/auth/registro/", self.DATOS, format="json")
        self.assertEqual(api.post("/api/auth/registro/", self.DATOS, format="json").status_code, 409)
        self.assertEqual(api.post("/api/auth/registro/", {**self.DATOS, "username": "x", "email": "x@test.com", "password": "123"}, format="json").status_code, 400)

    def test_login_invalido_400(self):
        r = APIClient().post("/api/auth/login/", {"username": "no", "password": "no"}, format="json")
        self.assertEqual(r.status_code, 400)
