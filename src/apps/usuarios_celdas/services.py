"""Servicios de propietarios, vehículos y cambio de propietario (RF-101, RF-102, RF-105, RF-109).

Reglas: RN-23, RN-25, RN-26, RN-29, RN-30, RN-33, RN-34. Cada operación se registra en la bitácora (DEC-013).
"""
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core import reloj
from apps.core.errores import ErrorNegocio

from .models import (EstadoSolicitud, HistorialPropiedad, Propietario, SolicitudCambioPropietario,
                     TipoVehiculo, Vehiculo)
from .selectors import normalizar_placa

CAMPOS_PROPIETARIO = ["nombre_completo", "numero_documento", "telefono", "correo", "direccion"]
CAMPOS_VEHICULO = ["tipo", "marca", "nombre", "modelo", "color"]
FORMATOS_PLACA = {
    TipoVehiculo.CARRO: [r"[A-Z]{3}\d{3}"],
    TipoVehiculo.CAMIONETA: [r"[A-Z]{3}\d{3}"],
    TipoVehiculo.MOTO: [r"[A-Z]{3}\d{2}[A-Z]", r"[A-Z]{3}\d{2}"],
}


# ------------------------------------------------------------------ propietarios
def _validar_propietario(datos: dict, excluir_id: int | None = None) -> dict:
    limpio = {c: " ".join(str(datos.get(c, "")).split()) for c in CAMPOS_PROPIETARIO}
    faltantes = [c for c, v in limpio.items() if not v]
    if faltantes:
        raise ErrorNegocio("Todos los campos son obligatorios.")
    if not re.fullmatch(r"\d{5,10}", limpio["numero_documento"]):
        raise ErrorNegocio("La cédula debe tener entre 5 y 10 dígitos.")
    if not re.fullmatch(r"3\d{9}", limpio["telefono"]):
        raise ErrorNegocio("El celular debe tener 10 dígitos y empezar por 3")
    try:
        validate_email(limpio["correo"])
    except ValidationError:
        raise ErrorNegocio("El correo no tiene un formato válido.")
    repetido = Propietario.objects.filter(numero_documento=limpio["numero_documento"]).exclude(pk=excluir_id)
    if repetido.exists():
        raise ErrorNegocio("Ya existe un propietario con esa cédula")
    limpio["correo"] = limpio["correo"].lower()
    return limpio


@transaction.atomic
def registrar_propietario(datos: dict, usuario) -> Propietario:
    """UC-16 / HU-012."""
    limpio = _validar_propietario(datos)
    propietario = Propietario.objects.create(**limpio, activo=True, fecha_registro=reloj.ahora())
    bitacora.registrar(usuario, Accion.CREAR, Entidad.PROPIETARIO, propietario.pk,
                       f"Registró al propietario {propietario.nombre_completo}")
    return propietario


@transaction.atomic
def modificar_propietario(propietario: Propietario, datos: dict, usuario) -> Propietario:
    """UC-19 / HU-015: guarda los valores antes y después en la bitácora."""
    antes = bitacora.instantanea(propietario, CAMPOS_PROPIETARIO)
    limpio = _validar_propietario(datos, excluir_id=propietario.pk)
    for campo, valor in limpio.items():
        setattr(propietario, campo, valor)
    propietario.save()
    cambios = bitacora.diferencias(antes, bitacora.instantanea(propietario, CAMPOS_PROPIETARIO))
    if cambios:
        bitacora.registrar(usuario, Accion.MODIFICAR, Entidad.PROPIETARIO, propietario.pk,
                           f"Modificó al propietario {propietario.nombre_completo}", cambios)
    return propietario


@transaction.atomic
def cambiar_estado_propietario(propietario: Propietario, activo: bool, usuario) -> Propietario:
    """Activar o inactivar (RN-07: nunca se borra; RN-29: inactivo no entra)."""
    if propietario.activo != activo:
        propietario.activo = activo
        propietario.save(update_fields=["activo"])
        bitacora.registrar(usuario, Accion.ACTIVAR if activo else Accion.INACTIVAR, Entidad.PROPIETARIO,
                           propietario.pk, f"{'Activó' if activo else 'Inactivó'} al propietario {propietario.nombre_completo}")
    return propietario


# ------------------------------------------------------------------ vehículos
def validar_placa_para_tipo(placa: str, tipo: str) -> str:
    """RN-23: carro y camioneta ABC123; moto ABC12D o ABC12."""
    if tipo not in TipoVehiculo.values:
        raise ErrorNegocio("Selecciona un tipo de vehículo válido.")
    if not any(re.fullmatch(p, placa) for p in FORMATOS_PLACA[tipo]):
        raise ErrorNegocio("La placa no corresponde al tipo de vehículo")
    return placa


def _validar_datos_vehiculo(datos: dict) -> dict:
    limpio = {c: " ".join(str(datos.get(c, "")).split()) for c in CAMPOS_VEHICULO}
    if any(not v for v in limpio.values()):
        raise ErrorNegocio("Todos los campos son obligatorios.")
    try:
        modelo = int(limpio["modelo"])
    except ValueError:
        raise ErrorNegocio("El modelo debe ser un año, por ejemplo 2020.")
    maximo = reloj.hoy().year + 1
    if not 1950 <= modelo <= maximo:
        raise ErrorNegocio(f"El modelo debe estar entre 1950 y {maximo}.")
    limpio["modelo"] = modelo
    return limpio


@transaction.atomic
def registrar_vehiculo(placa: str, datos: dict, propietario: Propietario, usuario) -> Vehiculo:
    """UC-17 / HU-013."""
    placa = normalizar_placa(placa)
    limpio = _validar_datos_vehiculo(datos)
    validar_placa_para_tipo(placa, limpio["tipo"])
    if Vehiculo.objects.filter(placa=placa).exists():
        raise ErrorNegocio("Ya existe un vehículo con esa placa")
    if not propietario.activo:
        raise ErrorNegocio("El propietario está inactivo")
    vehiculo = Vehiculo.objects.create(placa=placa, propietario=propietario, activo=True, fecha_registro=reloj.ahora(), **limpio)
    bitacora.registrar(usuario, Accion.CREAR, Entidad.VEHICULO, vehiculo.pk,
                       f"Registró el vehículo {placa} de {propietario.nombre_completo}")
    return vehiculo


@transaction.atomic
def modificar_vehiculo(vehiculo: Vehiculo, datos: dict, usuario) -> Vehiculo:
    """UC-19 / HU-015. La placa no se edita (RN-26) ni el propietario (RF-109)."""
    antes = bitacora.instantanea(vehiculo, CAMPOS_VEHICULO)
    limpio = _validar_datos_vehiculo(datos)
    validar_placa_para_tipo(vehiculo.placa, limpio["tipo"])
    for campo, valor in limpio.items():
        setattr(vehiculo, campo, valor)
    vehiculo.save()
    cambios = bitacora.diferencias(antes, bitacora.instantanea(vehiculo, CAMPOS_VEHICULO))
    if cambios:
        bitacora.registrar(usuario, Accion.MODIFICAR, Entidad.VEHICULO, vehiculo.pk, f"Modificó el vehículo {vehiculo.placa}", cambios)
    return vehiculo


@transaction.atomic
def cambiar_estado_vehiculo(vehiculo: Vehiculo, activo: bool, usuario) -> Vehiculo:
    if vehiculo.activo != activo:
        vehiculo.activo = activo
        vehiculo.save(update_fields=["activo"])
        bitacora.registrar(usuario, Accion.ACTIVAR if activo else Accion.INACTIVAR, Entidad.VEHICULO, vehiculo.pk,
                           f"{'Activó' if activo else 'Inactivó'} el vehículo {vehiculo.placa}")
    return vehiculo


# ------------------------------------------------------------------ cambio de propietario
@transaction.atomic
def solicitar_cambio(vehiculo: Vehiculo, nuevo: Propietario, motivo: str, usuario) -> SolicitudCambioPropietario:
    """UC-20 / HU-016."""
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorNegocio("Escribe el motivo de la solicitud.")
    if nuevo.pk == vehiculo.propietario_id:
        raise ErrorNegocio("El nuevo propietario debe ser distinto del actual.")
    if not nuevo.activo:
        raise ErrorNegocio("El nuevo propietario está inactivo.")
    if vehiculo.solicitudes_cambio.filter(estado=EstadoSolicitud.PENDIENTE).exists():
        raise ErrorNegocio("Ya hay una solicitud pendiente para este vehículo")
    try:
        with transaction.atomic():
            solicitud = SolicitudCambioPropietario.objects.create(
                vehiculo=vehiculo, propietario_actual=vehiculo.propietario, propietario_nuevo=nuevo,
                motivo=motivo, solicitado_por=usuario, fecha_solicitud=reloj.ahora(),
            )
    except IntegrityError:
        raise ErrorNegocio("Ya hay una solicitud pendiente para este vehículo")
    bitacora.registrar(usuario, Accion.SOLICITAR_CAMBIO, Entidad.VEHICULO, vehiculo.pk,
                       f"Solicitó cambiar el propietario de {vehiculo.placa}: {vehiculo.propietario.nombre_completo} → {nuevo.nombre_completo}",
                       {"motivo": ["", motivo], "solicitud": ["", str(solicitud.pk)]})
    return solicitud


def _exigir_administrador(usuario) -> None:
    if not usuario.es_administrador():
        raise ErrorNegocio("Acceso denegado")


def _pendiente(solicitud_id: int) -> SolicitudCambioPropietario:
    solicitud = (SolicitudCambioPropietario.objects.select_for_update()
                 .select_related("vehiculo", "propietario_actual", "propietario_nuevo").filter(pk=solicitud_id).first())
    if solicitud is None or solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise ErrorNegocio("La solicitud ya fue resuelta o no existe.")
    return solicitud


@transaction.atomic
def aprobar_cambio(solicitud_id: int, administrador, observacion: str = "") -> Vehiculo:
    """UC-21 / HU-017: historial + cambio de propietario + estado, todo en una transacción (RN-33)."""
    _exigir_administrador(administrador)
    solicitud = _pendiente(solicitud_id)
    vehiculo = solicitud.vehiculo
    if vehiculo.propietario_id != solicitud.propietario_actual_id:
        raise ErrorNegocio("El propietario del vehículo cambió después de la solicitud. Recházala y crea una nueva.")
    if not solicitud.propietario_nuevo.activo:
        raise ErrorNegocio("El nuevo propietario está inactivo.")
    ahora = reloj.ahora()
    HistorialPropiedad.objects.create(vehiculo=vehiculo, propietario=solicitud.propietario_actual,
                                      desde=vehiculo.propietario_desde(), hasta=ahora)
    vehiculo.propietario = solicitud.propietario_nuevo
    vehiculo.save(update_fields=["propietario"])
    solicitud.estado, solicitud.resuelto_por, solicitud.fecha_resolucion = EstadoSolicitud.APROBADA, administrador, ahora
    solicitud.observacion = (observacion or "").strip() or None
    solicitud.save()
    bitacora.registrar(administrador, Accion.APROBAR_CAMBIO, Entidad.VEHICULO, vehiculo.pk,
                       f"Aprobó el cambio de propietario de {vehiculo.placa}",
                       {"propietario": [solicitud.propietario_actual.nombre_completo, solicitud.propietario_nuevo.nombre_completo]})
    return vehiculo


@transaction.atomic
def rechazar_cambio(solicitud_id: int, administrador, observacion: str) -> SolicitudCambioPropietario:
    _exigir_administrador(administrador)
    observacion = (observacion or "").strip()
    if not observacion:
        raise ErrorNegocio("Escribe una observación para rechazar la solicitud.")
    solicitud = _pendiente(solicitud_id)
    solicitud.estado, solicitud.resuelto_por, solicitud.fecha_resolucion = EstadoSolicitud.RECHAZADA, administrador, reloj.ahora()
    solicitud.observacion = observacion
    solicitud.save()
    bitacora.registrar(administrador, Accion.RECHAZAR_CAMBIO, Entidad.VEHICULO, solicitud.vehiculo_id,
                       f"Rechazó el cambio de propietario de {solicitud.vehiculo.placa}", {"observacion": ["", observacion]})
    return solicitud
