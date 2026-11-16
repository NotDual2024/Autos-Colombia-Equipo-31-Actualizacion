"""Comprobaciones del modelo v1.3 (iteración 2) a través del ORM: equivalen a las 18 nuevas del DDL."""
from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bitacora.models import RegistroOperacion
from apps.cuentas.models import AutorizacionFueraTurno, HorarioOperador, Rol, Usuario
from apps.usuarios_celdas.models import HistorialPropiedad, Propietario, SolicitudCambioPropietario, Vehiculo

TZ = ZoneInfo("America/Bogota")
D = datetime(2026, 11, 15, 8, 0, tzinfo=TZ)


def fh(texto):
    return datetime.fromisoformat(texto).replace(tzinfo=TZ)


class ModeloV13Tests(TestCase):
    def falla(self, funcion):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                funcion()

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user("admin", password="x", rol=Rol.ADMINISTRADOR)
        cls.op = Usuario.objects.create_user("op", password="x", rol=Rol.OPERADOR)
        cls.ana = Propietario.objects.create(nombre_completo="Ana Gil", numero_documento="1023456789", telefono="3001234567", correo="a@b.co", direccion="C", fecha_registro=D)
        cls.luis = Propietario.objects.create(nombre_completo="Luis Mora", numero_documento="1056789012", telefono="3109876543", correo="l@m.co", direccion="C", fecha_registro=D)
        cls.v = Vehiculo.objects.create(placa="ABC123", tipo="CARRO", marca="M", nombre="N", modelo=2020, color="Rojo", propietario=cls.ana, fecha_registro=D)

    def propietario(self, telefono):
        return Propietario.objects.create(nombre_completo="X", numero_documento="1067890123", telefono=telefono, correo="x@z.co", direccion="C", fecha_registro=D)

    def test_rn30_celular(self):
        self.falla(lambda: self.propietario("6012345678"))
        self.falla(lambda: self.propietario("300123456"))
        self.assertTrue(self.propietario("3201234567").pk)

    def test_horarios(self):
        nocturna = HorarioOperador.objects.create(operador=self.op, dia_semana=5, hora_inicio=time(22), hora_fin=time(6))
        self.assertTrue(nocturna.cruza_medianoche())
        self.falla(lambda: HorarioOperador.objects.create(operador=self.op, dia_semana=1, hora_inicio=time(8), hora_fin=time(8)))

    def test_autorizaciones(self):
        AutorizacionFueraTurno.objects.create(operador=self.op, autorizado_por=self.admin, motivo="Cubre ausencia", desde=fh("2026-11-15 15:00"), hasta=fh("2026-11-15 19:00"), fecha_registro=D)
        self.falla(lambda: AutorizacionFueraTurno.objects.create(operador=self.op, autorizado_por=self.admin, motivo="x", desde=fh("2026-11-15 19:00"), hasta=fh("2026-11-15 15:00"), fecha_registro=D))
        self.falla(lambda: AutorizacionFueraTurno.objects.create(operador=self.admin, autorizado_por=self.admin, motivo="x", desde=fh("2026-11-15 15:00"), hasta=fh("2026-11-15 19:00"), fecha_registro=D))

    def solicitud(self, **kw):
        datos = dict(vehiculo=self.v, propietario_actual=self.ana, propietario_nuevo=self.luis, motivo="Venta", solicitado_por=self.op, fecha_solicitud=D)
        datos.update(kw)
        return SolicitudCambioPropietario.objects.create(**datos)

    def test_solicitudes(self):
        s = self.solicitud()
        self.falla(lambda: self.solicitud(motivo="Otra"))                     # una pendiente por vehículo
        self.falla(lambda: self.solicitud(propietario_nuevo=self.ana))         # mismo propietario
        s.estado = "APROBADA"
        self.falla(s.save)                                                     # aprobada sin resolución
        s.resuelto_por, s.fecha_resolucion = self.admin, fh("2026-11-15 10:00")
        s.save()
        self.assertTrue(self.solicitud(motivo="Nueva").pk)                     # ya no hay pendiente

    def test_historial(self):
        HistorialPropiedad.objects.create(vehiculo=self.v, propietario=self.ana, desde=fh("2026-05-01 08:00"), hasta=fh("2026-11-15 10:00"))
        self.falla(lambda: HistorialPropiedad.objects.create(vehiculo=self.v, propietario=self.ana, desde=fh("2026-11-15 10:00"), hasta=fh("2026-05-01 08:00")))
        self.assertEqual(self.v.propietario_desde(), fh("2026-11-15 10:00"))

    def test_bitacora(self):
        RegistroOperacion.objects.create(fecha_hora=D, usuario=self.op, accion="MODIFICAR", entidad="PROPIETARIO", entidad_id=self.ana.pk, descripcion="Cambió el celular", detalle={"telefono": ["3001112233", "3001234567"]})
        self.falla(lambda: RegistroOperacion.objects.create(fecha_hora=D, usuario=self.op, accion="BORRAR", entidad="PROPIETARIO", entidad_id=1, descripcion="x"))


class HorarioDominioTests(TestCase):
    """Métodos de dominio de HorarioOperador (CL-03)."""

    def setUp(self):
        self.op = Usuario.objects.create_user("op", password="x")

    def franja(self, dia, inicio, fin):
        return HorarioOperador(operador=self.op, dia_semana=dia, hora_inicio=time(*inicio), hora_fin=time(*fin))

    def test_franja_diurna(self):
        lunes = self.franja(1, (6, 0), (14, 0))  # 16/11/2026 es lunes
        self.assertTrue(lunes.cubre(fh("2026-11-16 06:00")))
        self.assertFalse(lunes.cubre(fh("2026-11-16 14:00")))
        self.assertFalse(lunes.cubre(fh("2026-11-17 08:00")))
        self.assertEqual(lunes.fin_en(fh("2026-11-16 10:00")), fh("2026-11-16 14:00"))

    def test_franja_nocturna(self):
        viernes = self.franja(5, (22, 0), (6, 0))  # viernes 20/11 22:00 a sábado 21/11 06:00
        self.assertTrue(viernes.cubre(fh("2026-11-20 23:00")))
        self.assertTrue(viernes.cubre(fh("2026-11-21 05:59")))
        self.assertFalse(viernes.cubre(fh("2026-11-21 06:00")))
        self.assertEqual(viernes.fin_en(fh("2026-11-20 23:00")), fh("2026-11-21 06:00"))

    def test_franja_hasta_medianoche(self):
        tarde = self.franja(1, (12, 0), (0, 0))
        self.assertTrue(tarde.cubre(fh("2026-11-16 23:59")))
        self.assertFalse(tarde.cubre(fh("2026-11-17 00:00")))
        self.assertEqual(tarde.fin_en(fh("2026-11-16 13:00")), fh("2026-11-17 00:00"))

    def test_rn37_cruce(self):
        self.assertTrue(self.franja(2, (6, 0), (12, 0)).se_cruza_con(self.franja(2, (10, 0), (14, 0))))
        self.assertFalse(self.franja(2, (6, 0), (10, 0)).se_cruza_con(self.franja(2, (16, 0), (20, 0))))
        self.assertFalse(self.franja(2, (6, 0), (10, 0)).se_cruza_con(self.franja(2, (10, 0), (14, 0))))  # contiguas
        self.assertTrue(self.franja(5, (22, 0), (6, 0)).se_cruza_con(self.franja(6, (5, 0), (9, 0))))    # nocturna
        self.assertTrue(self.franja(7, (22, 0), (6, 0)).se_cruza_con(self.franja(1, (5, 0), (9, 0))))    # domingo → lunes
