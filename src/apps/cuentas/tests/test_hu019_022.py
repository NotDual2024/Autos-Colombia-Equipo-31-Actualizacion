"""Criterios de aceptación de HU-019 a HU-023 (operadores, horarios, turno, autorizaciones, bitácora)."""
from datetime import time

from django.urls import reverse

from apps.bitacora.models import RegistroOperacion
from apps.core.errores import ErrorNegocio
from apps.cuentas import services, turnos
from apps.cuentas.control_turno import CLAVE_FIN
from apps.cuentas.models import HorarioOperador
from apps.demo import fabricas as f
from apps.demo.pruebas_base import CLAVE, PruebaConReloj, fh

NUEVA = "NuevaClave2026"


class HU019EditarOperador(PruebaConReloj):
    def test_editar_nombre_y_bitacora(self):
        services.editar_nombre(self.admin, self.operador.pk, "María José Rodríguez")
        self.operador.refresh_from_db()
        self.assertEqual(self.operador.nombre_completo(), "María José Rodríguez")
        self.assertTrue(RegistroOperacion.objects.filter(accion="MODIFICAR", entidad="OPERADOR").exists())

    def test_restablecer_clave_sin_guardarla_en_bitacora(self):
        services.restablecer_clave(self.admin, self.operador.pk, NUEVA, NUEVA)
        self.assertTrue(self.client.login(username="operador", password=NUEVA))
        self.assertFalse(self.client.login(username="operador", password=CLAVE))
        op = RegistroOperacion.objects.get(accion="RESTABLECER_CLAVE")
        self.assertIsNone(op.detalle)
        self.assertNotIn(NUEVA, op.descripcion)

    def test_clave_debil_o_confirmacion_distinta(self):
        with self.assertRaises(ErrorNegocio):
            services.restablecer_clave(self.admin, self.operador.pk, "123", "123")
        with self.assertRaisesMessage(ErrorNegocio, "confirmación"):
            services.restablecer_clave(self.admin, self.operador.pk, NUEVA, "otra")


class HU020Horarios(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.op2 = f.crear_usuario("operador2", CLAVE, "Julián Torres")

    def test_franjas_diurna_nocturna_y_varias(self):
        turnos.asignar_franja(self.admin, self.op2.pk, 1, time(6), time(14))
        turnos.asignar_franja(self.admin, self.op2.pk, 5, time(22), time(6))
        turnos.asignar_franja(self.admin, self.op2.pk, 2, time(6), time(10))
        turnos.asignar_franja(self.admin, self.op2.pk, 2, time(16), time(20))
        self.assertEqual(self.op2.horarios.count(), 4)
        self.assertEqual(RegistroOperacion.objects.filter(accion="ASIGNAR_HORARIO").count(), 4)

    def test_rn37_franjas_cruzadas(self):
        turnos.asignar_franja(self.admin, self.op2.pk, 2, time(6), time(12))
        with self.assertRaisesMessage(ErrorNegocio, "La franja se cruza con otra del mismo día"):
            turnos.asignar_franja(self.admin, self.op2.pk, 2, time(10), time(14))

    def test_quitar_franja(self):
        franja = turnos.asignar_franja(self.admin, self.op2.pk, 1, time(6), time(14))
        turnos.quitar_franja(self.admin, franja.pk)
        self.assertFalse(HorarioOperador.objects.filter(pk=franja.pk).exists())
        self.assertTrue(RegistroOperacion.objects.filter(accion="QUITAR_HORARIO").exists())

    def test_solo_administrador(self):
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            turnos.asignar_franja(self.operador, self.op2.pk, 1, time(6), time(14))


class HU021Turno(PruebaConReloj):
    """Domingo 15/11/2026. operador2 trabaja el domingo (7) de 06:00 a 14:00."""

    def setUp(self):
        super().setUp()
        self.op2 = f.crear_usuario("operador2", CLAVE, "Julián Torres")
        HorarioOperador.objects.create(operador=self.op2, dia_semana=7, hora_inicio=time(6), hora_fin=time(14))

    def login(self, usuario="operador2"):
        return self.client.post(reverse("cuentas:login"), {"username": usuario, "password": CLAVE})

    def test_ingreso_dentro_del_turno_y_encabezado(self):
        self.AHORA = fh("2026-11-15 08:00")
        self.assertEqual(self.login().status_code, 302)
        r = self.client.get(reverse("entradas_salidas:entrada"))
        self.assertContains(r, "Operador · Turno 06:00 – 14:00")
        self.assertLessEqual(self.client.session.get_expiry_age(), 12 * 3600)  # sesión de 12 horas como máximo

    def test_ingreso_fuera_del_turno(self):
        self.AHORA = fh("2026-11-15 15:00")
        self.assertContains(self.login(), "Estás fuera de tu turno. Solicita autorización al administrador")

    def test_operador_sin_horario(self):
        f.crear_usuario("operador3", CLAVE, "Sin Horario")
        self.assertContains(self.login("operador3"), "No tienes un horario asignado")

    def test_turno_nocturno(self):
        HorarioOperador.objects.create(operador=self.op2, dia_semana=7, hora_inicio=time(22), hora_fin=time(6))
        self.AHORA = fh("2026-11-16 03:00")  # lunes de madrugada, dentro de la franja del domingo
        self.assertEqual(self.login().status_code, 302)

    def test_administrador_sin_restriccion(self):
        self.AHORA = fh("2026-11-15 03:00")
        self.assertEqual(self.login("admin").status_code, 302)

    def test_fin_de_turno_gracia_de_5_minutos(self):
        self.AHORA = fh("2026-11-15 13:50")
        self.login()
        self.client.get(reverse("entradas_salidas:entrada"))
        self.assertEqual(self.client.session[CLAVE_FIN], fh("2026-11-15 14:00").isoformat())
        self.AHORA = fh("2026-11-15 14:03")
        r = self.client.get(reverse("entradas_salidas:entrada"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="aviso-turno" role="alert" >')  # aviso visible durante la gracia
        self.AHORA = fh("2026-11-15 14:06")
        r = self.client.get(reverse("entradas_salidas:entrada"))
        self.assertRedirects(r, reverse("cuentas:login") + "?motivo=turno", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_fin_de_turno_con_registro_en_curso(self):
        """RN-35a: el guardado se completa aunque haya pasado la gracia y luego se cierra la sesión."""
        from apps.usuarios_celdas.models import Propietario

        self.AHORA = fh("2026-11-15 13:55")
        self.login()
        self.client.get(reverse("usuarios_celdas:propietario_nuevo"))
        self.AHORA = fh("2026-11-15 14:20")
        r = self.client.post(reverse("usuarios_celdas:propietario_nuevo"), {
            "nombre_completo": "Laura Méndez", "numero_documento": "1023456789", "telefono": "3001234567",
            "correo": "laura@correo.co", "direccion": "Calle 10"})
        self.assertTrue(Propietario.objects.filter(numero_documento="1023456789").exists())
        self.assertRedirects(r, reverse("cuentas:login") + "?motivo=turno", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_guardado_con_error_no_cierra_la_sesion(self):
        self.AHORA = fh("2026-11-15 13:55")
        self.login()
        self.client.get(reverse("usuarios_celdas:propietario_nuevo"))
        self.AHORA = fh("2026-11-15 14:20")
        r = self.client.post(reverse("usuarios_celdas:propietario_nuevo"), {"nombre_completo": "", "numero_documento": "1"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("_auth_user_id", self.client.session)


class HU022Autorizaciones(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.op2 = f.crear_usuario("operador2", CLAVE, "Julián Torres")
        HorarioOperador.objects.create(operador=self.op2, dia_semana=7, hora_inicio=time(6), hora_fin=time(14))

    def test_autorizacion_vigente_y_vencida(self):
        turnos.autorizar(self.admin, self.op2.pk, fh("2026-11-15 15:00"), fh("2026-11-15 19:00"), "Cubre ausencia")
        self.assertTrue(turnos.puede_ingresar(self.op2, fh("2026-11-15 16:00")))
        self.assertEqual(turnos.fin_de_jornada(self.op2, fh("2026-11-15 16:00")), fh("2026-11-15 19:00"))
        self.assertFalse(turnos.puede_ingresar(self.op2, fh("2026-11-15 19:30")))
        self.assertTrue(RegistroOperacion.objects.filter(accion="AUTORIZAR_FUERA_TURNO").exists())

    def test_autorizacion_que_extiende_el_turno(self):
        turnos.autorizar(self.admin, self.op2.pk, fh("2026-11-15 13:00"), fh("2026-11-15 18:00"), "Turno extra")
        self.assertEqual(turnos.fin_de_jornada(self.op2, fh("2026-11-15 10:00")), fh("2026-11-15 18:00"))

    def test_solo_administrador_y_datos(self):
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            turnos.autorizar(self.operador, self.op2.pk, fh("2026-11-15 15:00"), fh("2026-11-15 19:00"), "x")
        with self.assertRaisesMessage(ErrorNegocio, "posterior"):
            turnos.autorizar(self.admin, self.op2.pk, fh("2026-11-15 19:00"), fh("2026-11-15 15:00"), "x")
        self.ingresar(self.operador)
        self.assertEqual(self.client.get(reverse("cuentas:autorizaciones")).status_code, 403)


class HU023Bitacora(PruebaConReloj):
    def test_bitacora_completa_con_filtros_y_permisos(self):
        services.editar_nombre(self.admin, self.operador.pk, "María José Rodríguez")
        self.ingresar(self.admin)
        r = self.client.get(reverse("bitacora:bitacora"), {"usuario": self.admin.pk, "accion": "MODIFICAR"})
        self.assertContains(r, "Editó el nombre del operador operador")
        self.ingresar(self.operador)
        self.assertEqual(self.client.get(reverse("bitacora:bitacora")).status_code, 403)
