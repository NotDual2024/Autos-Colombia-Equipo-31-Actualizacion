"""Funciones para crear datos de prueba y de demostración (RNF-014)."""
from datetime import date, datetime, timedelta

from apps.core import reloj
from apps.cuentas.models import Rol, Usuario
from apps.entradas_salidas.models import Estadia
from apps.pagos.models import Pago, Tarifa
from apps.usuarios_celdas.models import Categoria, Celda, Propietario, Vehiculo

TARIFAS = {Categoria.CARRO_CAMIONETA: 150000, Categoria.MOTO: 80000}  # RN-19


def crear_usuario(username: str, clave: str, nombre: str, rol: str = Rol.OPERADOR) -> Usuario:
    nombre_pila, _, apellido = nombre.partition(" ")
    return Usuario.objects.create_user(username, password=clave, first_name=nombre_pila, last_name=apellido, rol=rol)


def crear_celdas(carros: int = 150, motos: int = 50) -> None:
    """RN-20: A-001 … A-150 (carro/camioneta) y M-01 … M-50 (moto) — CHG-002."""
    Celda.objects.bulk_create(
        [Celda(codigo=f"A-{i:03d}", tipo=Categoria.CARRO_CAMIONETA) for i in range(1, carros + 1)]
        + [Celda(codigo=f"M-{i:02d}", tipo=Categoria.MOTO) for i in range(1, motos + 1)]
    )


def crear_tarifas(desde: date) -> None:
    for categoria, valor in TARIFAS.items():
        Tarifa.objects.create(categoria=categoria, valor=valor, vigente_desde=desde)


def crear_propietario(nombre: str, cedula: str, correo: str, activo: bool = True, telefono: str = "3001234567",
                      direccion: str = "Calle 10 # 20-30, Bogotá") -> Propietario:
    return Propietario.objects.create(
        nombre_completo=nombre, numero_documento=cedula, telefono=telefono, correo=correo,
        direccion=direccion, activo=activo, fecha_registro=reloj.ahora() - timedelta(days=200),
    )


def crear_vehiculo(propietario: Propietario, placa: str, tipo: str, marca: str, nombre: str, modelo: int, color: str,
                   activo: bool = True) -> Vehiculo:
    return Vehiculo.objects.create(
        placa=placa, tipo=tipo, marca=marca, nombre=nombre, modelo=modelo, color=color,
        propietario=propietario, activo=activo, fecha_registro=reloj.ahora() - timedelta(days=200),
    )


def crear_pago(vehiculo: Vehiculo, fin: date, registrado_por: Usuario, dias: int = 30) -> Pago:
    """Pago de un periodo que termina (vence) en 'fin'."""
    inicio = fin - timedelta(days=dias - 1)
    valor = TARIFAS[Categoria(vehiculo.categoria())]
    fecha_pago = reloj.ahora().replace(year=inicio.year, month=inicio.month, day=inicio.day, hour=8, minute=0)
    return Pago.objects.create(vehiculo=vehiculo, periodo_inicio=inicio, periodo_fin=fin, valor=valor,
                               fecha_pago=fecha_pago, registrado_por=registrado_por)


def crear_estadia(vehiculo: Vehiculo, codigo_celda: str, entrada: datetime, usuario: Usuario,
                  salida: datetime | None = None, usuario_salida: Usuario | None = None) -> Estadia:
    return Estadia.objects.create(
        vehiculo=vehiculo, celda=Celda.objects.get(codigo=codigo_celda), fecha_hora_entrada=entrada,
        usuario_entrada=usuario, fecha_hora_salida=salida, usuario_salida=usuario_salida if salida else None,
    )


def asignar_horario_24h(usuario: Usuario) -> None:
    """Todos los días, 24 horas: 00:00–12:00 y 12:00–00:00 (RN-36). Para demostración y pruebas."""
    from datetime import time

    from apps.cuentas.models import HorarioOperador

    HorarioOperador.objects.bulk_create(
        [HorarioOperador(operador=usuario, dia_semana=d, hora_inicio=time(0), hora_fin=time(12)) for d in range(1, 8)]
        + [HorarioOperador(operador=usuario, dia_semana=d, hora_inicio=time(12), hora_fin=time(0)) for d in range(1, 8)]
    )
