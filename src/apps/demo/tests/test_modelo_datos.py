"""Repite, a través del ORM y las migraciones de Django, las comprobaciones del
DDL aprobado (docs/sql/validar_ddl.py, 42 casos). Garantiza que las migraciones
reproducen el modelo físico v1.1."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from apps.cuentas.models import HorarioOperador, Rol, Usuario
from apps.entradas_salidas.models import Estadia
from apps.notificaciones.models import AvisoCorreo, ContactoAutoridad
from apps.novedades.models import Novedad, NovedadEstadia
from apps.pagos.models import Pago, Tarifa
from apps.usuarios_celdas.models import Celda, Propietario, Vehiculo

TZ = ZoneInfo("America/Bogota")


def fh(texto: str) -> datetime:
    return datetime.fromisoformat(texto).replace(tzinfo=TZ)


D = fh("2026-11-15 08:00")


class ModeloDatosTests(TestCase):
    def falla(self, funcion):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                funcion()

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user("admin", password="x", rol=Rol.ADMINISTRADOR)
        cls.prop = Propietario.objects.create(
            nombre_completo="Ana Gil", numero_documento="1023456789", telefono="3001234567", correo="a@b.co",
            direccion="Cra 1 # 2-3", fecha_registro=D,
        )
        cls.carro = Vehiculo.objects.create(placa="ABC123", tipo="CARRO", marca="Chevrolet", nombre="Spark", modelo=2020, color="Rojo", propietario=cls.prop, fecha_registro=D)
        cls.moto = Vehiculo.objects.create(placa="XYZ12D", tipo="MOTO", marca="Yamaha", nombre="NMAX", modelo=2023, color="Negro", propietario=cls.prop, fecha_registro=D)
        cls.c1 = Celda.objects.create(codigo="A-001", tipo="CARRO_CAMIONETA")
        cls.c2 = Celda.objects.create(codigo="A-002", tipo="CARRO_CAMIONETA")
        cls.pago = Pago.objects.create(vehiculo=cls.carro, periodo_inicio=date(2026, 10, 16), periodo_fin=date(2026, 11, 15), valor=150000, fecha_pago=D, registrado_por=cls.admin)

    def vehiculo(self, **kw):
        datos = dict(placa="QQQ111", tipo="CARRO", marca="M", nombre="N", modelo=2020, color="Azul", propietario=self.prop, fecha_registro=D)
        datos.update(kw)
        return Vehiculo.objects.create(**datos)

    # --- usuarios y propietarios
    def test_rol_invalido(self):
        self.falla(lambda: Usuario.objects.create(username="x", password="h", rol="JEFE"))

    def test_cedula_duplicada(self):
        self.falla(lambda: Propietario.objects.create(nombre_completo="X", numero_documento="1023456789", telefono="3001112233", correo="x@y.co", direccion="C", fecha_registro=D))

    def test_cedula_con_letras(self):
        self.falla(lambda: Propietario.objects.create(nombre_completo="X", numero_documento="10A3456", telefono="3001112233", correo="x@y.co", direccion="C", fecha_registro=D))

    def test_cedula_muy_corta(self):
        self.falla(lambda: Propietario.objects.create(nombre_completo="X", numero_documento="1234", telefono="3001112233", correo="x@y.co", direccion="C", fecha_registro=D))

    # --- vehículos (RN-02, RN-23)
    def test_tipo_invalido(self):
        self.falla(lambda: self.vehiculo(tipo="BUS"))

    def test_placa_moto_antigua_aceptada(self):
        self.assertEqual(self.vehiculo(placa="MNO45", tipo="MOTO").placa, "MNO45")

    def test_placa_minusculas_rechazada(self):
        self.falla(lambda: self.vehiculo(placa="abc124"))

    def test_placa_formato_invalido(self):
        self.falla(lambda: self.vehiculo(placa="AB-123"))

    def test_modelo_fuera_de_rango(self):
        self.falla(lambda: self.vehiculo(placa="JKL987", modelo=1800))

    def test_placa_duplicada(self):
        self.falla(lambda: self.vehiculo(placa="ABC123"))

    # --- tarifas y pagos
    def test_tarifa_valor_cero(self):
        self.falla(lambda: Tarifa.objects.create(categoria="MOTO", valor=0, vigente_desde=date(2026, 1, 1)))

    def test_tarifa_duplicada(self):
        Tarifa.objects.create(categoria="MOTO", valor=80000, vigente_desde=date(2026, 1, 1))
        self.falla(lambda: Tarifa.objects.create(categoria="MOTO", valor=90000, vigente_desde=date(2026, 1, 1)))

    def test_pago_periodo_invertido(self):
        self.falla(lambda: Pago.objects.create(vehiculo=self.carro, periodo_inicio=date(2026, 11, 15), periodo_fin=date(2026, 10, 16), valor=150000, fecha_pago=D, registrado_por=self.admin))

    # --- estadías (RN-04, RN-05)
    def entrada(self, vehiculo, celda, cuando=D):
        return Estadia.objects.create(vehiculo=vehiculo, celda=celda, fecha_hora_entrada=cuando, usuario_entrada=self.admin)

    def test_rn04_segunda_estadia_abierta_del_vehiculo(self):
        self.entrada(self.carro, self.c1)
        self.falla(lambda: self.entrada(self.carro, self.c2))

    def test_rn05_celda_ocupada(self):
        self.entrada(self.carro, self.c1)
        self.falla(lambda: self.entrada(self.moto, self.c1))

    def test_salida_sin_usuario(self):
        e = self.entrada(self.carro, self.c1)
        e.fecha_hora_salida = fh("2026-11-15 09:00")
        self.falla(e.save)

    def test_salida_anterior_a_entrada(self):
        e = self.entrada(self.carro, self.c1)
        e.fecha_hora_salida, e.usuario_salida = fh("2026-11-15 07:00"), self.admin
        self.falla(e.save)

    def test_salida_que_cruza_medianoche_y_reingreso(self):
        e = self.entrada(self.carro, self.c1, fh("2026-11-15 23:30"))
        e.fecha_hora_salida, e.usuario_salida = fh("2026-11-16 06:00"), self.admin
        e.save()
        self.entrada(self.moto, self.c1, fh("2026-11-16 07:00"))  # celda liberada
        self.entrada(self.carro, self.c2, fh("2026-11-16 08:00"))  # el vehículo vuelve a entrar
        self.assertEqual(Estadia.objects.filter(fecha_hora_salida__isnull=True).count(), 2)

    # --- novedades (RN-14)
    def test_novedad_y_vinculos(self):
        e1, e2 = self.entrada(self.carro, self.c1), self.entrada(self.moto, self.c2)
        n = Novedad.objects.create(tipo="RAYON", descripcion="Rayón lateral", fecha_hora_ocurrencia=fh("2026-11-15 08:30"), fecha_hora_registro=fh("2026-11-15 09:00"), registrado_por=self.admin)
        NovedadEstadia.objects.create(novedad=n, estadia=e1)
        NovedadEstadia.objects.create(novedad=n, estadia=e2)
        self.assertEqual(n.vinculos.count(), 2)
        self.falla(lambda: NovedadEstadia.objects.create(novedad=n, estadia=e2))

    def test_novedad_sin_descripcion(self):
        self.falla(lambda: Novedad.objects.create(tipo="OTRO", descripcion="   ", fecha_hora_ocurrencia=D, fecha_hora_registro=D, registrado_por=self.admin))

    def test_novedad_registrada_antes_de_ocurrir(self):
        self.falla(lambda: Novedad.objects.create(tipo="OTRO", descripcion="x", fecha_hora_ocurrencia=fh("2026-11-15 10:00"), fecha_hora_registro=fh("2026-11-15 09:00"), registrado_por=self.admin))

    # --- avisos (RN-11, RN-22, P-24) y contactos (P-25)
    def aviso(self, numero, origen="AUTOMATICO", usuario=None, resultado="ENVIADO_SIMULADO"):
        return AvisoCorreo.objects.create(pago=self.pago, numero_envio=numero, origen=origen, enviado_por=usuario, destinatario="a@b.co", asunto="s", cuerpo="c", fecha_hora=D, resultado=resultado)

    def test_avisos_limite(self):
        self.aviso(1)
        self.falla(lambda: self.aviso(1, "MANUAL", self.admin))       # segundo "primer" correo
        self.aviso(2, "MANUAL", self.admin)                           # un reenvío
        self.falla(lambda: self.aviso(3, "MANUAL", self.admin))       # segundo reenvío
        self.aviso(None, resultado="FALLIDO")                         # fallido sin número (P-24)
        self.falla(lambda: self.aviso(None, "MANUAL", None, "FALLIDO"))  # manual sin usuario

    def test_varios_contactos_por_vencimiento(self):
        ContactoAutoridad.objects.create(pago=self.pago, fecha_hora=D, registrado_por=self.admin, observacion="Llamada a tránsito")
        ContactoAutoridad.objects.create(pago=self.pago, fecha_hora=D, registrado_por=self.admin, observacion="Seguimiento")
        self.assertEqual(self.pago.contactos_autoridad.count(), 2)

    def test_contacto_sin_observacion(self):
        self.falla(lambda: ContactoAutoridad.objects.create(pago=self.pago, fecha_hora=D, registrado_por=self.admin, observacion=" "))

    # --- horario provisional
    def test_horario_dia_invalido(self):
        self.falla(lambda: HorarioOperador.objects.create(operador=self.admin, dia_semana=8, hora_inicio="08:00", hora_fin="16:00"))

    # --- RN-07: no se borra
    def test_no_se_puede_borrar_vehiculo_con_estadias(self):
        self.entrada(self.carro, self.c1)
        with self.assertRaises(ProtectedError):
            self.carro.delete()

    # --- métodos de dominio
    def test_metodos_de_dominio(self):
        moto_celda = Celda(codigo="M-001", tipo="MOTO")
        self.assertTrue(self.c1.admite(self.carro))
        self.assertFalse(moto_celda.admite(self.carro))
        self.assertTrue(moto_celda.admite(self.moto))
        self.assertTrue(self.pago.cubre(date(2026, 11, 15)))
        self.assertFalse(self.pago.cubre(date(2026, 11, 16)))
        e = Estadia(fecha_hora_entrada=fh("2026-11-15 08:00"), fecha_hora_salida=fh("2026-11-15 12:00"))
        self.assertTrue(e.incluye(fh("2026-11-15 10:00")))
        self.assertFalse(e.incluye(fh("2026-11-15 13:00")))
