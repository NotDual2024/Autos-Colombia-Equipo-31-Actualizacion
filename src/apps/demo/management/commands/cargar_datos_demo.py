"""Carga datos de demostración (RNF-014). Las fechas se calculan desde el día de ejecución.

Uso:  python manage.py cargar_datos_demo            (base de datos vacía)
      python manage.py cargar_datos_demo --reiniciar (BORRA todos los datos y los vuelve a cargar)
"""
from datetime import time, timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core import reloj
from apps.cuentas.models import HorarioOperador, Rol, Usuario
from apps.usuarios_celdas import services as clientes
from apps.pagos import registro, tarifas
from apps.pagos.calendario import sumar_meses
from apps.pagos.models import MedioPago
from apps.usuarios_celdas import celdas
from apps.usuarios_celdas.models import Categoria, Celda, HistorialPropiedad, MotivoInactivacion
from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.demo import fabricas as f
from apps.novedades.models import Novedad, NovedadEstadia

ADMIN = ("admin", "AdminDemo2026", "Laura Castillo")
OPERADOR = ("operador", "OperadorDemo2026", "María Rodríguez")
OPERADOR_2 = ("operador2", "OperadorDemo2026", "Julián Torres")


class Command(BaseCommand):
    help = "Carga usuarios de prueba, 200 celdas, propietarios, vehículos, pagos, estadías y novedades de demostración."

    def add_arguments(self, parser):
        parser.add_argument("--reiniciar", action="store_true", help="Borra TODOS los datos antes de cargar.")

    def handle(self, *args, **opciones):
        if Usuario.objects.exists():
            if not opciones["reiniciar"]:
                raise CommandError("La base de datos ya tiene datos. Use --reiniciar para borrarlos y cargar de nuevo.")
            call_command("flush", interactive=False, verbosity=0)
        with transaction.atomic():
            self._cargar()
        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))
        self.stdout.write(f"  Administrador: {ADMIN[0]} / {ADMIN[1]}")
        self.stdout.write(f"  Operador:      {OPERADOR[0]} / {OPERADOR[1]}  (turno de 24 horas)")
        self.stdout.write(f"  Operador:      {OPERADOR_2[0]} / {OPERADOR_2[1]}  (lunes a viernes 06:00-07:00)")

    def _cargar(self):
        ahora = reloj.ahora()
        hoy = ahora.date()
        admin = f.crear_usuario(*ADMIN, rol=Rol.ADMINISTRADOR)
        op = f.crear_usuario(*OPERADOR)
        op2 = f.crear_usuario(*OPERADOR_2)
        retirado = f.crear_usuario("operador_retirado", "OperadorDemo2026", "Pedro Gómez")
        retirado.is_active = False  # ejemplo de operador desactivado (RF-106)
        retirado.save(update_fields=["is_active"])
        # Horarios (plan iteración 2, sección 3): operador 24 h para probar a cualquier hora;
        # operador2 de lunes a viernes 06:00-07:00 para mostrar el bloqueo y la autorización.
        f.asignar_horario_24h(op)
        HorarioOperador.objects.bulk_create(
            [HorarioOperador(operador=op2, dia_semana=d, hora_inicio=time(6), hora_fin=time(7)) for d in range(1, 6)])
        f.crear_celdas()
        f.crear_tarifas(hoy.replace(month=1, day=1))

        def prop(nombre, cedula, activo=True):
            correo = nombre.lower().split()[0] + "." + nombre.lower().split()[1] + "@correo.co"
            correo = correo.translate(str.maketrans("áéíóúñ", "aeioun"))
            return f.crear_propietario(nombre, cedula, correo, activo)

        andres, laura = prop("Andrés Gómez", "1012345678"), prop("Laura Méndez", "1023456789")
        carlos = f.crear_propietario("Carlos Herrera", "1034567890", "carlos.herrera@correo.co", activo=False,
                                     motivo=MotivoInactivacion.OTRO, descripcion="Solicitud del cliente")
        ana, luis, sofia = prop("Ana Gil", "1045678901"), prop("Luis Mora", "1056789012"), prop("Sofía Ruiz", "1067890123")
        diego, paula = prop("Diego Pardo", "1078901234"), prop("Paula Ríos", "1089012345")

        V = f.crear_vehiculo
        klm = V(andres, "KLM482", "CARRO", "Renault", "Sandero", 2019, "Gris")
        jtr = V(laura, "JTR625", "CARRO", "Mazda", "3", 2021, "Blanco")
        mnp = V(carlos, "MNP913", "CARRO", "Chevrolet", "Onix", 2022, "Negro")
        bgt = V(andres, "BGT219", "CAMIONETA", "Toyota", "Fortuner", 2020, "Plata")
        xqh = V(ana, "XQH73F", "MOTO", "Yamaha", "NMAX", 2023, "Negro")
        rsd = V(luis, "RSD508", "CARRO", "Kia", "Picanto", 2018, "Rojo")
        dwl = V(sofia, "DWL26E", "MOTO", "Honda", "CB 190", 2022, "Azul")
        hjc = V(diego, "HJC671", "CAMIONETA", "Nissan", "Kicks", 2021, "Gris")
        jgs = V(paula, "JGS94D", "MOTO", "Suzuki", "Gixxer", 2020, "Rojo")
        pln = V(sofia, "PLN304", "CARRO", "Volkswagen", "Gol", 2017, "Blanco")
        bcd = V(diego, "BCD740", "CARRO", "Ford", "Fiesta", 2016, "Azul")
        vence_hoy = V(ana, "ABC123", "CARRO", "Chevrolet", "Spark", 2020, "Rojo")
        vencido_3 = V(luis, "QWE852", "CAMIONETA", "Mazda", "CX-5", 2022, "Azul")
        vencido_9 = V(paula, "JKL987", "CAMIONETA", "Renault", "Duster", 2019, "Verde")
        fuera_vencido = V(laura, "ZXC456", "CARRO", "Hyundai", "i10", 2015, "Negro")

        # Pagos: vigentes (vencen dentro de 15 días), uno que vence hoy, vencidos hace 3 y 9 días, y uno vencido fuera.
        for v in [klm, jtr, mnp, bgt, xqh, rsd, dwl, hjc, jgs, pln, bcd]:
            f.crear_pago(v, hoy + timedelta(days=15), admin)
        f.crear_pago(vence_hoy, hoy, op)
        f.crear_pago(vencido_3, hoy - timedelta(days=3), op)
        f.crear_pago(vencido_9, hoy - timedelta(days=9), op)
        f.crear_pago(fuera_vencido, hoy - timedelta(days=5), op)

        h = lambda horas, minutos=0: ahora - timedelta(hours=horas, minutes=minutos)  # noqa: E731
        d = lambda dias, hora, minuto=0: (ahora - timedelta(days=dias)).replace(hour=hora, minute=minuto, second=0, microsecond=0)  # noqa: E731

        # Historial cerrado (incluye una estadía que cruza la medianoche)
        e_ant1 = f.crear_estadia(klm, "A-006", d(1, 9, 0), op, d(1, 12, 40), op2)
        f.crear_estadia(klm, "A-003", d(3, 8, 30), op2, d(3, 11, 15), op2)
        f.crear_estadia(klm, "A-011", d(6, 13, 10), op, d(6, 16, 25), op)
        f.crear_estadia(rsd, "A-020", d(2, 23, 30), op, d(1, 6, 0), op2)
        f.crear_estadia(bcd, "A-040", d(4, 7, 50), op2, d(4, 18, 5), op)

        # Vehículos dentro ahora
        e_klm = f.crear_estadia(klm, "A-003", h(5, 25), op)
        f.crear_estadia(bgt, "A-001", h(5, 10), op)
        f.crear_estadia(xqh, "M-02", h(4, 30), op)
        e_rsd = f.crear_estadia(rsd, "A-005", h(3, 53), op)
        f.crear_estadia(dwl, "M-07", h(3, 15), op2)
        f.crear_estadia(hjc, "A-008", h(1, 50), op2)
        f.crear_estadia(jgs, "M-04", h(1, 30), op2)
        f.crear_estadia(pln, "A-010", h(0, 45), op)
        f.crear_estadia(vence_hoy, "A-012", d(2, 7, 40), op)
        f.crear_estadia(vencido_3, "A-015", d(5, 8, 15), op2)
        f.crear_estadia(vencido_9, "A-018", d(12, 9, 5), op)

        # Novedades (una con dos vehículos, RN-14)
        n1 = Novedad.objects.create(tipo="OBSERVACION", descripcion="Rayón leve en la puerta trasera derecha, reportado al ingreso.",
                                    fecha_hora_ocurrencia=h(5, 20), fecha_hora_registro=h(5, 15), registrado_por=op)
        NovedadEstadia.objects.create(novedad=n1, estadia=e_klm)
        n2 = Novedad.objects.create(tipo="RAYON", descripcion="El carro RSD508 rozó el guardabarros del KLM482 al parquear.",
                                    fecha_hora_ocurrencia=h(3, 40), fecha_hora_registro=h(3, 30), registrado_por=op)
        NovedadEstadia.objects.create(novedad=n2, estadia=e_klm)
        NovedadEstadia.objects.create(novedad=n2, estadia=e_rsd)
        n3 = Novedad.objects.create(tipo="OBSERVACION", descripcion="El cliente solicita apoyo para salir de la celda. Se realiza acompañamiento sin inconvenientes.",
                                    fecha_hora_ocurrencia=d(1, 12, 35), fecha_hora_registro=d(1, 12, 38), registrado_por=op)
        NovedadEstadia.objects.create(novedad=n3, estadia=e_ant1)

        # Iteración 2: historial de propietarios, solicitud pendiente y operaciones en la bitácora
        HistorialPropiedad.objects.create(vehiculo=bgt, propietario=paula, desde=ahora - timedelta(days=400), hasta=ahora - timedelta(days=60))
        bitacora.registrar(admin, Accion.APROBAR_CAMBIO, Entidad.VEHICULO, bgt.pk, "Aprobó el cambio de propietario de BGT219",
                           {"propietario": [paula.nombre_completo, andres.nombre_completo]})
        clientes.modificar_propietario(laura, {"nombre_completo": laura.nombre_completo, "numero_documento": laura.numero_documento,
                                               "telefono": "3009876543", "correo": laura.correo, "direccion": laura.direccion}, op)
        clientes.solicitar_cambio(jtr, andres, "Venta del vehículo", op)

        # Iteración 3 (plan, sección 3): descuentos, tarifa programada, pago con descuento, pago corregido,
        # vehículo vencido hace 3 meses e inactivo por falta de pago, y vehículos por vencer.
        frecuente = tarifas.crear_descuento(admin, "Cliente frecuente", 10)
        apertura = tarifas.crear_descuento(admin, "Promoción apertura", 15)
        tarifas.cambiar_estado_descuento(admin, apertura, False)
        tarifas.registrar_tarifa(admin, Categoria.CARRO_CAMIONETA, 160000, hoy.replace(year=hoy.year + 1, month=1, day=1))
        con_descuento = V(laura, "KJH205", "CARRO", "Kia", "Rio", 2021, "Gris")
        f.crear_pago(con_descuento, hoy + timedelta(days=40), op, meses=3, medio=MedioPago.TARJETA, descuento=frecuente)
        corregido = V(andres, "TYU318", "CARRO", "Renault", "Logan", 2020, "Blanco")
        mal = registro.registrar(corregido, 1, MedioPago.EFECTIVO, None, op).pago
        registro.corregir(mal.pk, "Eran 2 meses, no 1", 2, MedioPago.EFECTIVO, None, op)  # el operador puede corregir (24 h)
        atrasado = V(luis, "WER74D", "MOTO", "Bajaj", "Pulsar", 2019, "Negro")
        f.crear_pago(atrasado, sumar_meses(hoy, -3) - timedelta(days=2), op)
        clientes.cambiar_estado_vehiculo(atrasado, False, admin, MotivoInactivacion.FALTA_PAGO)
        por_vencer = V(sofia, "GHJ852", "CARRO", "Suzuki", "Swift", 2023, "Rojo")
        f.crear_pago(por_vencer, hoy + timedelta(days=3), op)

        # CHG-003: una celda en mantenimiento para mostrar la gestión de celdas y el mapa
        celdas.inactivar(admin, Celda.objects.get(codigo="A-150"), "Mantenimiento de la demarcación")
