"""ServicioCeldas: creación y administración de celdas por el administrador (RF-103, CHG-003, RN-48 a RN-53).

La ocupación y el historial se consultan con la relación inversa "estadias" (sin importar entradas_salidas),
igual que el mapa de celdas, para no crear un ciclo de dependencias entre módulos (PK-01).
"""
import re
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core.errores import ErrorNegocio

from .models import Categoria, Celda

FORMATOS = {
    Categoria.CARRO_CAMIONETA: (r"A-\d{3}", "A", 3, "El código de una celda de carro/camioneta debe tener el formato A-001 a A-999"),
    Categoria.MOTO: (r"M-\d{2}", "M", 2, "El código de una celda de moto debe tener el formato M-01 a M-99"),
}
LIBRE, OCUPADA, INACTIVA = "LIBRE", "OCUPADA", "INACTIVA"


def _exigir_administrador(usuario) -> None:
    if not usuario.es_administrador():
        raise ErrorNegocio("Acceso denegado")


def _tipo_valido(tipo: str) -> str:
    if tipo not in Categoria.values:
        raise ErrorNegocio("Elige el tipo de celda.")
    return tipo


def normalizar_codigo(codigo: str) -> str:
    return "".join((codigo or "").split()).upper()


def validar_codigo(codigo: str, tipo: str, excluir_id: int | None = None) -> str:
    """RN-49: formato según el tipo y código único (sin importar mayúsculas)."""
    codigo = normalizar_codigo(codigo)
    patron, prefijo, digitos, mensaje = FORMATOS[_tipo_valido(tipo)]
    if not re.fullmatch(patron, codigo) or int(codigo[2:]) == 0:
        raise ErrorNegocio(mensaje)
    if Celda.objects.filter(codigo__iexact=codigo).exclude(pk=excluir_id).exists():
        raise ErrorNegocio(f"Ya existe una celda con el código {codigo}")
    return codigo


def siguiente_codigo(tipo: str) -> str | None:
    """Sugiere el número siguiente al mayor código existente del tipo (o el primer hueco si se llegó al límite)."""
    _, prefijo, digitos, _ = FORMATOS[_tipo_valido(tipo)]
    usados = {int(c[2:]) for c in Celda.objects.filter(codigo__startswith=f"{prefijo}-").values_list("codigo", flat=True)
              if c[2:].isdigit()}
    maximo = 10 ** digitos - 1
    candidato = max(usados, default=0) + 1
    if candidato > maximo:
        candidato = next((n for n in range(1, maximo + 1) if n not in usados), None)
    return None if candidato is None else f"{prefijo}-{candidato:0{digitos}d}"


def esta_ocupada(celda: Celda) -> bool:
    return celda.estadias.filter(fecha_hora_salida__isnull=True).exists()


def tiene_historial(celda: Celda) -> bool:
    return celda.estadias.exists()


@dataclass
class FilaCelda:
    celda: Celda
    estado: str
    placa: str | None
    usada: bool


def listar(tipo: str = "", estado: str = "", texto: str = "") -> list[FilaCelda]:
    """HU-034: lista con estado (libre, ocupada con la placa, o inactiva) y filtros."""
    qs: QuerySet = Celda.objects.all().order_by("tipo", "codigo")
    if tipo in Categoria.values:
        qs = qs.filter(tipo=tipo)
    if texto:
        qs = qs.filter(codigo__icontains=normalizar_codigo(texto))
    ocupadas = dict(Celda.objects.filter(estadias__isnull=False, estadias__fecha_hora_salida__isnull=True)
                    .values_list("id", "estadias__vehiculo__placa"))
    usadas = set(Celda.objects.filter(estadias__isnull=False).values_list("id", flat=True))
    filas = []
    for c in qs:
        e = INACTIVA if not c.activa else OCUPADA if c.id in ocupadas else LIBRE
        if estado and e != estado:
            continue
        filas.append(FilaCelda(c, e, ocupadas.get(c.id), c.id in usadas))
    return filas


@transaction.atomic
def crear(administrador, tipo: str, codigo: str | None = None) -> Celda:
    """UC-41 / HU-033."""
    _exigir_administrador(administrador)
    tipo = _tipo_valido(tipo)
    codigo = codigo if normalizar_codigo(codigo or "") else siguiente_codigo(tipo)
    if codigo is None:
        raise ErrorNegocio("No quedan códigos libres para este tipo de celda.")
    codigo = validar_codigo(codigo, tipo)
    try:
        with transaction.atomic():
            celda = Celda.objects.create(codigo=codigo, tipo=tipo, activa=True)
    except IntegrityError:
        raise ErrorNegocio(f"Ya existe una celda con el código {codigo}")
    bitacora.registrar(administrador, Accion.CREAR, Entidad.CELDA, celda.pk,
                       f"Creó la celda {codigo} ({celda.get_tipo_display().lower()})")
    return celda


@transaction.atomic
def cambiar_tipo(administrador, celda: Celda, tipo: str, codigo: str | None = None) -> Celda:
    """UC-42 / HU-034, RN-52: solo una celda libre que nunca se usó; recibe un código del tipo nuevo."""
    _exigir_administrador(administrador)
    tipo = _tipo_valido(tipo)
    if tipo == celda.tipo:
        raise ErrorNegocio("La celda ya es de ese tipo.")
    if esta_ocupada(celda):
        raise ErrorNegocio("La celda está ocupada")
    if tiene_historial(celda):
        raise ErrorNegocio("La celda ya se usó; inactívala y crea una nueva")
    codigo = validar_codigo(codigo if normalizar_codigo(codigo or "") else siguiente_codigo(tipo) or "", tipo, celda.pk)
    antes = {"tipo": celda.get_tipo_display(), "codigo": celda.codigo}
    celda.tipo, celda.codigo = tipo, codigo
    celda.save(update_fields=["tipo", "codigo"])
    bitacora.registrar(administrador, Accion.MODIFICAR, Entidad.CELDA, celda.pk,
                       f"Cambió el tipo de la celda {antes['codigo']} a {celda.get_tipo_display().lower()} ({codigo})",
                       {"tipo": [antes["tipo"], celda.get_tipo_display()], "codigo": [antes["codigo"], codigo]})
    return celda


@transaction.atomic
def inactivar(administrador, celda: Celda, motivo: str) -> Celda:
    """UC-43 / HU-035, RN-50, RN-51."""
    _exigir_administrador(administrador)
    motivo = " ".join((motivo or "").split())
    if not motivo:
        raise ErrorNegocio("Escribe el motivo de la inactivación.")
    if not celda.activa:
        raise ErrorNegocio("La celda ya está inactiva.")
    if esta_ocupada(celda):
        raise ErrorNegocio("La celda está ocupada")
    celda.activa, celda.motivo_inactivacion = False, motivo[:100]
    celda.save(update_fields=["activa", "motivo_inactivacion"])
    bitacora.registrar(administrador, Accion.INACTIVAR, Entidad.CELDA, celda.pk, f"Inactivó la celda {celda.codigo}",
                       {"motivo_inactivacion": ["", celda.motivo_inactivacion]})
    return celda


@transaction.atomic
def reactivar(administrador, celda: Celda) -> Celda:
    """UC-43 / HU-035."""
    _exigir_administrador(administrador)
    if celda.activa:
        raise ErrorNegocio("La celda ya está activa.")
    motivo = celda.motivo_inactivacion
    celda.activa, celda.motivo_inactivacion = True, None
    celda.save(update_fields=["activa", "motivo_inactivacion"])
    bitacora.registrar(administrador, Accion.ACTIVAR, Entidad.CELDA, celda.pk, f"Reactivó la celda {celda.codigo}",
                       {"motivo_inactivacion": [motivo, ""]})
    return celda


@transaction.atomic
def eliminar(administrador, celda: Celda) -> str:
    """UC-44 / HU-036, RN-52: solo si nunca se usó (la clave foránea de la estadía también lo impide)."""
    _exigir_administrador(administrador)
    if esta_ocupada(celda):
        raise ErrorNegocio("La celda está ocupada")
    if tiene_historial(celda):
        raise ErrorNegocio("La celda tiene historial; solo se puede inactivar")
    codigo, pk = celda.codigo, celda.pk
    celda.delete()
    bitacora.registrar(administrador, Accion.ELIMINAR, Entidad.CELDA, pk, f"Eliminó la celda {codigo}")
    return codigo


__all__ = ["listar", "crear", "cambiar_tipo", "inactivar", "reactivar", "eliminar", "siguiente_codigo",
           "validar_codigo", "esta_ocupada", "tiene_historial", "LIBRE", "OCUPADA", "INACTIVA"]
