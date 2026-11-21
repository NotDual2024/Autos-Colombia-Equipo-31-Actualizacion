"""Escenarios de HU-024 a HU-032 (iteración 3: gestión de pagos).

Hoy en las pruebas: domingo 15/11/2026 14:35 (PruebaConReloj). Tarifas: carro 150 000, moto 80 000.
"""
from datetime import date, timedelta

from django.urls import reverse

from apps.bitacora.models import Accion, Entidad, RegistroOperacion
from apps.core.errores import ErrorNegocio
from apps.demo import fabricas as f
from apps.demo.pruebas_base import PruebaConReloj
from apps.notificaciones import services as avisos
from apps.pagos import registro, selectors, services as vigencia, tarifas
from apps.pagos.models import CorreoConfirmacion, Descuento, EstadoPago, Pago, Tarifa
from apps.usuarios_celdas import services as clientes


class BasePagos(PruebaConReloj):
    def setUp(self):
        super().setUp()
        f.crear_tarifas(date(2026, 1, 1))

    def registrar(self, v, meses=1, medio="EFECTIVO", descuento=None, usuario=None):
        return registro.registrar(v, meses, medio, descuento.pk if descuento else None, usuario or self.operador)

    def descuento(self, porcentaje=10, descripcion="Cliente frecuente", habilitado=True):
        return Descuento.objects.create(descripcion=descripcion, porcentaje=porcentaje, habilitado=habilitado,
                                        creado_por=self.admin, fecha_creacion=self.AHORA)


# ====================================================================== HU-024
class HU024RegistrarPago(BasePagos):
    def test_primer_pago(self):
        v = self.vehiculo(vigente=False)
        r = self.registrar(v)
        p = r.pago
        self.assertEqual((p.periodo_inicio, p.periodo_fin, p.valor), (date(2026, 11, 15), date(2026, 12, 15), 150000))
        self.assertEqual(vigencia.dia_cobro(v), 15)
        self.assertEqual(p.numero_factura, 1)
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.CREAR, entidad=Entidad.PAGO, entidad_id=p.pk,
                                                         usuario=self.operador).exists())

    def test_resumen_antes_de_confirmar(self):
        v = self.vehiculo(vigente=False)
        self.ingresar()
        r = self.client.get(reverse("pagos:registrar"), {"placa": "abc123", "meses": "1"})
        self.assertContains(r, "15/11/2026 → 15/12/2026")
        self.assertContains(r, "150 000 COP")
        self.assertContains(r, v.propietario.nombre_completo)
        self.assertEqual(Pago.objects.count(), 0)

    def test_pagar_tarde_no_mueve_el_dia_de_cobro(self):
        v = self.vehiculo(fin=date(2026, 11, 13))
        p = self.registrar(v).pago
        self.assertEqual((p.periodo_inicio, p.periodo_fin), (date(2026, 11, 13), date(2026, 12, 13)))

    def test_fin_de_mes(self):
        v = self.vehiculo(fin=date(2027, 1, 31))  # primer pago 31/12/2026 -> día de cobro 31
        p = self.registrar(v, meses=2).pago
        self.assertEqual((p.periodo_inicio, p.periodo_fin), (date(2027, 1, 31), date(2027, 3, 31)))
        self.assertEqual(vigencia.dia_cobro(v), 31)

    def test_varios_meses_atrasados(self):
        v = self.vehiculo(fin=date(2026, 8, 15))
        self.assertEqual(vigencia.estado(v, self.hoy).meses_pendientes, 3)
        self.ingresar()
        self.assertContains(self.client.get(reverse("pagos:registrar"), {"placa": "ABC123"}), "Debe 3 meses para quedar al día")
        r = self.registrar(v, meses=1)
        self.assertEqual((r.pago.periodo_inicio, r.pago.periodo_fin), (date(2026, 8, 15), date(2026, 9, 15)))
        self.assertIn("debe 2 meses más", r.advertencias[0])

    def test_varios_meses_en_un_pago(self):
        v = self.vehiculo(vigente=False)
        self.assertEqual(self.registrar(v, meses=3).pago.valor, 450000)
        for meses in (0, 13, "x"):
            with self.assertRaisesMessage(ErrorNegocio, "entre 1 y 12"):
                registro.preparar(v, meses)

    def test_aplicar_descuento(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v, meses=3, descuento=self.descuento(10)).pago
        self.assertEqual((p.valor_bruto, p.porcentaje_descuento, p.valor_descuento(), p.valor), (450000, 10, 45000, 405000))

    def test_descuento_deshabilitado_se_rechaza(self):
        v = self.vehiculo(vigente=False)
        with self.assertRaisesMessage(ErrorNegocio, "ya no está habilitado"):
            self.registrar(v, descuento=self.descuento(habilitado=False))

    def test_el_valor_no_se_escribe_a_mano(self):
        self.vehiculo(vigente=False)
        self.ingresar()
        self.client.post(reverse("pagos:registrar"), {"placa": "ABC123", "meses": "1", "medio": "EFECTIVO", "valor": "1"})
        self.assertEqual(Pago.objects.get().valor, 150000)

    def test_medio_de_pago_obligatorio(self):
        v = self.vehiculo(vigente=False)
        with self.assertRaisesMessage(ErrorNegocio, "medio de pago"):
            self.registrar(v, medio="")
        self.ingresar()
        r = self.client.post(reverse("pagos:registrar"), {"placa": "ABC123", "meses": "1", "medio": ""})
        self.assertContains(r, "Elige el medio de pago")
        self.assertEqual(Pago.objects.count(), 0)

    def test_vehiculo_dentro_vencido_sale_del_proceso_de_retiro(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=3))
        f.crear_estadia(v, "A-001", self.AHORA - timedelta(days=5), self.operador)
        self.assertEqual([x.vehiculo for x in avisos.vencidos_dentro()], [v])
        self.registrar(v)
        self.assertEqual(avisos.vencidos_dentro(), [])

    def test_confirmacion_al_propietario(self):
        v = self.vehiculo(vigente=False)
        r = self.registrar(v)
        correo = CorreoConfirmacion.objects.get(pago=r.pago)
        self.assertEqual((correo.destinatario, correo.resultado), ("ana.gil@correo.co", "ENVIADO_SIMULADO"))
        self.assertIn("15/11/2026 a 15/12/2026", correo.cuerpo)
        self.assertTrue(r.correo_enviado)

    def test_flujo_en_pantalla(self):
        self.vehiculo(vigente=False)
        self.ingresar()
        r = self.client.post(reverse("pagos:registrar"), {"placa": "ABC123", "meses": "2", "medio": "TARJETA"}, follow=True)
        self.assertContains(r, "Pago registrado · Factura N.º 000001")
        self.assertContains(r, "Se envió un correo simulado a ana.gil@correo.co")
        self.assertContains(r, "Imprimir factura")

    def test_sin_tarifa_vigente(self):
        Tarifa.objects.all().delete()
        with self.assertRaisesMessage(ErrorNegocio, "No hay una tarifa vigente"):
            self.registrar(self.vehiculo(vigente=False))

    def test_numeros_de_factura_consecutivos(self):
        a, b = self.vehiculo(vigente=False), self.vehiculo("DEF456", vigente=False)
        self.assertEqual([self.registrar(a).pago.numero_factura, self.registrar(b).pago.numero_factura], [1, 2])


# ====================================================================== HU-025
class HU025Vigencia(BasePagos):
    def test_al_dia(self):
        v = self.vehiculo(fin=self.hoy + timedelta(days=10))
        e = vigencia.estado(v, self.hoy)
        self.assertEqual((e.texto, e.vencimiento, e.dia_cobro), ("Al día", date(2026, 11, 25), 25))
        self.ingresar()
        r = self.client.get(reverse("pagos:vehiculo", args=[v.pk]))
        self.assertContains(r, "Al día")
        self.assertContains(r, "25/11/2026")

    def test_vence_hoy_todavia_puede_entrar(self):
        v = self.vehiculo(fin=self.hoy)
        self.assertEqual(vigencia.estado(v, self.hoy).texto, "Vence hoy")
        self.assertTrue(vigencia.esta_vigente(v, self.hoy))

    def test_vencida(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=5))
        e = vigencia.estado(v, self.hoy)
        self.assertEqual((e.texto, e.meses_pendientes), ("Vencida hace 5 días", 1))

    def test_sin_pagos(self):
        v = self.vehiculo(vigente=False)
        e = vigencia.estado(v, self.hoy)
        self.assertEqual(e.texto, "Sin pagos")
        self.assertFalse(e.puede_entrar)

    def test_pago_corregido_no_cuenta_para_la_entrada_ni_los_avisos(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v).pago
        Pago.objects.filter(pk=p.pk).update(estado=EstadoPago.CORREGIDO, motivo_correccion="Error", corregido_por=self.admin,
                                            fecha_correccion=self.AHORA)
        self.assertFalse(vigencia.esta_vigente(v, self.hoy))
        self.assertIsNone(vigencia.ultimo_pago(v))


# ====================================================================== HU-026
class HU026HistorialYFactura(BasePagos):
    def test_historial_de_un_vehiculo(self):
        v = self.vehiculo(vigente=False)
        p1 = self.registrar(v).pago
        self.AHORA += timedelta(days=1)
        p2 = self.registrar(v).pago
        self.assertEqual(list(selectors.historial_vehiculo(v)), [p2, p1])

    def test_historial_de_un_propietario(self):
        a, b = self.vehiculo(vigente=False), self.vehiculo("DEF456", vigente=False)
        self.registrar(a)
        self.registrar(b)
        self.ingresar()
        r = self.client.get(reverse("pagos:propietario", args=[self.prop.pk]))
        self.assertContains(r, "ABC123")
        self.assertContains(r, "DEF456")

    def test_pago_corregido_en_el_historial(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v).pago
        nuevo = registro.corregir(p.pk, "Eran 2 meses", 2, "EFECTIVO", None, self.operador).pago
        self.ingresar()
        r = self.client.get(reverse("pagos:vehiculo", args=[v.pk]))
        self.assertContains(r, "Corregido")
        self.assertContains(r, "Eran 2 meses")
        self.assertContains(r, f"→ {nuevo.numero_factura_texto}")

    def test_imprimir_factura(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v, meses=3, descuento=self.descuento(10)).pago
        self.ingresar()
        r = self.client.get(reverse("pagos:factura", args=[p.numero_factura]))
        for texto in ("SIMULACIÓN – SIN VALIDEZ FISCAL", "Factura N.º 000001", "Parqueadero Autos Colombia", "Ana Gil",
                      "1045678901", "ABC123", "15/11/2026 – 15/02/2027", "450 000", "45 000", "405 000", "Efectivo",
                      "María Rodríguez", "@media print", "window.print()"):
            self.assertContains(r, texto)

    def test_factura_inexistente(self):
        self.ingresar()
        self.assertEqual(self.client.get(reverse("pagos:factura", args=[999])).status_code, 404)


# ====================================================================== HU-027
class HU027Tarifas(BasePagos):
    def test_tarifa_nueva_con_fecha_futura(self):
        tarifas.registrar_tarifa(self.admin, "CARRO_CAMIONETA", "160000", date(2027, 1, 1))
        v = self.vehiculo(vigente=False)
        self.assertEqual(self.registrar(v).pago.valor, 150000)
        self.AHORA = self.AHORA.replace(year=2027, month=1, day=2)
        otro = self.vehiculo("DEF456", vigente=False)
        self.assertEqual(self.registrar(otro).pago.valor, 160000)
        self.assertEqual(Pago.objects.get(vehiculo=v).valor, 150000)  # los pagos anteriores no cambian
        self.assertTrue(RegistroOperacion.objects.filter(entidad=Entidad.TARIFA, accion=Accion.CREAR).exists())

    def test_fecha_repetida(self):
        tarifas.registrar_tarifa(self.admin, "MOTO", 90000, date(2027, 1, 1))
        with self.assertRaisesMessage(ErrorNegocio, "Ya existe una tarifa de moto desde esa fecha"):
            tarifas.registrar_tarifa(self.admin, "MOTO", 95000, date(2027, 1, 1))

    def test_pantalla_sin_edicion(self):
        self.ingresar(self.admin)
        r = self.client.post(reverse("pagos:tarifas"), {"categoria": "MOTO", "valor": "85000", "vigente_desde": "2027-02-01"}, follow=True)
        self.assertContains(r, "Programada")
        self.assertNotContains(r, "Editar")

    def test_solo_el_administrador(self):
        self.ingresar()
        self.assertEqual(self.client.get(reverse("pagos:tarifas")).status_code, 403)
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            tarifas.registrar_tarifa(self.operador, "MOTO", 90000, date(2027, 1, 1))


# ====================================================================== HU-028
class HU028InactivacionYReactivacion(BasePagos):
    def test_motivo_obligatorio(self):
        v = self.vehiculo()
        with self.assertRaisesMessage(ErrorNegocio, "motivo"):
            clientes.cambiar_estado_vehiculo(v, False, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "descripción"):
            clientes.cambiar_estado_vehiculo(v, False, self.operador, "OTRO", "  ")

    def test_el_motivo_se_ve_en_la_ficha(self):
        v = self.vehiculo()
        self.ingresar()
        self.client.post(reverse("usuarios_celdas:vehiculo_estado", args=[v.pk]), {"activo": "0", "motivo": "FALTA_PAGO"})
        v.refresh_from_db()
        self.assertEqual((v.activo, v.motivo_inactivacion), (False, "FALTA_PAGO"))
        r = self.client.get(reverse("usuarios_celdas:vehiculo", args=[v.pk]))
        self.assertContains(r, "Inactivo: Falta de pago")
        self.assertContains(r, "María Rodríguez")

    def test_reactivacion_al_pagar(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=3))
        clientes.cambiar_estado_vehiculo(v, False, self.operador, "FALTA_PAGO")
        r = self.registrar(v)
        v.refresh_from_db()
        self.assertTrue(v.activo)
        self.assertIsNone(v.motivo_inactivacion)
        self.assertEqual(r.reactivados, ["el vehículo ABC123"])
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.ACTIVAR, entidad=Entidad.VEHICULO,
                                                         descripcion__contains="automáticamente").exists())

    def test_propietario_inactivo_por_falta_de_pago(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=3))
        clientes.cambiar_estado_propietario(self.prop, False, self.operador, "FALTA_PAGO")
        self.registrar(v)
        self.prop.refresh_from_db()
        self.assertTrue(self.prop.activo)

    def test_inactivo_por_otro_motivo(self):
        v = self.vehiculo(fin=self.hoy - timedelta(days=3))
        clientes.cambiar_estado_vehiculo(v, False, self.operador, "OTRO", "Vehículo vendido")
        r = self.registrar(v)
        v.refresh_from_db()
        self.assertFalse(v.activo)
        self.assertIn("debe activarse a mano", r.advertencias[0])

    def test_pago_que_no_deja_al_dia_no_reactiva(self):
        v = self.vehiculo(fin=date(2026, 8, 15))
        clientes.cambiar_estado_vehiculo(v, False, self.operador, "FALTA_PAGO")
        self.registrar(v, meses=1)
        v.refresh_from_db()
        self.assertFalse(v.activo)

    def test_el_sistema_no_inactiva_por_su_cuenta(self):
        v = self.vehiculo(fin=date(2026, 6, 15))
        avisos.enviar_automaticos()
        v.refresh_from_db()
        self.assertTrue(v.activo)


# ====================================================================== HU-029
class HU029CorregirPago(BasePagos):
    def test_correccion_dentro_de_las_24_horas(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v).pago
        self.AHORA += timedelta(hours=2)
        nuevo = registro.corregir(p.pk, "Eran 2 meses", 2, "EFECTIVO", None, self.operador).pago
        p.refresh_from_db()
        self.assertEqual((p.estado, p.motivo_correccion, p.corregido_por), (EstadoPago.CORREGIDO, "Eran 2 meses", self.operador))
        self.assertEqual((nuevo.corrige_a, nuevo.periodo_inicio, nuevo.periodo_fin), (p, date(2026, 11, 15), date(2027, 1, 15)))
        self.assertEqual(vigencia.ultimo_pago(v), nuevo)
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.CORREGIR_PAGO, entidad_id=p.pk).exists())

    def test_motivo_obligatorio(self):
        p = self.registrar(self.vehiculo(vigente=False)).pago
        with self.assertRaisesMessage(ErrorNegocio, "motivo"):
            registro.corregir(p.pk, " ", 2, "EFECTIVO", None, self.operador)

    def test_operador_despues_de_24_horas(self):
        p = self.registrar(self.vehiculo(vigente=False)).pago
        self.AHORA += timedelta(hours=25)
        with self.assertRaisesMessage(ErrorNegocio, "Este pago solo lo puede corregir el administrador"):
            registro.corregir(p.pk, "x", 2, "EFECTIVO", None, self.operador)
        self.ingresar()
        self.assertContains(self.client.get(reverse("pagos:corregir", args=[p.pk])), "Este pago solo lo puede corregir el administrador")

    def test_administrador_en_cualquier_momento(self):
        p = self.registrar(self.vehiculo(vigente=False)).pago
        self.AHORA += timedelta(days=10)
        registro.corregir(p.pk, "Medio equivocado", 1, "TRANSFERENCIA", None, self.admin)
        p.refresh_from_db()
        self.assertEqual(p.estado, EstadoPago.CORREGIDO)

    def test_un_pago_corregido_no_se_vuelve_a_corregir(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v).pago
        registro.corregir(p.pk, "x", 2, "EFECTIVO", None, self.operador)
        with self.assertRaisesMessage(ErrorNegocio, "ya fue corregido"):
            registro.corregir(p.pk, "y", 3, "EFECTIVO", None, self.operador)
        self.ingresar()
        self.assertNotContains(self.client.get(reverse("pagos:vehiculo", args=[v.pk])), reverse("pagos:corregir", args=[p.pk]))

    def test_solo_el_ultimo_pago(self):
        v = self.vehiculo(vigente=False)
        p1 = self.registrar(v).pago
        self.registrar(v)
        with self.assertRaisesMessage(ErrorNegocio, "último pago registrado"):
            registro.corregir(p1.pk, "x", 2, "EFECTIVO", None, self.admin)

    def test_factura_del_pago_corregido(self):
        p = self.registrar(self.vehiculo(vigente=False)).pago
        nuevo = registro.corregir(p.pk, "Eran 2 meses", 2, "EFECTIVO", None, self.operador).pago
        self.ingresar()
        r = self.client.get(reverse("pagos:factura", args=[p.numero_factura]))
        self.assertContains(r, f"ANULADA – reemplazada por la factura N.º {nuevo.numero_factura_texto}")

    def test_flujo_en_pantalla(self):
        v = self.vehiculo(vigente=False)
        p = self.registrar(v).pago
        self.ingresar()
        r = self.client.post(reverse("pagos:corregir", args=[p.pk]), {"meses": "2", "medio": "EFECTIVO", "descuento": "",
                                                                      "motivo": "Eran 2 meses"}, follow=True)
        self.assertContains(r, "Reemplaza a la factura N.º 000001")
        self.assertEqual(Pago.objects.filter(vehiculo=v, estado=EstadoPago.REGISTRADO).get().valor, 300000)


# ====================================================================== HU-030
class HU030PorVencer(BasePagos):
    def test_lista_de_por_vencer(self):
        cerca = self.vehiculo("ABC123", fin=self.hoy + timedelta(days=3))
        self.vehiculo("XYZ789", fin=self.hoy + timedelta(days=10))
        hoy_mismo = self.vehiculo("JTR625", fin=self.hoy)
        self.assertEqual([x.vehiculo for x in selectors.por_vencer(self.hoy)], [hoy_mismo, cerca])
        self.ingresar()
        r = self.client.get(reverse("pagos:por_vencer"))
        self.assertContains(r, "ABC123")
        self.assertContains(r, "3001234567")
        self.assertContains(r, "Vence hoy")
        self.assertNotContains(r, "XYZ789")

    def test_solo_vehiculos_activos(self):
        v = self.vehiculo(fin=self.hoy + timedelta(days=2))
        clientes.cambiar_estado_vehiculo(v, False, self.operador, "OTRO", "Vendido")
        self.assertEqual(selectors.por_vencer(self.hoy), [])


# ====================================================================== HU-031
class HU031Descuentos(BasePagos):
    def test_crear_descuento(self):
        d = tarifas.crear_descuento(self.admin, "Cliente frecuente", "10")
        self.assertTrue(d.habilitado)
        self.assertTrue(RegistroOperacion.objects.filter(entidad=Entidad.DESCUENTO, accion=Accion.CREAR, usuario=self.admin).exists())

    def test_porcentaje_invalido(self):
        for p in ("0", "120", "diez"):
            with self.assertRaisesMessage(ErrorNegocio, "El porcentaje debe estar entre 1 y 100"):
                tarifas.crear_descuento(self.admin, "x", p)

    def test_deshabilitar(self):
        d = tarifas.crear_descuento(self.admin, "Cliente frecuente", 10)
        p = self.registrar(self.vehiculo(vigente=False), descuento=d).pago
        tarifas.cambiar_estado_descuento(self.admin, d, False)
        self.assertNotIn(d, tarifas.habilitados())
        p.refresh_from_db()
        self.assertEqual((p.porcentaje_descuento, p.valor), (10, 135000))
        self.assertTrue(RegistroOperacion.objects.filter(accion=Accion.DESHABILITAR).exists())

    def test_no_se_edita(self):
        self.ingresar(self.admin)
        tarifas.crear_descuento(self.admin, "Cliente frecuente", 10)
        r = self.client.get(reverse("pagos:descuentos"))
        self.assertContains(r, "Deshabilitar")
        self.assertNotContains(r, "Editar")

    def test_el_operador_solo_aplica(self):
        d = tarifas.crear_descuento(self.admin, "Cliente frecuente", 10)
        self.ingresar()
        self.assertEqual(self.client.get(reverse("pagos:descuentos")).status_code, 403)
        self.assertEqual(self.client.post(reverse("pagos:descuento_estado", args=[d.pk]), {"habilitado": "0"}).status_code, 403)
        with self.assertRaisesMessage(ErrorNegocio, "Acceso denegado"):
            tarifas.crear_descuento(self.operador, "x", 5)
        self.vehiculo(vigente=False)
        self.assertContains(self.client.get(reverse("pagos:registrar"), {"placa": "ABC123"}), "Cliente frecuente (10 %)")


# ====================================================================== HU-032
class HU032Ingresos(BasePagos):
    def test_ingresos_del_mes_sin_corregidos_y_por_fecha_de_pago(self):
        a, b = self.vehiculo(vigente=False), self.vehiculo("XYZ12D", tipo="MOTO", vigente=False)
        self.registrar(a, meses=3)                                      # 450 000, carro, efectivo
        p = self.registrar(b, medio="TARJETA").pago                     # 80 000 -> se corrige
        registro.corregir(p.pk, "Eran 2 meses", 2, "TARJETA", None, self.operador)  # 160 000
        informe = selectors.ingresos(2026, 11)
        self.assertEqual((informe.total, informe.cantidad), (610000, 2))
        self.assertEqual({f["nombre"]: f["total"] for f in informe.por_medio}, {"Efectivo": 450000, "Transferencia": 0, "Tarjeta": 160000})
        self.assertEqual(selectors.ingresos(2026, 12).total, 0)
        self.ingresar(self.admin)
        self.assertContains(self.client.get(reverse("pagos:ingresos"), {"mes": "2026-11"}), "610 000 COP")

    def test_solo_el_administrador(self):
        self.ingresar()
        self.assertEqual(self.client.get(reverse("pagos:ingresos")).status_code, 403)
