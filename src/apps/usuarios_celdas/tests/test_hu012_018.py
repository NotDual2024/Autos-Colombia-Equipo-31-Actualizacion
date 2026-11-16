"""Criterios de aceptación de HU-012 a HU-018."""
from datetime import timedelta

from django.urls import reverse

from apps.bitacora.models import RegistroOperacion
from apps.core.errores import ErrorNegocio
from apps.demo import fabricas as f
from apps.demo.pruebas_base import PruebaConReloj, fh
from apps.entradas_salidas import services as estadias
from apps.usuarios_celdas import selectors, services
from apps.usuarios_celdas.models import HistorialPropiedad, Propietario, SolicitudCambioPropietario

DATOS_LAURA = {"nombre_completo": "Laura Méndez", "numero_documento": "1023456789", "telefono": "3001234567",
               "correo": "laura@correo.co", "direccion": "Calle 10 # 20-30"}
DATOS_VEHICULO = {"tipo": "CARRO", "marca": "Mazda", "nombre": "3", "modelo": "2021", "color": "Blanco"}


class HU012RegistrarPropietario(PruebaConReloj):
    def test_registro_correcto_y_bitacora(self):
        p = services.registrar_propietario(DATOS_LAURA, self.operador)
        self.assertTrue(p.activo)
        op = RegistroOperacion.objects.get(entidad="PROPIETARIO", entidad_id=p.pk)
        self.assertEqual((op.accion, op.usuario), ("CREAR", self.operador))

    def test_cedula_repetida(self):
        services.registrar_propietario(DATOS_LAURA, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "Ya existe un propietario con esa cédula"):
            services.registrar_propietario({**DATOS_LAURA, "nombre_completo": "Otra"}, self.operador)

    def test_celular_invalido(self):
        with self.assertRaisesMessage(ErrorNegocio, "El celular debe tener 10 dígitos y empezar por 3"):
            services.registrar_propietario({**DATOS_LAURA, "telefono": "6012345678"}, self.operador)

    def test_datos_incompletos_o_correo_invalido(self):
        with self.assertRaises(ErrorNegocio):
            services.registrar_propietario({**DATOS_LAURA, "direccion": ""}, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "correo"):
            services.registrar_propietario({**DATOS_LAURA, "correo": "laura@"}, self.operador)

    def test_pantalla(self):
        self.ingresar()
        r = self.client.post(reverse("usuarios_celdas:propietario_nuevo"), DATOS_LAURA, follow=True)
        self.assertContains(r, "Propietario Laura Méndez registrado")
        r = self.client.post(reverse("usuarios_celdas:propietario_nuevo"), {**DATOS_LAURA, "telefono": "123"})
        self.assertContains(r, "El celular debe tener 10 dígitos")


class HU013RegistrarVehiculo(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.laura = services.registrar_propietario(DATOS_LAURA, self.operador)

    def test_registro_correcto_normaliza_placa(self):
        v = services.registrar_vehiculo("jtr 625", DATOS_VEHICULO, self.laura, self.operador)
        self.assertEqual((v.placa, v.activo), ("JTR625", True))
        self.assertIn(v, self.laura.vehiculos.all())

    def test_placa_que_no_corresponde_al_tipo(self):
        with self.assertRaisesMessage(ErrorNegocio, "La placa no corresponde al tipo de vehículo"):
            services.registrar_vehiculo("ABC123", {**DATOS_VEHICULO, "tipo": "MOTO"}, self.laura, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "La placa no corresponde al tipo de vehículo"):
            services.registrar_vehiculo("ABC12D", DATOS_VEHICULO, self.laura, self.operador)
        moto = services.registrar_vehiculo("XYZ12D", {**DATOS_VEHICULO, "tipo": "MOTO"}, self.laura, self.operador)
        self.assertEqual(moto.placa, "XYZ12D")

    def test_placa_repetida(self):
        services.registrar_vehiculo("JTR625", DATOS_VEHICULO, self.laura, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "Ya existe un vehículo con esa placa"):
            services.registrar_vehiculo("JTR625", DATOS_VEHICULO, self.laura, self.operador)

    def test_propietario_inactivo(self):
        services.cambiar_estado_propietario(self.laura, False, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "El propietario está inactivo"):
            services.registrar_vehiculo("JTR625", DATOS_VEHICULO, self.laura, self.operador)

    def test_modelo_fuera_de_rango(self):
        with self.assertRaisesMessage(ErrorNegocio, "entre 1950"):
            services.registrar_vehiculo("JTR625", {**DATOS_VEHICULO, "modelo": "1940"}, self.laura, self.operador)

    def test_pantalla_busca_propietario_por_cedula(self):
        self.ingresar()
        r = self.client.get(reverse("usuarios_celdas:vehiculo_nuevo"), {"documento": "1023456789"})
        self.assertContains(r, "Laura Méndez")
        r = self.client.post(reverse("usuarios_celdas:vehiculo_nuevo"), {"documento": "1023456789", "placa": "JTR625", **DATOS_VEHICULO}, follow=True)
        self.assertContains(r, "Vehículo JTR625 registrado")


class HU014Consultar(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.laura = services.registrar_propietario(DATOS_LAURA, self.operador)
        self.v = services.registrar_vehiculo("JTR625", DATOS_VEHICULO, self.laura, self.operador)
        self.ingresar()

    def test_busquedas(self):
        for texto in ("1023456789", "Méndez"):
            self.assertIn(self.laura, selectors.buscar_propietarios(texto))
        self.assertIn(self.v, selectors.buscar_vehiculos("jtr625"))
        r = self.client.get(reverse("usuarios_celdas:propietarios"), {"q": "ZZZ999"})
        self.assertContains(r, "No se encontraron resultados")

    def test_ficha_del_propietario_con_ubicacion(self):
        f.crear_pago(self.v, self.hoy + timedelta(days=10), self.admin)
        estadias.registrar_entrada("JTR625", "A-002", self.operador)
        r = self.client.get(reverse("usuarios_celdas:propietario", args=[self.laura.pk]))
        self.assertContains(r, "Dentro (A-002)")
        self.assertContains(r, "Registró al propietario")

    def test_ficha_del_vehiculo_con_historial_y_bitacora(self):
        r = self.client.get(reverse("usuarios_celdas:vehiculo", args=[self.v.pk]))
        self.assertContains(r, "Sin propietarios anteriores")
        self.assertContains(r, "Registró el vehículo JTR625")


class HU015Modificar(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.laura = services.registrar_propietario(DATOS_LAURA, self.operador)
        self.v = services.registrar_vehiculo("JTR625", DATOS_VEHICULO, self.laura, self.operador)

    def test_modificar_guarda_antes_y_despues(self):
        services.modificar_propietario(self.laura, {**DATOS_LAURA, "telefono": "3009998877"}, self.operador)
        op = RegistroOperacion.objects.filter(accion="MODIFICAR", entidad="PROPIETARIO").get()
        self.assertEqual(op.detalle, {"telefono": ["3001234567", "3009998877"]})

    def test_la_placa_no_se_edita(self):
        services.modificar_vehiculo(self.v, {**DATOS_VEHICULO, "color": "Gris", "placa": "ZZZ999"}, self.operador)
        self.v.refresh_from_db()
        self.assertEqual((self.v.placa, self.v.color), ("JTR625", "Gris"))
        self.ingresar()
        r = self.client.get(reverse("usuarios_celdas:vehiculo_editar", args=[self.v.pk]))
        self.assertContains(r, 'value="JTR625" readonly')

    def test_placa_mal_escrita_se_inactiva_y_se_registra_otra(self):
        services.cambiar_estado_vehiculo(self.v, False, self.operador)
        nuevo = services.registrar_vehiculo("JTR626", DATOS_VEHICULO, self.laura, self.operador)
        self.assertEqual(self.laura.vehiculos.count(), 2)
        self.assertFalse(self.laura.vehiculos.get(placa="JTR625").activo)
        self.assertTrue(nuevo.activo)

    def test_rn29_inactivo_dentro_sale_pero_no_entra(self):
        f.crear_pago(self.v, self.hoy + timedelta(days=10), self.admin)
        estadias.registrar_entrada("JTR625", "A-001", self.operador)
        services.cambiar_estado_propietario(self.laura, False, self.operador)
        self.AHORA = fh("2026-11-15 15:00")
        self.assertIsNotNone(estadias.registrar_salida("JTR625", self.operador).fecha_hora_salida)
        with self.assertRaisesMessage(ErrorNegocio, "INACTIVO"):
            estadias.registrar_entrada("JTR625", "A-001", self.operador)
        services.cambiar_estado_propietario(self.laura, True, self.operador)
        self.assertIsNotNone(estadias.registrar_entrada("JTR625", "A-001", self.operador))
        acciones = list(RegistroOperacion.objects.filter(entidad="PROPIETARIO").values_list("accion", flat=True))
        self.assertIn("INACTIVAR", acciones)
        self.assertIn("ACTIVAR", acciones)


class HU016y017CambioPropietario(PruebaConReloj):
    def setUp(self):
        super().setUp()
        self.laura = services.registrar_propietario(DATOS_LAURA, self.operador)
        self.andres = services.registrar_propietario({**DATOS_LAURA, "nombre_completo": "Andrés Gómez", "numero_documento": "1012345678"}, self.operador)
        self.v = services.registrar_vehiculo("JTR625", DATOS_VEHICULO, self.laura, self.operador)
        f.crear_pago(self.v, self.hoy + timedelta(days=10), self.admin)

    def test_solicitud_pendiente_no_cambia_aun(self):
        s = services.solicitar_cambio(self.v, self.andres, "Venta del vehículo", self.operador)
        self.v.refresh_from_db()
        self.assertEqual((s.estado, self.v.propietario), ("PENDIENTE", self.laura))

    def test_una_sola_pendiente_y_reglas(self):
        services.solicitar_cambio(self.v, self.andres, "Venta", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "Ya hay una solicitud pendiente para este vehículo"):
            services.solicitar_cambio(self.v, self.andres, "Otra", self.operador)
        otro = services.registrar_vehiculo("ABC123", DATOS_VEHICULO, self.laura, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "distinto"):
            services.solicitar_cambio(otro, self.laura, "x", self.operador)

    def test_aprobar_con_historial_y_pagos(self):
        s = services.solicitar_cambio(self.v, self.andres, "Venta", self.operador)
        estadias.registrar_entrada("JTR625", "A-001", self.operador)
        self.AHORA = fh("2026-11-15 16:00")
        services.aprobar_cambio(s.pk, self.admin)
        self.v.refresh_from_db()
        self.assertEqual(self.v.propietario, self.andres)
        historial = HistorialPropiedad.objects.get(vehiculo=self.v)
        self.assertEqual((historial.propietario, historial.hasta), (self.laura, fh("2026-11-15 16:00")))
        self.assertEqual(self.v.propietario_desde(), fh("2026-11-15 16:00"))
        self.assertEqual(self.v.pagos.count(), 1)       # los pagos siguen con el vehículo
        self.assertEqual(self.v.estadias.count(), 1)    # y las estadías también
        self.assertEqual(SolicitudCambioPropietario.objects.get().estado, "APROBADA")

    def test_rechazar_con_observacion(self):
        s = services.solicitar_cambio(self.v, self.andres, "Venta", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "observación"):
            services.rechazar_cambio(s.pk, self.admin, "")
        services.rechazar_cambio(s.pk, self.admin, "Falta el documento de traspaso")
        self.v.refresh_from_db()
        self.assertEqual(self.v.propietario, self.laura)
        self.assertEqual(SolicitudCambioPropietario.objects.get().observacion, "Falta el documento de traspaso")

    def test_solo_el_administrador_resuelve(self):
        s = services.solicitar_cambio(self.v, self.andres, "Venta", self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            services.aprobar_cambio(s.pk, self.operador)
        self.ingresar(self.operador)
        r = self.client.post(reverse("usuarios_celdas:resolver_solicitud", args=[s.pk]), {"decision": "aprobar"})
        self.assertEqual(r.status_code, 403)

    def test_pantallas(self):
        self.ingresar(self.operador)
        r = self.client.post(reverse("usuarios_celdas:solicitar_cambio", args=[self.v.pk]), {"documento": "1012345678", "motivo": "Venta"}, follow=True)
        self.assertContains(r, "Solicitud enviada")
        self.assertContains(r, "Solicitud de cambio pendiente")
        self.AHORA = fh("2026-11-15 16:00")
        self.ingresar(self.admin)
        s = SolicitudCambioPropietario.objects.get()
        r = self.client.post(reverse("usuarios_celdas:resolver_solicitud", args=[s.pk]), {"decision": "aprobar"}, follow=True)
        self.assertContains(r, "ahora es de Andrés Gómez")


class HU018MapaCeldas(PruebaConReloj):
    def test_mapa_con_placas_y_contadores(self):
        v = self.vehiculo("KLM482")
        estadias.registrar_entrada("KLM482", "A-003", self.operador)
        mapa = selectors.mapa_celdas("A", 1)
        self.assertEqual((mapa["total"], mapa["ocupadas"], mapa["libres"]), (3, 1, 2))
        self.assertIn({"codigo": "A-003", "placa": "KLM482"}, mapa["celdas"])
        self.ingresar()
        r = self.client.get(reverse("usuarios_celdas:mapa"), {"zona": "M"})
        self.assertContains(r, "M-01")
        self.assertNotContains(r, "Agregar celda")
        self.assertIsNotNone(v)
