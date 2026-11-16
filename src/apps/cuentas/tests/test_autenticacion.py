from django.test import TestCase
from django.urls import reverse

from apps.cuentas.models import Rol, Usuario

CLAVE = "ClaveSegura2026"


class AutenticacionTests(TestCase):
    def setUp(self):
        self.operador = Usuario.objects.create_user("operador1", password=CLAVE, first_name="María", last_name="Pérez", rol=Rol.OPERADOR)

    def test_contrasena_se_guarda_con_argon2(self):
        # RNF-001, DEC-012
        self.assertTrue(self.operador.password.startswith("argon2$argon2id$"))

    def test_inicio_de_sesion_valido(self):
        r = self.client.post(reverse("cuentas:login"), {"username": "operador1", "password": CLAVE})
        self.assertEqual(r.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_credenciales_invalidas_muestran_mensaje_generico(self):
        r = self.client.post(reverse("cuentas:login"), {"username": "operador1", "password": "mala"})
        self.assertContains(r, "Usuario o contraseña incorrectos")

    def test_usuario_inactivo_no_puede_iniciar_sesion(self):
        # RF-106
        self.operador.is_active = False
        self.operador.save()
        r = self.client.post(reverse("cuentas:login"), {"username": "operador1", "password": CLAVE})
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(r, "Usuario o contraseña incorrectos")

    def test_pantallas_exigen_sesion(self):
        r = self.client.get(reverse("entradas_salidas:entrada"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("cuentas:login"), r["Location"])

    def test_no_existe_panel_admin(self):
        # DEC-011: el panel /admin no se habilita
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_rol_es_administrador(self):
        admin = Usuario.objects.create_user("admin", password=CLAVE, rol=Rol.ADMINISTRADOR)
        self.assertTrue(admin.es_administrador())
        self.assertFalse(self.operador.es_administrador())
