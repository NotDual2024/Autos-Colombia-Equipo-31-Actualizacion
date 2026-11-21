"""ServicioTarifas y ServicioDescuentos (RF-204, RF-208, RN-42, RN-45)."""
from datetime import date

from django.db import IntegrityError, transaction

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core import reloj
from apps.core.errores import ErrorNegocio
from apps.usuarios_celdas.models import Categoria

from .models import Descuento, Tarifa


def _exigir_administrador(usuario) -> None:
    if not usuario.es_administrador():
        raise ErrorNegocio("Acceso denegado")


# ------------------------------------------------------------------ tarifas
def vigente(categoria: str, fecha: date) -> Tarifa:
    """Tarifa con la fecha 'vigente desde' más reciente que no sea posterior a 'fecha'."""
    tarifa = Tarifa.objects.filter(categoria=categoria, vigente_desde__lte=fecha).order_by("-vigente_desde").first()
    if tarifa is None:
        raise ErrorNegocio(f"No hay una tarifa vigente para {Categoria(categoria).label.lower()}.")
    return tarifa


def actuales(fecha: date) -> list[Tarifa]:
    resultado = []
    for categoria in Categoria.values:
        try:
            resultado.append(vigente(categoria, fecha))
        except ErrorNegocio:
            pass
    return resultado


def historial():
    return Tarifa.objects.all()


@transaction.atomic
def registrar_tarifa(administrador, categoria: str, valor, vigente_desde: date | None) -> Tarifa:
    """UC-38 / HU-027: tarifa nueva con su fecha (puede ser futura). Las anteriores no se editan."""
    _exigir_administrador(administrador)
    if categoria not in Categoria.values:
        raise ErrorNegocio("Elige el tipo de vehículo.")
    try:
        valor = int(str(valor).replace(".", "").replace(" ", ""))
    except ValueError:
        raise ErrorNegocio("El valor debe ser un número entero de pesos.")
    if valor <= 0:
        raise ErrorNegocio("El valor debe ser mayor que cero.")
    if vigente_desde is None:
        raise ErrorNegocio("Escribe la fecha desde la que rige la tarifa.")
    try:
        with transaction.atomic():
            tarifa = Tarifa.objects.create(categoria=categoria, valor=valor, vigente_desde=vigente_desde)
    except IntegrityError:
        raise ErrorNegocio(f"Ya existe una tarifa de {Categoria(categoria).label.lower()} desde esa fecha")
    bitacora.registrar(administrador, Accion.CREAR, Entidad.TARIFA, tarifa.pk,
                       f"Registró la tarifa de {tarifa.get_categoria_display().lower()}: {valor:,} COP desde "
                       f"{vigente_desde:%d/%m/%Y}".replace(",", " "))
    return tarifa


# ------------------------------------------------------------------ descuentos
def habilitados():
    return Descuento.objects.filter(habilitado=True).order_by("descripcion")


@transaction.atomic
def crear_descuento(administrador, descripcion: str, porcentaje) -> Descuento:
    """UC-39 / HU-031: descripción y porcentaje (1 a 100); queda habilitado."""
    _exigir_administrador(administrador)
    descripcion = " ".join((descripcion or "").split())
    if not descripcion:
        raise ErrorNegocio("Escribe la descripción del descuento.")
    try:
        porcentaje = int(str(porcentaje).strip())
    except ValueError:
        raise ErrorNegocio("El porcentaje debe estar entre 1 y 100")
    if not 1 <= porcentaje <= 100:
        raise ErrorNegocio("El porcentaje debe estar entre 1 y 100")
    descuento = Descuento.objects.create(descripcion=descripcion[:100], porcentaje=porcentaje, habilitado=True,
                                         creado_por=administrador, fecha_creacion=reloj.ahora())
    bitacora.registrar(administrador, Accion.CREAR, Entidad.DESCUENTO, descuento.pk,
                       f"Creó el descuento {descuento.descripcion} ({porcentaje} %)")
    return descuento


@transaction.atomic
def cambiar_estado_descuento(administrador, descuento: Descuento, habilitado: bool) -> Descuento:
    _exigir_administrador(administrador)
    if descuento.habilitado != habilitado:
        descuento.habilitado = habilitado
        descuento.save(update_fields=["habilitado"])
        bitacora.registrar(administrador, Accion.HABILITAR if habilitado else Accion.DESHABILITAR, Entidad.DESCUENTO,
                           descuento.pk, f"{'Habilitó' if habilitado else 'Deshabilitó'} el descuento {descuento}")
    return descuento
