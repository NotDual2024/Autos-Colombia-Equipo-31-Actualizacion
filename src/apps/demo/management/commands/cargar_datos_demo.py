"""Carga datos de demostración (RNF-014). Las fechas se calculan desde el día de ejecución.

Uso:  python manage.py cargar_datos_demo            (base de datos vacía)
      python manage.py cargar_datos_demo --reiniciar (BORRA todos los datos y los vuelve a cargar)
"""
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core import reloj
from apps.cuentas.models import Rol, Usuario
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
        self.stdout.write(f"  Operador:      {OPERADOR[0]} / {OPERADOR[1]}")

    def _cargar(self):
        ahora = reloj.ahora()
        hoy = ahora.date()
        admin = f.crear_usuario(*ADMIN, rol=Rol.ADMINISTRADOR)
        op = f.crear_usuario(*OPERADOR)
        op2 = f.crear_usuario(*OPERADOR_2)
        retirado = f.crear_usuario("operador_retirado", "OperadorDemo2026", "Pedro Gómez")
        retirado.is_active = False  # ejemplo de operador desactivado (RF-106)
        retirado.save(update_fields=["is_active"])
        f.crear_celdas()
        f.crear_tarifas(hoy.replace(month=1, day=1))

        def prop(nombre, cedula, activo=True):
            correo = nombre.lower().split()[0] + "." + nombre.lower().split()[1] + "@correo.co"
            correo = correo.translate(str.maketrans("áéíóúñ", "aeioun"))
            return f.crear_propietario(nombre, cedula, correo, activo)

        andres, laura, carlos = prop("Andrés Gómez", "1012345678"), prop("Laura Méndez", "1023456789"), prop("Carlos Herrera", "1034567890", activo=False)
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
