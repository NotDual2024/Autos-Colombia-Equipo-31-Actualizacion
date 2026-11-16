"""Criterios de aceptación de HU-007, HU-008, HU-009 y HU-011, y del planificador (DEC-008)."""
from datetime import timedelta
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from apps.core import correo
from apps.core.errores import ErrorNegocio
from apps.demo import fabricas as f
from apps.demo.pruebas_base import PruebaConReloj, fh
from apps.notificaciones import planificador, services
from apps.notificaciones.models import AvisoCorreo, ContactoAutoridad


class Base(PruebaConReloj):
    def dentro_con_vencimiento(self, placa="ABC123", dias_vencido=1):
        v = self.vehiculo(placa, fin=self.hoy - timedelta(days=dias_vencido))
        f.crear_estadia(v, "A-001" if placa == "ABC123" else "A-002", fh("2026-11-01 08:00"), self.operador)
        return v


class HU007Vencidos(Base):
    def test_vencido_aparece_con_dias(self):
        self.dentro_con_vencimiento(dias_vencido=1)
        filas = services.vencidos_dentro()
        self.assertEqual((len(filas), filas[0].dias_vencido, filas[0].envios), (1, 1, 0))

    def test_vigente_no_aparece(self):
        v = self.vehiculo()
        f.crear_estadia(v, "A-001", fh("2026-11-15 08:00"), self.operador)
        self.assertEqual(services.vencidos_dentro(), [])

    def test_si_paga_deja_de_aparecer_rn17(self):
        v = self.dentro_con_vencimiento(dias_vencido=3)
        f.crear_pago(v, self.hoy + timedelta(days=27), self.operador)
        self.assertEqual(services.vencidos_dentro(), [])

    def test_si_sale_deja_de_aparecer(self):
        self.dentro_con_vencimiento()
        from apps.entradas_salidas import services as estadias
        estadias.registrar_salida("ABC123", self.operador)
        self.assertEqual(services.vencidos_dentro(), [])


class HU008AvisoAutomatico(Base):
    def test_envio_el_dia_del_vencimiento(self):
        self.dentro_con_vencimiento(dias_vencido=0)
        self.assertEqual(services.enviar_automaticos(), 1)
        aviso = AvisoCorreo.objects.get()
        self.assertEqual((aviso.numero_envio, aviso.origen, aviso.resultado), (1, "AUTOMATICO", "ENVIADO_SIMULADO"))
        self.assertIn("ABC123", aviso.cuerpo)
        self.assertIn("23/11/2026", aviso.cuerpo)  # fecha límite: vencimiento + 8 días
        self.assertIn("Debe pagar la mensualidad", aviso.cuerpo)

    def test_un_solo_correo_idempotente(self):
        self.dentro_con_vencimiento(dias_vencido=0)
        services.enviar_automaticos()
        self.assertEqual(services.enviar_automaticos(), 0)
        self.assertEqual(AvisoCorreo.objects.count(), 1)

    def test_pendiente_por_servidor_apagado_rn21(self):
        self.dentro_con_vencimiento(dias_vencido=4)
        self.assertEqual(services.enviar_automaticos(), 1)

    def test_fallo_del_correo_queda_registrado_y_no_cuenta_rnf013(self):
        self.dentro_con_vencimiento(dias_vencido=0)

        class Roto(correo.ServicioCorreo):
            def enviar(self, *a):
                raise ConnectionError("sin servicio")

        correo.usar_servicio_correo(Roto())
        self.addCleanup(correo.usar_servicio_correo, correo.ServicioCorreoSimulado())
        with self.assertLogs("apps.notificaciones.services", level="ERROR"):
            self.assertEqual(services.enviar_automaticos(), 0)
        aviso = AvisoCorreo.objects.get()
        self.assertEqual((aviso.resultado, aviso.numero_envio), ("FALLIDO", None))
        # las entradas siguen funcionando
        from apps.entradas_salidas import services as estadias
        self.vehiculo("DEF456")
        self.assertIsNotNone(estadias.registrar_entrada("DEF456", "A-002", self.operador))
        correo.usar_servicio_correo(correo.ServicioCorreoSimulado())
        self.assertEqual(services.enviar_automaticos(), 1)  # se reintenta: el fallido no cuenta (P-24)

    def test_vehiculo_que_ya_salio_no_recibe_correo(self):
        v = self.vehiculo(fin=self.hoy)
        f.crear_estadia(v, "A-001", fh("2026-11-14 08:00"), self.operador, fh("2026-11-15 08:00"), self.operador)
        self.assertEqual(services.enviar_automaticos(), 0)

    def test_comando(self):
        self.dentro_con_vencimiento(dias_vencido=0)
        call_command("enviar_avisos_vencimiento", stdout=mock.MagicMock())
        self.assertEqual(AvisoCorreo.objects.count(), 1)


class HU009Plazo(Base):
    def test_dia_8_no_vencido_dia_9_vencido(self):
        # Vence el día 1 → el día 8 aún no; el día 9 (vencimiento + 8) sí.
        v = self.vehiculo(fin=fh("2026-11-01 00:00").date())
        f.crear_estadia(v, "A-001", fh("2026-10-20 08:00"), self.operador)
        self.AHORA = fh("2026-11-08 10:00")
        self.assertFalse(services.vencidos_dentro()[0].plazo_vencido)
        self.AHORA = fh("2026-11-09 10:00")
        self.assertTrue(services.vencidos_dentro()[0].plazo_vencido)

    def test_registrar_contacto_solo_admin_y_varios(self):
        self.dentro_con_vencimiento(dias_vencido=9)
        pago = services.vencidos_dentro()[0].pago
        services.registrar_contacto(pago.id, self.admin, "Llamada a tránsito")
        services.registrar_contacto(pago.id, self.admin, "Seguimiento")
        self.assertEqual(ContactoAutoridad.objects.count(), 2)
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            services.registrar_contacto(pago.id, self.operador, "x")

    def test_operador_recibe_acceso_denegado_en_pantalla(self):
        self.dentro_con_vencimiento(dias_vencido=9)
        pago = services.vencidos_dentro()[0].pago
        self.ingresar(self.operador)
        r = self.client.post(reverse("notificaciones:contacto", args=[pago.id]), {"observacion": "x"})
        self.assertEqual(r.status_code, 403)
        self.assertContains(r, "Acceso denegado", status_code=403)

    def test_antes_del_plazo_no_se_puede_registrar(self):
        self.dentro_con_vencimiento(dias_vencido=7)
        pago = services.vencidos_dentro()[0].pago
        with self.assertRaisesMessage(ErrorNegocio, "todavía no ha vencido"):
            services.registrar_contacto(pago.id, self.admin, "x")


class HU011CorreoManual(Base):
    def setUp(self):
        super().setUp()
        self.dentro_con_vencimiento(dias_vencido=2)
        self.pago = services.vencidos_dentro()[0].pago

    def test_primer_envio_manual(self):
        aviso = services.enviar_manual(self.pago.id, self.operador)
        self.assertEqual((aviso.numero_envio, aviso.origen, aviso.enviado_por), (1, "MANUAL", self.operador))

    def test_reenvio_exige_confirmacion_y_solo_uno(self):
        services.enviar_automaticos()
        with self.assertRaises(services.RequiereConfirmacion):
            services.enviar_manual(self.pago.id, self.operador)
        self.assertEqual(services.enviar_manual(self.pago.id, self.operador, confirmar_reenvio=True).numero_envio, 2)
        with self.assertRaisesMessage(ErrorNegocio, "El correo de este vencimiento ya se reenvió una vez"):
            services.enviar_manual(self.pago.id, self.operador, confirmar_reenvio=True)

    def test_pantallas_confirmacion_y_correo(self):
        services.enviar_automaticos()
        self.ingresar()
        r = self.client.post(reverse("notificaciones:enviar", args=[self.pago.id]))
        self.assertContains(r, "¿Desea reenviarlo?")
        r = self.client.post(reverse("notificaciones:enviar", args=[self.pago.id]), {"confirmar": "1"}, follow=True)
        self.assertContains(r, "Correo enviado (simulación)")
        self.assertContains(r, "2 de 2")
        r = self.client.get(reverse("notificaciones:vencidos"))
        self.assertContains(r, "2 de 2 (máximo)")
        self.assertNotContains(r, "Enviar correo</button>")


class PlanificadorTests(SimpleTestCase):
    def test_solo_en_el_proceso_del_servidor(self):
        self.assertFalse(planificador.es_proceso_servidor(["manage.py", "test"], {}))
        self.assertFalse(planificador.es_proceso_servidor(["manage.py", "migrate"], {}))
        self.assertFalse(planificador.es_proceso_servidor(["manage.py", "runserver"], {}))  # proceso padre del autoreload
        self.assertTrue(planificador.es_proceso_servidor(["manage.py", "runserver"], {"RUN_MAIN": "true"}))
        self.assertTrue(planificador.es_proceso_servidor(["manage.py", "runserver", "--noreload"], {}))

    @override_settings(AVISOS_PLANIFICADOR_ACTIVO=True)
    def test_no_arranca_en_pruebas(self):
        self.assertFalse(planificador.iniciar())
