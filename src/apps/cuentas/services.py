"""ServicioOperadores: crear, editar, restablecer contraseña, activar y desactivar (RF-106, HU-010, HU-019)."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core.errores import ErrorNegocio

from .models import Rol, Usuario


def exigir_administrador(usuario) -> None:
    if not usuario.is_authenticated or not usuario.es_administrador():
        raise ErrorNegocio("Acceso denegado")


def _validar_clave(clave: str, usuario: Usuario) -> None:
    try:
        validate_password(clave, usuario)
    except ValidationError as error:
        raise ErrorNegocio(" ".join(error.messages))


def _nombres(nombre_completo: str) -> tuple[str, str]:
    nombre_completo = " ".join((nombre_completo or "").split())
    if not nombre_completo:
        raise ErrorNegocio("El nombre completo es obligatorio.")
    nombre, _, apellido = nombre_completo.partition(" ")
    return nombre, apellido


def operador(operador_id: int) -> Usuario:
    encontrado = Usuario.objects.filter(pk=operador_id, rol=Rol.OPERADOR).first()
    if encontrado is None:
        raise ErrorNegocio("Operador no encontrado")
    return encontrado


@transaction.atomic
def crear_operador(administrador, nombre_completo: str, nombre_usuario: str, clave: str) -> Usuario:
    exigir_administrador(administrador)
    nombre_usuario = (nombre_usuario or "").strip()
    nombre, apellido = _nombres(nombre_completo)
    if not nombre_usuario:
        raise ErrorNegocio("El nombre completo y el usuario son obligatorios.")
    if Usuario.objects.filter(username__iexact=nombre_usuario).exists():
        raise ErrorNegocio("El nombre de usuario ya existe")
    nuevo = Usuario(username=nombre_usuario, first_name=nombre, last_name=apellido, rol=Rol.OPERADOR)
    _validar_clave(clave, nuevo)
    nuevo.set_password(clave)
    nuevo.save()
    bitacora.registrar(administrador, Accion.CREAR, Entidad.OPERADOR, nuevo.pk, f"Creó al operador {nuevo.username}")
    return nuevo


@transaction.atomic
def editar_nombre(administrador, operador_id: int, nombre_completo: str) -> Usuario:
    """HU-019."""
    exigir_administrador(administrador)
    usuario = operador(operador_id)
    antes = usuario.nombre_completo()
    usuario.first_name, usuario.last_name = _nombres(nombre_completo)
    usuario.save(update_fields=["first_name", "last_name"])
    if antes != usuario.nombre_completo():
        bitacora.registrar(administrador, Accion.MODIFICAR, Entidad.OPERADOR, usuario.pk,
                           f"Editó el nombre del operador {usuario.username}", {"nombre": [antes, usuario.nombre_completo()]})
    return usuario


@transaction.atomic
def restablecer_clave(administrador, operador_id: int, clave: str, confirmacion: str) -> Usuario:
    """HU-019. La bitácora registra el hecho, nunca la contraseña (DM-11)."""
    exigir_administrador(administrador)
    usuario = operador(operador_id)
    if clave != confirmacion:
        raise ErrorNegocio("La confirmación no coincide con la contraseña.")
    _validar_clave(clave, usuario)
    usuario.set_password(clave)
    usuario.save(update_fields=["password"])
    bitacora.registrar(administrador, Accion.RESTABLECER_CLAVE, Entidad.OPERADOR, usuario.pk,
                       f"Restableció la contraseña del operador {usuario.username}")
    return usuario


@transaction.atomic
def cambiar_estado(administrador, operador_id: int, activo: bool) -> Usuario:
    """Desactivar o reactivar. Nunca se borra (RN-07)."""
    exigir_administrador(administrador)
    usuario = operador(operador_id)
    if usuario.is_active != activo:
        usuario.is_active = activo
        usuario.save(update_fields=["is_active"])
        bitacora.registrar(administrador, Accion.ACTIVAR if activo else Accion.INACTIVAR, Entidad.OPERADOR, usuario.pk,
                           f"{'Reactivó' if activo else 'Desactivó'} al operador {usuario.username}")
    return usuario
