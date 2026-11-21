"""Pruebas unitarias de CalendarioCobro (RN-38, RN-39; plan iteración 3, paso 2)."""
from datetime import date

from django.test import SimpleTestCase

from apps.pagos import calendario as c


class SumarMeses(SimpleTestCase):
    def test_mismo_dia_del_mes_siguiente(self):
        self.assertEqual(c.sumar_meses(date(2026, 11, 18), 1), date(2026, 12, 18))

    def test_31_pasa_al_ultimo_dia_y_vuelve_al_31(self):
        ancla = date(2027, 1, 31)
        self.assertEqual(c.sumar_meses(ancla, 1), date(2027, 2, 28))
        self.assertEqual(c.sumar_meses(ancla, 2), date(2027, 3, 31))
        self.assertEqual(c.sumar_meses(ancla, 3), date(2027, 4, 30))

    def test_anio_bisiesto(self):
        self.assertEqual(c.sumar_meses(date(2028, 1, 31), 1), date(2028, 2, 29))
        self.assertEqual(c.sumar_meses(date(2028, 1, 29), 1), date(2028, 2, 29))

    def test_dia_30(self):
        ancla = date(2027, 1, 30)
        self.assertEqual(c.sumar_meses(ancla, 1), date(2027, 2, 28))
        self.assertEqual(c.sumar_meses(ancla, 2), date(2027, 3, 30))

    def test_cambio_de_anio_y_meses_negativos(self):
        self.assertEqual(c.sumar_meses(date(2026, 12, 18), 1), date(2027, 1, 18))
        self.assertEqual(c.sumar_meses(date(2026, 11, 18), 12), date(2027, 11, 18))
        self.assertEqual(c.sumar_meses(date(2027, 1, 18), -2), date(2026, 11, 18))


class Periodos(SimpleTestCase):
    def test_primer_pago_empieza_en_el_ancla(self):
        self.assertEqual(c.siguiente_periodo(date(2026, 11, 20), None, 1), (date(2026, 11, 20), date(2026, 12, 20)))

    def test_pago_tarde_no_mueve_la_fecha(self):
        # RN-39: vence el 18/11 y se paga el 20/11 -> cubre 18/11 a 18/12
        self.assertEqual(c.siguiente_periodo(date(2026, 8, 18), date(2026, 11, 18), 1), (date(2026, 11, 18), date(2026, 12, 18)))

    def test_fin_de_mes_se_calcula_desde_el_ancla(self):
        # Ancla 31/12/2026; último vencimiento 31/01/2027; 2 meses -> pasa por 28/02 y termina el 31/03
        self.assertEqual(c.siguiente_periodo(date(2026, 12, 31), date(2027, 1, 31), 2), (date(2027, 1, 31), date(2027, 3, 31)))
        # Desde 28/02 (vencimiento recortado) vuelve al 31
        self.assertEqual(c.siguiente_periodo(date(2026, 12, 31), date(2027, 2, 28), 1), (date(2027, 2, 28), date(2027, 3, 31)))


class MesesPendientes(SimpleTestCase):
    def test_al_dia_o_vence_hoy(self):
        self.assertEqual(c.meses_pendientes(date(2026, 1, 18), date(2026, 12, 18), date(2026, 11, 20)), 0)
        self.assertEqual(c.meses_pendientes(date(2026, 1, 20), date(2026, 11, 20), date(2026, 11, 20)), 0)

    def test_cuatro_meses_atrasados(self):
        # HU-024: venció el 18/08 y hoy es 20/11 -> debe 4 meses (hasta el 18/12)
        self.assertEqual(c.meses_pendientes(date(2026, 1, 18), date(2026, 8, 18), date(2026, 11, 20)), 4)

    def test_un_mes(self):
        self.assertEqual(c.meses_pendientes(date(2026, 1, 15), date(2026, 11, 15), date(2026, 11, 20)), 1)
