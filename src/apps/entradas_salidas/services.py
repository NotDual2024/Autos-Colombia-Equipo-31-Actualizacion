"""ServicioEstadias: registrar entradas y salidas (RF-001 a RF-004)."""
from django.db import IntegrityError, transaction

from apps.core import reloj
from apps.core.errores import ErrorNegocio
from apps.pagos import services as vigencia
from apps.usuarios_celdas.models import Celda, Vehiculo
from apps.usuarios_celdas.selectors import normalizar_placa, vehiculo_por_placa

from . import selectors
from .models import Estadia

MSG_NO_REGISTRADO = "Vehículo no registrado"
MSG_YA_DENTRO = "El vehículo ya se encuentra dentro"
MSG_NO_VIGENTE = "Mensualidad no vigente"
MSG_CELDA_TIPO = "La celda no corresponde al tipo de vehículo"
MSG_CELDA_OCUPADA = "La celda está ocupada"
MSG_SIN_CELDAS = "No hay celdas disponibles para este tipo de vehículo"
MSG_NO_DENTRO = "El vehículo no se encuentra dentro"
MSG_CLIENTE_INACTIVO = "El cliente está INACTIVO. No es posible registrar la entrada."
MSG_VEHICULO_INACTIVO = "El vehículo está INACTIVO. No es posible registrar la entrada."


def obtener_vehiculo(placa: str) -> Vehiculo:
    vehiculo = vehiculo_por_placa(placa)
    if vehiculo is None:
        raise ErrorNegocio(MSG_NO_REGISTRADO)
    return vehiculo


def validar_entrada(vehiculo: Vehiculo) -> None:
    """Reglas que se verifican antes de elegir la celda (RF-001, RF-002, RN-03, RN-04, RN-24)."""
    if not vehiculo.propietario.activo:
        raise ErrorNegocio(MSG_CLIENTE_INACTIVO)
    if not vehiculo.activo:
        raise ErrorNegocio(MSG_VEHICULO_INACTIVO)
    if selectors.estadia_abierta(vehiculo):
        raise ErrorNegocio(MSG_YA_DENTRO)
    if not vigencia.esta_vigente(vehiculo, reloj.hoy()):
        raise ErrorNegocio(MSG_NO_VIGENTE)
    if not any(not c["ocupada"] for c in selectors.celdas_de_categoria(vehiculo.categoria())):
        raise ErrorNegocio(MSG_SIN_CELDAS)


@transaction.atomic
def registrar_entrada(placa: str, codigo_celda: str, usuario) -> Estadia:
    """Registra la entrada en la celda elegida (RF-001, RF-003, RN-05, RN-08)."""
    vehiculo = obtener_vehiculo(placa)
    validar_entrada(vehiculo)
    celda = Celda.objects.filter(codigo=(codigo_celda or "").strip(), activa=True).first()
    if celda is None:
        raise ErrorNegocio("Selecciona una celda válida")
    if not celda.admite(vehiculo):
        raise ErrorNegocio(MSG_CELDA_TIPO)
    if Estadia.objects.filter(celda=celda, fecha_hora_salida__isnull=True).exists():
        raise ErrorNegocio(MSG_CELDA_OCUPADA)
    try:
        with transaction.atomic():
            return Estadia.objects.create(
                vehiculo=vehiculo, celda=celda, fecha_hora_entrada=reloj.ahora(), usuario_entrada=usuario
            )
    except IntegrityError:
        # Otra persona registró al mismo tiempo (RNF-003): la base de datos lo impidió.
        if selectors.estadia_abierta(vehiculo):
            raise ErrorNegocio(MSG_YA_DENTRO)
        raise ErrorNegocio(MSG_CELDA_OCUPADA)


def buscar_estadia_abierta(placa: str) -> Estadia:
    vehiculo = obtener_vehiculo(placa)
    estadia = selectors.estadia_abierta(vehiculo)
    if estadia is None:
        raise ErrorNegocio(MSG_NO_DENTRO)
    return estadia


@transaction.atomic
def registrar_salida(placa: str, usuario) -> Estadia:
    """Cierra la estadía abierta y libera la celda (RF-004). Se permite con mensualidad vencida (RN-13)."""
    estadia = buscar_estadia_abierta(normalizar_placa(placa))
    estadia.fecha_hora_salida = reloj.ahora()
    estadia.usuario_salida = usuario
    estadia.save(update_fields=["fecha_hora_salida", "usuario_salida"])
    return estadia
