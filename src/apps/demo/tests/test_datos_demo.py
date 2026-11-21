"""RNF-014: el comando de demostración carga datos coherentes en una base vacía."""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.cuentas.models import Usuario
from apps.entradas_salidas import selectors
from apps.notificaciones import services
from apps.usuarios_celdas.models import Celda


class DatosDemoTests(TestCase):
    def test_carga_y_escenarios_disponibles(self):
        call_command("cargar_datos_demo", stdout=StringIO())
        self.assertTrue(Usuario.objects.get(username="admin").es_administrador())
        self.assertTrue(Usuario.objects.get(username="operador").check_password("OperadorDemo2026"))
        self.assertEqual((Celda.objects.filter(tipo="CARRO_CAMIONETA").count(), Celda.objects.filter(tipo="MOTO").count()), (150, 50))
        self.assertGreaterEqual(selectors.vehiculos_dentro().count(), 10)
        dias = sorted(fila.dias_vencido for fila in services.vencidos_dentro())
        self.assertEqual(dias, [0, 3, 9])  # vence hoy, en plazo y plazo vencido
        # Iteración 2: horarios, solicitud pendiente, historial y bitácora
        from apps.bitacora.models import RegistroOperacion
        from apps.usuarios_celdas.models import HistorialPropiedad, SolicitudCambioPropietario
        self.assertEqual(Usuario.objects.get(username="operador").horarios.count(), 14)
        self.assertEqual(Usuario.objects.get(username="operador2").horarios.count(), 5)
        self.assertEqual(SolicitudCambioPropietario.objects.filter(estado="PENDIENTE").count(), 1)
        self.assertEqual(HistorialPropiedad.objects.count(), 1)
        self.assertGreaterEqual(RegistroOperacion.objects.count(), 3)
        # Iteración 3: descuentos, tarifa programada, pago corregido, vencido inactivo por falta de pago y por vencer
        from apps.core import reloj
        from apps.pagos import selectors as consultas, services as vigencia
        from apps.pagos.models import Descuento, Pago, Tarifa
        from apps.usuarios_celdas.models import Vehiculo
        self.assertEqual(list(Descuento.objects.order_by("descripcion").values_list("descripcion", "habilitado")),
                         [("Cliente frecuente", True), ("Promoción apertura", False)])
        self.assertTrue(Tarifa.objects.filter(vigente_desde__gt=reloj.hoy()).exists())
        self.assertEqual(Pago.objects.filter(estado="CORREGIDO").count(), 1)
        self.assertTrue(Pago.objects.filter(porcentaje_descuento=10, meses=3).exists())
        atrasado = Vehiculo.objects.get(placa="WER74D")
        self.assertEqual((atrasado.activo, atrasado.motivo_inactivacion), (False, "FALTA_PAGO"))
        self.assertEqual(vigencia.estado(atrasado, reloj.hoy()).meses_pendientes, 4)
        self.assertEqual([x.vehiculo.placa for x in consultas.por_vencer(reloj.hoy())], ["ABC123", "GHJ852"])

    def test_no_sobrescribe_sin_reiniciar(self):
        call_command("cargar_datos_demo", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("cargar_datos_demo", stdout=StringIO())
        call_command("cargar_datos_demo", "--reiniciar", stdout=StringIO())
        self.assertEqual(Usuario.objects.filter(username="admin").count(), 1)
