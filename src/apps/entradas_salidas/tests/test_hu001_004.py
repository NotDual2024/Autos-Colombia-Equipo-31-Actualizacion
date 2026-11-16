"""Criterios de aceptación de HU-001 a HU-004 (servicios y pantallas)."""
from datetime import timedelta
from unittest import mock

from django.db import IntegrityError
from django.urls import reverse

from apps.core.errores import ErrorNegocio
from apps.demo import fabricas as f
from apps.demo.pruebas_base import PruebaConReloj, fh
from apps.entradas_salidas import services
from apps.entradas_salidas.models import Estadia


class HU001RegistrarEntrada(PruebaConReloj):
    def test_entrada_exitosa(self):
        v = self.vehiculo()
        e = services.registrar_entrada("abc 123", "A-002", self.operador)
        self.assertEqual((e.vehiculo, e.celda.codigo, e.usuario_entrada, e.fecha_hora_entrada), (v, "A-002", self.operador, self.AHORA))
        self.assertTrue(Estadia.objects.filter(celda__codigo="A-002", fecha_hora_salida__isnull=True).exists())

    def test_mensualidad_no_vigente(self):
        self.vehiculo(fin=self.hoy - timedelta(days=1))
        with self.assertRaisesMessage(ErrorNegocio, "Mensualidad no vigente"):
            services.registrar_entrada("ABC123", "A-001", self.operador)

    def test_vigente_el_dia_del_vencimiento(self):
        self.vehiculo(fin=self.hoy)
        self.assertIsNotNone(services.registrar_entrada("ABC123", "A-001", self.operador))

    def test_salio_vencido_y_no_puede_volver_a_entrar(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=2))
        f.crear_estadia(v, "A-001", fh("2026-11-10 08:00"), self.operador, fh("2026-11-14 08:00"), self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "Mensualidad no vigente"):
            services.registrar_entrada("ABC123", "A-001", self.operador)

    def test_vehiculo_ya_dentro(self):
        self.vehiculo()
        services.registrar_entrada("ABC123", "A-001", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "El vehículo ya se encuentra dentro"):
            services.registrar_entrada("ABC123", "A-002", self.operador)

    def test_placa_no_registrada(self):
        with self.assertRaisesMessage(ErrorNegocio, "Vehículo no registrado"):
            services.registrar_entrada("ZZZ999", "A-001", self.operador)

    def test_celda_de_tipo_incorrecto(self):
        self.vehiculo("XYZ12D", "MOTO")
        with self.assertRaisesMessage(ErrorNegocio, "La celda no corresponde al tipo de vehículo"):
            services.registrar_entrada("XYZ12D", "A-001", self.operador)

    def test_celda_ocupada(self):
        self.vehiculo()
        self.vehiculo("DEF456")
        services.registrar_entrada("ABC123", "A-001", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La celda está ocupada"):
            services.registrar_entrada("DEF456", "A-001", self.operador)

    def test_sin_celdas_disponibles(self):
        for i, placa in enumerate(["MOT11A", "MOT12B", "MOT13C"]):
            self.vehiculo(placa, "MOTO")
        services.registrar_entrada("MOT11A", "M-01", self.operador)
        services.registrar_entrada("MOT12B", "M-02", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "No hay celdas disponibles para este tipo de vehículo"):
            services.registrar_entrada("MOT13C", "M-01", self.operador)

    def test_rn24_cliente_inactivo(self):
        inactivo = f.crear_propietario("Carlos Herrera", "1034567890", "c.h@correo.co", activo=False)
        self.vehiculo("MNP913", propietario=inactivo)
        with self.assertRaisesMessage(ErrorNegocio, "El cliente está INACTIVO"):
            services.registrar_entrada("MNP913", "A-001", self.operador)

    def test_rnf003_registro_simultaneo_convertido_en_mensaje(self):
        """La base de datos rechaza el choque y el usuario ve el mensaje de negocio (no es una prueba con hilos reales)."""
        self.vehiculo()
        with mock.patch.object(Estadia.objects, "create", side_effect=IntegrityError("UNIQUE")):
            with self.assertRaisesMessage(ErrorNegocio, "La celda está ocupada"):
                services.registrar_entrada("ABC123", "A-001", self.operador)

    def test_pantalla_flujo_completo(self):
        self.vehiculo("JTR625")
        self.ingresar()
        r = self.client.get(reverse("entradas_salidas:entrada"), {"placa": "JTR625"})
        self.assertContains(r, "Datos del vehículo")
        self.assertContains(r, "3 de 3 celdas disponibles")
        r = self.client.post(reverse("entradas_salidas:entrada"), {"placa": "JTR625", "celda": "A-002"}, follow=True)
        self.assertContains(r, "Entrada registrada correctamente")
        self.assertContains(r, "en la celda A-002")

    def test_pantalla_vehiculo_ya_dentro_muestra_detalle(self):
        self.vehiculo("KLM482")
        services.registrar_entrada("KLM482", "A-003", self.operador)
        self.ingresar()
        r = self.client.get(reverse("entradas_salidas:entrada"), {"placa": "KLM482"})
        self.assertContains(r, "El vehículo ya se encuentra dentro")
        self.assertContains(r, "ocupa la celda A-003")


class HU002RegistrarSalida(PruebaConReloj):
    def test_salida_exitosa_libera_celda(self):
        v = self.vehiculo()
        f.crear_estadia(v, "A-001", fh("2026-11-15 09:10"), self.operador)
        e = services.registrar_salida("ABC123", self.admin)
        self.assertEqual((e.fecha_hora_salida, e.usuario_salida), (self.AHORA, self.admin))
        self.assertFalse(Estadia.objects.filter(celda__codigo="A-001", fecha_hora_salida__isnull=True).exists())

    def test_salida_con_mensualidad_vencida_se_permite(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=3))
        f.crear_estadia(v, "A-001", fh("2026-11-10 09:10"), self.operador)
        self.assertIsNotNone(services.registrar_salida("ABC123", self.operador).fecha_hora_salida)

    def test_estadia_que_cruza_la_medianoche(self):
        self.AHORA = fh("2026-11-16 06:00")
        v = self.vehiculo()
        f.crear_estadia(v, "A-001", fh("2026-11-15 23:30"), self.operador)
        e = services.registrar_salida("ABC123", self.operador)
        self.assertEqual((e.fecha_hora_salida - e.fecha_hora_entrada), timedelta(hours=6, minutes=30))

    def test_vehiculo_que_no_esta_dentro(self):
        self.vehiculo()
        with self.assertRaisesMessage(ErrorNegocio, "El vehículo no se encuentra dentro"):
            services.registrar_salida("ABC123", self.operador)

    def test_pantalla_salida(self):
        v = self.vehiculo("KLM482")
        f.crear_estadia(v, "A-003", fh("2026-11-15 09:10"), self.operador)
        self.ingresar()
        r = self.client.get(reverse("entradas_salidas:salida"), {"placa": "KLM482"})
        self.assertContains(r, "Entrada encontrada")
        self.assertContains(r, "5 h 25 min")
        r = self.client.post(reverse("entradas_salidas:salida"), {"placa": "KLM482"}, follow=True)
        self.assertContains(r, "Salida registrada correctamente")
        r = self.client.get(reverse("entradas_salidas:salida"), {"placa": "BCD740"})
        self.assertContains(r, "Vehículo no registrado")


class HU003Ocupacion(PruebaConReloj):
    def setUp(self):
        super().setUp()
        for placa, tipo, celda in [("AAA111", "CARRO", "A-001"), ("BBB222", "CAMIONETA", "A-002"), ("CCC33C", "MOTO", "M-01")]:
            f.crear_estadia(self.vehiculo(placa, tipo), celda, fh("2026-11-15 08:00"), self.operador)
        self.ingresar()

    def test_lista_de_vehiculos_dentro(self):
        r = self.client.get(reverse("entradas_salidas:dentro"))
        for placa in ["AAA111", "BBB222", "CCC33C"]:
            self.assertContains(r, placa)
        self.assertContains(r, "3 vehículos")

    def test_filtro_por_tipo(self):
        r = self.client.get(reverse("entradas_salidas:dentro"), {"tipo": "MOTO"})
        self.assertContains(r, "CCC33C")
        self.assertNotContains(r, "AAA111")

    def test_consultar_celda_ocupada_y_libre(self):
        r = self.client.get(reverse("entradas_salidas:dentro"), {"celda": "a-001"})
        self.assertContains(r, "Ocupada por AAA111")
        r = self.client.get(reverse("entradas_salidas:dentro"), {"celda": "M-02"})
        self.assertContains(r, "Celda M-02 disponible")


class HU004Historial(PruebaConReloj):
    def test_historial_por_rango_y_placa(self):
        v = self.vehiculo("KLM482")
        otro = self.vehiculo("DEF456")
        f.crear_estadia(v, "A-001", fh("2026-11-01 08:00"), self.operador, fh("2026-11-01 10:00"), self.operador)
        f.crear_estadia(v, "A-002", fh("2026-10-01 08:00"), self.operador, fh("2026-10-01 10:00"), self.operador)
        f.crear_estadia(otro, "A-003", fh("2026-11-02 08:00"), self.operador, fh("2026-11-02 10:00"), self.operador)
        self.ingresar(self.admin)
        r = self.client.get(reverse("entradas_salidas:historial"), {"placa": "KLM482", "desde": "2026-10-15", "hasta": "2026-11-15"})
        self.assertContains(r, "1 resultado")
        self.assertContains(r, "01/11/2026")
        self.assertNotContains(r, "01/10/2026")
        self.assertNotContains(r, "DEF456")

    def test_sin_resultados(self):
        self.ingresar(self.admin)
        r = self.client.get(reverse("entradas_salidas:historial"), {"placa": "ZZZ999"})
        self.assertContains(r, "No se encontraron resultados")
