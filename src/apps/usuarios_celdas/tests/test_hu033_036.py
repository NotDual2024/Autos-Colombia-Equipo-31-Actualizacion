"""Escenarios de HU-033 a HU-036 (CHG-003: gestión de celdas por el administrador, RN-48 a RN-53).

Celdas de la base de pruebas: A-001 a A-003 (carro/camioneta) y M-01, M-02 (moto).
"""
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.bitacora.models import Accion, Entidad, RegistroOperacion
from apps.core.errores import ErrorNegocio
from apps.demo import fabricas as f
from apps.demo.pruebas_base import PruebaConReloj
from apps.entradas_salidas import services as estadias
from apps.usuarios_celdas import celdas as servicio
from apps.usuarios_celdas.models import Celda


def celda(codigo):
    return Celda.objects.get(codigo=codigo)


# ====================================================================== HU-033
class HU033CrearCelda(PruebaConReloj):
    def test_crear_con_el_codigo_sugerido(self):
        self.assertEqual(servicio.siguiente_codigo("CARRO_CAMIONETA"), "A-004")
        self.assertEqual(servicio.siguiente_codigo("MOTO"), "M-03")
        c = servicio.crear(self.admin, "CARRO_CAMIONETA")
        self.assertEqual((c.codigo, c.activa), ("A-004", True))
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.CREAR, entidad=Entidad.CELDA, entidad_id=c.pk,
                                                         usuario=self.admin).exists())

    def test_crear_con_codigo_escrito_en_minusculas(self):
        self.assertEqual(servicio.crear(self.admin, "MOTO", " m-10 ").codigo, "M-10")

    def test_codigo_repetido(self):
        with self.assertRaisesMessage(ErrorNegocio, "Ya existe una celda con el código M-01"):
            servicio.crear(self.admin, "MOTO", "m-01")

    def test_formato_invalido(self):
        for codigo in ("A-200", "M-5", "M-001", "M-00"):
            with self.assertRaisesMessage(ErrorNegocio, "El código de una celda de moto debe tener el formato M-01 a M-99"):
                servicio.crear(self.admin, "MOTO", codigo)
        with self.assertRaisesMessage(ErrorNegocio, "A-001 a A-999"):
            servicio.crear(self.admin, "CARRO_CAMIONETA", "A-12")

    def test_la_base_de_datos_rechaza_un_formato_invalido(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Celda.objects.create(codigo="M-07", tipo="CARRO_CAMIONETA")

    def test_la_celda_nueva_se_puede_usar(self):
        servicio.crear(self.admin, "CARRO_CAMIONETA")
        self.vehiculo()
        estadias.registrar_entrada("ABC123", "A-004", self.operador)
        self.assertTrue(servicio.esta_ocupada(celda("A-004")))

    def test_pantalla(self):
        self.ingresar(self.admin)
        r = self.client.post(reverse("usuarios_celdas:celdas"), {"tipo": "MOTO", "codigo": ""}, follow=True)
        self.assertContains(r, "Celda M-03 creada.")
        r = self.client.post(reverse("usuarios_celdas:celdas"), {"tipo": "MOTO", "codigo": "M-03"})
        self.assertContains(r, "Ya existe una celda con el código M-03")

    def test_solo_el_administrador(self):
        self.ingresar()
        self.assertEqual(self.client.get(reverse("usuarios_celdas:celdas")).status_code, 403)
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            servicio.crear(self.operador, "MOTO")


# ====================================================================== HU-034
class HU034ConsultarYCambiarTipo(PruebaConReloj):
    def test_lista_con_estados_y_filtros(self):
        self.vehiculo()
        estadias.registrar_entrada("ABC123", "A-003", self.operador)
        servicio.inactivar(self.admin, celda("A-002"), "Mantenimiento")
        estados = {fila.celda.codigo: (fila.estado, fila.placa) for fila in servicio.listar()}
        self.assertEqual(estados["A-003"], (servicio.OCUPADA, "ABC123"))
        self.assertEqual(estados["A-002"], (servicio.INACTIVA, None))
        self.assertEqual(estados["A-001"], (servicio.LIBRE, None))
        self.assertEqual([x.celda.codigo for x in servicio.listar(tipo="MOTO")], ["M-01", "M-02"])
        self.assertEqual([x.celda.codigo for x in servicio.listar(estado=servicio.INACTIVA)], ["A-002"])
        self.assertEqual([x.celda.codigo for x in servicio.listar(texto="a-00")], ["A-001", "A-002", "A-003"])
        self.ingresar(self.admin)
        r = self.client.get(reverse("usuarios_celdas:celdas"))
        self.assertContains(r, "Ocupada · ABC123")
        self.assertContains(r, "Mantenimiento")

    def test_cambiar_el_tipo_de_una_celda_nueva(self):
        nueva = servicio.crear(self.admin, "CARRO_CAMIONETA")
        servicio.cambiar_tipo(self.admin, nueva, "MOTO", "M-51")
        nueva.refresh_from_db()
        self.assertEqual((nueva.codigo, nueva.tipo), ("M-51", "MOTO"))
        registro = RegistroOperacion.objects.get(accion=Accion.MODIFICAR, entidad=Entidad.CELDA, entidad_id=nueva.pk)
        self.assertEqual(registro.detalle["codigo"], ["A-004", "M-51"])

    def test_celda_ocupada(self):
        self.vehiculo()
        estadias.registrar_entrada("ABC123", "A-003", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La celda está ocupada"):
            servicio.cambiar_tipo(self.admin, celda("A-003"), "MOTO", "M-20")

    def test_celda_con_historial(self):
        v = self.vehiculo()
        f.crear_estadia(v, "A-001", self.AHORA - timedelta(days=2), self.operador, self.AHORA - timedelta(days=1), self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La celda ya se usó; inactívala y crea una nueva"):
            servicio.cambiar_tipo(self.admin, celda("A-001"), "MOTO", "M-20")


# ====================================================================== HU-035
class HU035InactivarYReactivar(PruebaConReloj):
    def test_inactivar_con_motivo(self):
        servicio.inactivar(self.admin, celda("A-001"), "Mantenimiento")
        c = celda("A-001")
        self.assertEqual((c.activa, c.motivo_inactivacion), (False, "Mantenimiento"))
        self.vehiculo()
        with self.assertRaises(ErrorNegocio):
            estadias.registrar_entrada("ABC123", "A-001", self.operador)
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.INACTIVAR, entidad=Entidad.CELDA).exists())

    def test_la_celda_inactiva_no_se_ofrece_al_registrar_una_entrada(self):
        servicio.inactivar(self.admin, celda("A-001"), "Mantenimiento")
        self.vehiculo()
        self.ingresar()
        r = self.client.get(reverse("entradas_salidas:entrada"), {"placa": "ABC123"})
        self.assertContains(r, "A-002")
        self.assertNotContains(r, 'value="A-001"')

    def test_motivo_obligatorio(self):
        with self.assertRaisesMessage(ErrorNegocio, "motivo"):
            servicio.inactivar(self.admin, celda("A-001"), "  ")

    def test_celda_ocupada(self):
        self.vehiculo()
        estadias.registrar_entrada("ABC123", "A-003", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La celda está ocupada"):
            servicio.inactivar(self.admin, celda("A-003"), "Mantenimiento")

    def test_reactivar(self):
        servicio.inactivar(self.admin, celda("A-001"), "Mantenimiento")
        self.ingresar(self.admin)
        self.client.post(reverse("usuarios_celdas:celda_estado", args=[celda("A-001").pk]), {"activa": "1"})
        c = celda("A-001")
        self.assertEqual((c.activa, c.motivo_inactivacion), (True, None))
        self.vehiculo()
        estadias.registrar_entrada("ABC123", "A-001", self.operador)

    def test_pantalla_inactivar(self):
        self.ingresar(self.admin)
        r = self.client.post(reverse("usuarios_celdas:celda_estado", args=[celda("A-001").pk]),
                             {"activa": "0", "motivo": ""}, follow=True)
        self.assertContains(r, "A-001: Escribe el motivo de la inactivación.")
        self.assertTrue(celda("A-001").activa)

    def test_solo_el_administrador(self):
        self.ingresar()
        r = self.client.post(reverse("usuarios_celdas:celda_estado", args=[celda("A-001").pk]), {"activa": "0", "motivo": "x"})
        self.assertEqual(r.status_code, 403)


# ====================================================================== HU-036
class HU036EliminarCelda(PruebaConReloj):
    def test_eliminar_una_celda_sin_historial(self):
        nueva = servicio.crear(self.admin, "MOTO")
        pk = nueva.pk
        self.ingresar(self.admin)
        r = self.client.post(reverse("usuarios_celdas:celda_eliminar", args=[pk]), follow=True)
        self.assertContains(r, "Celda M-03 eliminada.")
        self.assertFalse(Celda.objects.filter(pk=pk).exists())
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.ELIMINAR, entidad=Entidad.CELDA, entidad_id=pk).exists())

    def test_celda_con_historial(self):
        v = self.vehiculo()
        f.crear_estadia(v, "A-001", self.AHORA - timedelta(days=2), self.operador, self.AHORA - timedelta(days=1), self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La celda tiene historial; solo se puede inactivar"):
            servicio.eliminar(self.admin, celda("A-001"))
        self.assertTrue(Celda.objects.filter(codigo="A-001").exists())

    def test_celda_ocupada(self):
        self.vehiculo()
        estadias.registrar_entrada("ABC123", "A-002", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La celda está ocupada"):
            servicio.eliminar(self.admin, celda("A-002"))
