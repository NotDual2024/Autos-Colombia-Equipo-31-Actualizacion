"""ServicioOperadores: crear, desactivar y reactivar operadores (RF-106, HU-010)."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.errores import ErrorNegocio

from .models import Rol, Usuario


def _exigir_administrador(usuario) -> None:
    if not usuario.is_authenticated or not usuario.es_administrador():
        raise ErrorNegocio("Acceso denegado")


@transaction.atomic
def crear_operador(administrador, nombre_completo: str, nombre_usuario: str, clave: str) -> Usuario:
    _exigir_administrador(administrador)
    nombre_usuario = (nombre_usuario or "").strip()
    nombre_completo = " ".join((nombre_completo or "").split())
    if not nombre_completo or not nombre_usuario:
        raise ErrorNegocio("El nombre completo y el usuario son obligatorios.")
    if Usuario.objects.filter(username__iexact=nombre_usuario).exists():
        raise ErrorNegocio("El nombre de usuario ya existe")
    nombre, _, apellido = nombre_completo.partition(" ")
    operador = Usuario(username=nombre_usuario, first_name=nombre, last_name=apellido, rol=Rol.OPERADOR)
    try:
        validate_password(clave, operador)
    except ValidationError as error:
        raise ErrorNegocio(" ".join(error.messages))
    operador.set_password(clave)
    operador.save()
    return operador


def cambiar_estado(administrador, operador_id: int, activo: bool) -> Usuario:
    """Desactivar o reactivar. Nunca se borra (RN-07)."""
    _exigir_administrador(administrador)
    operador = Usuario.objects.filter(pk=operador_id, rol=Rol.OPERADOR).first()
    if operador is None:
        raise ErrorNegocio("Operador no encontrado")
    operador.is_active = activo
    operador.save(update_fields=["is_active"])
    return operador
