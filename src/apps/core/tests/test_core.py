from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from apps.core import reloj
from apps.core.correo import ENVIADO_SIMULADO, ServicioCorreoSimulado
from apps.core.errores import ErrorNegocio

BOGOTA = ZoneInfo("America/Bogota")


class RelojTests(SimpleTestCase):
    def test_ahora_esta_en_hora_de_bogota(self):
        self.assertEqual(reloj.ahora().utcoffset().total_seconds(), -5 * 3600)

    def test_hoy_se_puede_simular(self):
        fijo = datetime(2026, 11, 13, 23, 30, tzinfo=BOGOTA)
        with mock.patch("apps.core.reloj.ahora", return_value=fijo):
            self.assertEqual(reloj.hoy().isoformat(), "2026-11-13")


class CorreoSimuladoTests(SimpleTestCase):
    def test_envio_simulado_no_falla_y_devuelve_resultado(self):
        self.assertEqual(ServicioCorreoSimulado().enviar("a@b.co", "Asunto", "Cuerpo"), ENVIADO_SIMULADO)


class ErrorNegocioTests(SimpleTestCase):
    def test_conserva_el_mensaje(self):
        self.assertEqual(ErrorNegocio("Mensualidad no vigente").mensaje, "Mensualidad no vigente")
