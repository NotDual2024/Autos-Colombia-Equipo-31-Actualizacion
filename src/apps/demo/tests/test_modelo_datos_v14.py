"""Las comprobaciones nuevas del DDL v1.4 (docs/sql/validar_ddl.py), repetidas a través del ORM (plan iteración 3, paso 1)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bitacora.models import RegistroOperacion
from apps.cuentas.models import Rol, Usuario
from apps.pagos.models import CorreoConfirmacion, Descuento, Pago
from apps.usuarios_celdas.models import Propietario, Vehiculo

D = datetime(2026, 11, 15, 8, 0, tzinfo=ZoneInfo("America/Bogota"))


class ModeloDatosV14Tests(TestCase):
    def falla(self, funcion):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                funcion()

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user("admin", password="x", rol=Rol.ADMINISTRADOR)
        cls.prop = Propietario.objects.create(nombre_completo="Ana Gil", numero_documento="1023456789", telefono="3001234567",
                                              correo="a@b.co", direccion="Cra 1", fecha_registro=D)
        cls.carro = Vehiculo.objects.create(placa="ABC123", tipo="CARRO", marca="M", nombre="N", modelo=2020, color="Rojo",
                                            propietario=cls.prop, fecha_registro=D)
        cls.moto = Vehiculo.objects.create(placa="XYZ12D", tipo="MOTO", marca="M", nombre="N", modelo=2020, color="Negro",
                                           propietario=cls.prop, fecha_registro=D)
        cls.desc = Descuento.objects.create(descripcion="Cliente frecuente", porcentaje=10, creado_por=cls.admin, fecha_creacion=D)

    def pago(self, **kw):
        datos = dict(vehiculo=self.moto, periodo_inicio=date(2026, 11, 15), periodo_fin=date(2026, 12, 15), meses=1,
                     tarifa_unitaria=80000, valor_bruto=80000, valor=80000, medio="EFECTIVO",
                     numero_factura=Pago.objects.count() + 100, fecha_pago=D, registrado_por=self.admin)
        datos.update(kw)
        return Pago.objects.create(**datos)

    # --- RN-46: motivo de inactivación
    def test_inactivo_sin_motivo(self):
        self.falla(lambda: Vehiculo.objects.filter(pk=self.carro.pk).update(activo=False))

    def test_activo_con_motivo(self):
        self.falla(lambda: Vehiculo.objects.filter(pk=self.carro.pk).update(motivo_inactivacion="FALTA_PAGO"))

    def test_otro_sin_descripcion(self):
        self.falla(lambda: Propietario.objects.filter(pk=self.prop.pk).update(activo=False, motivo_inactivacion="OTRO",
                                                                              descripcion_inactivacion="  "))

    def test_motivos_validos(self):
        Vehiculo.objects.filter(pk=self.carro.pk).update(activo=False, motivo_inactivacion="FALTA_PAGO")
        Propietario.objects.filter(pk=self.prop.pk).update(activo=False, motivo_inactivacion="OTRO", descripcion_inactivacion="Vendió")
        self.falla(lambda: Vehiculo.objects.filter(pk=self.moto.pk).update(activo=False, motivo_inactivacion="ROBO"))

    # --- RN-42: descuentos
    def test_porcentaje_fuera_de_rango(self):
        for p in (0, 120):
            self.falla(lambda p=p: Descuento.objects.create(descripcion="x", porcentaje=p, creado_por=self.admin, fecha_creacion=D))

    def test_descuento_sin_descripcion(self):
        self.falla(lambda: Descuento.objects.create(descripcion="  ", porcentaje=10, creado_por=self.admin, fecha_creacion=D))

    # --- RN-40, RN-41, RN-43, RN-47: pago
    def test_valor_con_descuento_correcto(self):
        p = self.pago(vehiculo=self.carro, periodo_fin=date(2027, 2, 15), meses=3, tarifa_unitaria=150000, valor_bruto=450000,
                      descuento=self.desc, porcentaje_descuento=10, valor=405000, medio="TARJETA")
        self.assertEqual(p.valor_descuento(), 45000)

    def test_valor_distinto_del_calculado(self):
        self.falla(lambda: self.pago(valor=70000))

    def test_valor_bruto_distinto(self):
        self.falla(lambda: self.pago(meses=2, periodo_fin=date(2027, 1, 15), valor_bruto=150000, valor=150000))

    def test_descuento_sin_porcentaje_copiado(self):
        self.falla(lambda: self.pago(descuento=self.desc))

    def test_trece_meses(self):
        self.falla(lambda: self.pago(meses=13, valor_bruto=1040000, valor=1040000, periodo_fin=date(2027, 12, 15)))

    def test_medio_invalido(self):
        self.falla(lambda: self.pago(medio="CHEQUE"))

    def test_factura_repetida(self):
        self.pago(numero_factura=7)
        self.falla(lambda: self.pago(vehiculo=self.carro, tarifa_unitaria=150000, valor_bruto=150000, valor=150000, numero_factura=7))

    def test_pago_repetido_mismo_inicio(self):
        self.pago()
        self.falla(lambda: self.pago())

    def test_periodo_de_un_dia_o_invertido(self):
        self.falla(lambda: self.pago(periodo_fin=date(2026, 11, 15)))

    def test_descuento_100_deja_valor_cero(self):
        cortesia = Descuento.objects.create(descripcion="Cortesía", porcentaje=100, creado_por=self.admin, fecha_creacion=D)
        self.assertEqual(self.pago(descuento=cortesia, porcentaje_descuento=100, valor=0).valor, 0)

    # --- RN-44: corrección
    def test_corregido_sin_motivo(self):
        p = self.pago()
        self.falla(lambda: Pago.objects.filter(pk=p.pk).update(estado="CORREGIDO", corregido_por=self.admin, fecha_correccion=D))

    def test_correccion_completa_y_reemplazo(self):
        p = self.pago()
        Pago.objects.filter(pk=p.pk).update(estado="CORREGIDO", motivo_correccion="Eran 2 meses", corregido_por=self.admin, fecha_correccion=D)
        nuevo = self.pago(meses=2, periodo_fin=date(2027, 1, 15), valor_bruto=160000, valor=160000, corrige_a=p)
        self.assertEqual(Pago.objects.get(pk=p.pk).reemplazo, nuevo)
        self.falla(lambda: self.pago(periodo_inicio=date(2026, 12, 15), periodo_fin=date(2027, 1, 15), corrige_a=p))
        self.falla(lambda: Pago.objects.filter(pk=p.pk).delete())

    def test_un_pago_no_se_corrige_a_si_mismo(self):
        p = self.pago()
        self.falla(lambda: Pago.objects.filter(pk=p.pk).update(corrige_a=p))

    # --- RN-47 y bitácora
    def test_correo_de_confirmacion(self):
        p = self.pago()
        CorreoConfirmacion.objects.create(pago=p, destinatario="a@b.co", asunto="s", cuerpo="c", fecha_hora=D, resultado="ENVIADO_SIMULADO")
        self.falla(lambda: CorreoConfirmacion.objects.create(pago=p, destinatario="a@b.co", asunto="s", cuerpo="c", fecha_hora=D,
                                                             resultado="PENDIENTE"))

    def test_bitacora_acciones_nuevas(self):
        for accion, entidad in (("CORREGIR_PAGO", "PAGO"), ("DESHABILITAR", "DESCUENTO"), ("CREAR", "TARIFA")):
            RegistroOperacion.objects.create(fecha_hora=D, usuario=self.admin, accion=accion, entidad=entidad, entidad_id=1, descripcion="x")

    def test_otro_con_descripcion_nula(self):
        self.falla(lambda: Vehiculo.objects.filter(pk=self.carro.pk).update(activo=False, motivo_inactivacion="OTRO",
                                                                            descripcion_inactivacion=None))
