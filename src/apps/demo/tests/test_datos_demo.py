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

    def test_no_sobrescribe_sin_reiniciar(self):
        call_command("cargar_datos_demo", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("cargar_datos_demo", stdout=StringIO())
        call_command("cargar_datos_demo", "--reiniciar", stdout=StringIO())
        self.assertEqual(Usuario.objects.filter(username="admin").count(), 1)
