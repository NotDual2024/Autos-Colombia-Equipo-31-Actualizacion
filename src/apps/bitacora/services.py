"""ServicioBitacora (DEC-013): registra y consulta las operaciones."""
from datetime import date, datetime, time

from django.db.models import Model, QuerySet
from django.utils import timezone

from apps.core import reloj

from .models import Accion, Entidad, RegistroOperacion

CAMPOS_SENSIBLES = {"password", "clave"}  # DM-11: nunca se guardan


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, Model):
        return str(valor)
    return str(valor)


def instantanea(objeto: Model, campos: list[str]) -> dict[str, str]:
    """Valores actuales de los campos, como texto, para comparar antes y después."""
    return {c: _texto(getattr(objeto, c)) for c in campos if c not in CAMPOS_SENSIBLES}


def diferencias(antes: dict[str, str], despues: dict[str, str]) -> dict[str, list[str]]:
    return {c: [antes.get(c, ""), despues.get(c, "")] for c in despues if antes.get(c) != despues.get(c)}


def registrar(usuario, accion: str, entidad: str, entidad_id: int, descripcion: str, cambios: dict | None = None) -> RegistroOperacion:
    """UC-29. Se llama dentro de la misma transacción de la operación registrada."""
    cambios = {k: v for k, v in (cambios or {}).items() if k not in CAMPOS_SENSIBLES} or None
    return RegistroOperacion.objects.create(
        fecha_hora=reloj.ahora(), usuario=usuario, accion=accion, entidad=entidad,
        entidad_id=entidad_id, descripcion=descripcion[:255], detalle=cambios,
    )


def de_entidad(entidad: str, entidad_id: int) -> QuerySet[RegistroOperacion]:
    return RegistroOperacion.objects.filter(entidad=entidad, entidad_id=entidad_id).select_related("usuario")


def buscar(usuario_id: int | None = None, accion: str | None = None, desde: date | None = None, hasta: date | None = None) -> QuerySet[RegistroOperacion]:
    qs = RegistroOperacion.objects.select_related("usuario")
    if usuario_id:
        qs = qs.filter(usuario_id=usuario_id)
    if accion:
        qs = qs.filter(accion=accion)
    zona = timezone.get_current_timezone()
    if desde:
        qs = qs.filter(fecha_hora__gte=datetime.combine(desde, time.min, tzinfo=zona))
    if hasta:
        qs = qs.filter(fecha_hora__lte=datetime.combine(hasta, time.max, tzinfo=zona))
    return qs


__all__ = ["Accion", "Entidad", "registrar", "de_entidad", "buscar", "instantanea", "diferencias"]
