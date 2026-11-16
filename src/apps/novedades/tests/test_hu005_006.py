"""Criterios de aceptación de HU-005 y HU-006."""
from django.urls import reverse

from apps.core.errores import ErrorNegocio
from apps.demo import fabricas as f
from apps.demo.pruebas_base import PruebaConReloj, fh
from apps.novedades import selectors, services
from apps.novedades.models import Novedad


class HU005RegistrarNovedad(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.carro = self.vehiculo("ABC123")
        self.otro = self.vehiculo("DEF456")
        self.e1 = f.crear_estadia(self.carro, "A-001", fh("2026-11-15 08:00"), self.operador)
        self.e2 = f.crear_estadia(self.otro, "A-002", fh("2026-11-15 09:00"), self.operador)

    def test_novedad_de_un_vehiculo_dentro(self):
        n = services.registrar(["abc123"], "CAIDA", fh("2026-11-15 10:00"), "Se cayó una moto encima", self.operador)
        self.assertEqual((n.fecha_hora_registro, n.registrado_por, n.vinculos.get().estadia), (self.AHORA, self.operador, self.e1))
        self.assertEqual(n.codigo, f"N-{n.pk:04d}")

    def test_una_sola_novedad_con_dos_vehiculos(self):
        n = services.registrar(["ABC123", "DEF456"], "RAYON", fh("2026-11-15 10:20"), "Rayón entre ambos", self.operador)
        self.assertEqual(Novedad.objects.count(), 1)
        self.assertEqual(n.vinculos.count(), 2)

    def test_novedad_registrada_despues_de_la_salida(self):
        moto = self.vehiculo("XYZ12D", "MOTO")
        f.crear_estadia(moto, "M-01", fh("2026-11-14 08:00"), self.operador, fh("2026-11-14 18:00"), self.operador)
        n = services.registrar(["XYZ12D"], "DANO", fh("2026-11-14 12:00"), "Daño en el espejo", self.operador)
        self.assertEqual(n.vinculos.count(), 1)

    def test_un_vehiculo_no_estaba_dentro_rechaza_todo(self):
        with self.assertRaisesMessage(ErrorNegocio, "DEF456 no estaba dentro del parqueadero a la hora indicada"):
            services.registrar(["ABC123", "DEF456"], "RAYON", fh("2026-11-15 08:30"), "Rayón", self.operador)
        self.assertEqual(Novedad.objects.count(), 0)

    def test_datos_incompletos(self):
        with self.assertRaisesMessage(ErrorNegocio, "La descripción es obligatoria"):
            services.registrar(["ABC123"], "OTRO", fh("2026-11-15 10:00"), "   ", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "Indica al menos un vehículo"):
            services.registrar([], "OTRO", fh("2026-11-15 10:00"), "x", self.operador)

    def test_hora_del_hecho_futura(self):
        with self.assertRaisesMessage(ErrorNegocio, "no puede ser posterior"):
            services.registrar(["ABC123"], "OTRO", fh("2026-11-15 15:00"), "x", self.operador)

    def test_tipo_observacion_chg002(self):
        n = services.registrar(["ABC123"], "OBSERVACION", fh("2026-11-15 10:00"), "El cliente regresa en la tarde", self.operador)
        self.assertEqual(n.get_tipo_display(), "Observación")

    def test_pantalla_y_modal_desde_salida(self):
        self.ingresar()
        siguiente = reverse("entradas_salidas:salida") + "?placa=ABC123"
        r = self.client.post(reverse("novedades:registrar"), {
            "placa_principal": "ABC123", "otras_placas": "DEF456", "tipo": "RAYON",
            "ocurrencia": "2026-11-15T10:20", "descripcion": "Rayón al parquear", "siguiente": siguiente,
        })
        self.assertRedirects(r, siguiente, fetch_redirect_response=False)
        self.assertEqual(Novedad.objects.get().vinculos.count(), 2)

    def test_pantalla_descripcion_vacia(self):
        self.ingresar()
        r = self.client.post(reverse("novedades:registrar"), {"placas": "ABC123", "tipo": "OTRO", "ocurrencia": "2026-11-15T10:20", "descripcion": ""})
        self.assertContains(r, "La descripción es obligatoria")

    def test_no_existe_opcion_de_borrar(self):
        self.ingresar(self.admin)
        r = self.client.get(reverse("novedades:lista"))
        self.assertNotContains(r, "Borrar")
        self.assertNotContains(r, "Eliminar")


class HU006ConsultarNovedades(PruebaConReloj):
    def test_novedades_por_placa_y_orden(self):
        a, b = self.vehiculo("ABC123"), self.vehiculo("DEF456")
        f.crear_estadia(a, "A-001", fh("2026-11-15 08:00"), self.operador)
        f.crear_estadia(b, "A-002", fh("2026-11-15 08:00"), self.operador)
        services.registrar(["ABC123"], "OTRO", fh("2026-11-15 09:00"), "Primera", self.operador)
        services.registrar(["ABC123", "DEF456"], "RAYON", fh("2026-11-15 11:00"), "Segunda", self.operador)
        self.assertEqual([n.descripcion for n in selectors.buscar("ABC123")], ["Segunda", "Primera"])
        resultado = list(selectors.buscar("DEF456"))
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].vinculos.count(), 2)  # muestra ambos vehículos
        self.ingresar(self.admin)
        r = self.client.get(reverse("novedades:lista"), {"placa": "DEF456"})
        self.assertContains(r, "ABC123, DEF456")
