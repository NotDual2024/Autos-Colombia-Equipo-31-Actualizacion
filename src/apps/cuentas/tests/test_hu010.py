"""Criterios de aceptación de HU-010 (crear y desactivar operadores)."""
from django.urls import reverse

from apps.core.errores import ErrorNegocio
from apps.cuentas import services
from apps.cuentas.models import Usuario
from apps.demo.fabricas import asignar_horario_24h
from apps.demo.pruebas_base import CLAVE, PruebaConReloj


class HU010Operadores(PruebaConReloj):
    def test_crear_operador_y_puede_iniciar_sesion(self):
        nuevo = services.crear_operador(self.admin, "Pedro Rojas", "operador2", CLAVE)
        # Iteración 2 (RN-36): sin horario no puede iniciar sesión; con horario, sí.
        r = self.client.post(reverse("cuentas:login"), {"username": "operador2", "password": CLAVE})
        self.assertContains(r, "No tienes un horario asignado")
        asignar_horario_24h(nuevo)
        r = self.client.post(reverse("cuentas:login"), {"username": "operador2", "password": CLAVE})
        self.assertEqual(r.status_code, 302)

    def test_usuario_repetido(self):
        with self.assertRaisesMessage(ErrorNegocio, "El nombre de usuario ya existe"):
            services.crear_operador(self.admin, "Otro", "operador", CLAVE)

    def test_contrasena_debil(self):
        with self.assertRaises(ErrorNegocio):
            services.crear_operador(self.admin, "Pedro Rojas", "operador9", "123")

    def test_desactivar_conserva_la_cuenta_e_impide_ingresar(self):
        services.cambiar_estado(self.admin, self.operador.pk, False)
        self.assertTrue(Usuario.objects.filter(pk=self.operador.pk, is_active=False).exists())
        r = self.client.post(reverse("cuentas:login"), {"username": "operador", "password": CLAVE})
        self.assertContains(r, "Usuario o contraseña incorrectos")
        services.cambiar_estado(self.admin, self.operador.pk, True)
        self.assertTrue(Usuario.objects.get(pk=self.operador.pk).is_active)

    def test_operador_no_puede_gestionar(self):
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            services.crear_operador(self.operador, "X Y", "x", CLAVE)
        self.ingresar(self.operador)
        self.assertEqual(self.client.get(reverse("cuentas:operadores")).status_code, 403)

    def test_pantalla_administrador(self):
        self.ingresar(self.admin)
        r = self.client.post(reverse("cuentas:operadores"), {"nombre": "Pedro Rojas", "usuario": "operador3", "clave": CLAVE}, follow=True)
        self.assertContains(r, "Operador operador3 creado")
        r = self.client.post(reverse("cuentas:operadores"), {"nombre": "Pedro Rojas", "usuario": "operador3", "clave": CLAVE})
        self.assertContains(r, "El nombre de usuario ya existe")

    def test_menu_operadores_solo_para_administrador(self):
        self.ingresar(self.operador)
        self.assertNotContains(self.client.get(reverse("entradas_salidas:entrada")), reverse("cuentas:operadores"))
        self.ingresar(self.admin)
        self.assertContains(self.client.get(reverse("entradas_salidas:entrada")), reverse("cuentas:operadores"))
