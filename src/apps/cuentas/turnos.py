"""ServicioHorarios y ServicioAutorizaciones (RF-107, RF-110; RN-31, RN-32, RN-36, RN-37; DEC-014)."""
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from apps.bitacora import services as bitacora
from apps.bitacora.models import Accion, Entidad
from apps.core import reloj
from apps.core.errores import ErrorNegocio

from .models import DIAS, AutorizacionFueraTurno, HorarioOperador, Usuario
from .services import exigir_administrador, operador as obtener_operador

GRACIA = timedelta(minutes=5)  # RN-35
MSG_FUERA_TURNO = "Estás fuera de tu turno. Solicita autorización al administrador"
MSG_SIN_HORARIO = "No tienes un horario asignado. Contacta al administrador"


# ------------------------------------------------------------------ horarios
@transaction.atomic
def asignar_franja(administrador, operador_id: int, dia: int, inicio: time, fin: time) -> HorarioOperador:
    """UC-24 / HU-020."""
    exigir_administrador(administrador)
    operador = obtener_operador(operador_id)
    if dia not in DIAS:
        raise ErrorNegocio("Selecciona un día válido.")
    if inicio == fin:
        raise ErrorNegocio("La hora de inicio y la de fin no pueden ser iguales.")
    franja = HorarioOperador(operador=operador, dia_semana=dia, hora_inicio=inicio, hora_fin=fin)
    if any(franja.se_cruza_con(otra) for otra in operador.horarios.all()):
        raise ErrorNegocio("La franja se cruza con otra del mismo día")
    franja.save()
    bitacora.registrar(administrador, Accion.ASIGNAR_HORARIO, Entidad.OPERADOR, operador.pk,
                       f"Asignó a {operador.username} la franja {franja}")
    return franja


@transaction.atomic
def quitar_franja(administrador, franja_id: int) -> None:
    exigir_administrador(administrador)
    franja = HorarioOperador.objects.select_related("operador").filter(pk=franja_id).first()
    if franja is None:
        raise ErrorNegocio("La franja no existe.")
    descripcion = f"Quitó a {franja.operador.username} la franja {franja}"
    operador_id = franja.operador_id
    franja.delete()  # el horario es configuración; la bitácora conserva el cambio (HU-020)
    bitacora.registrar(administrador, Accion.QUITAR_HORARIO, Entidad.OPERADOR, operador_id, descripcion)


def franja_actual(usuario: Usuario, momento: datetime) -> HorarioOperador | None:
    return next((f for f in usuario.horarios.all() if f.cubre(momento)), None)


# ------------------------------------------------------------------ autorizaciones
@transaction.atomic
def autorizar(administrador, operador_id: int, desde: datetime, hasta: datetime, motivo: str) -> AutorizacionFueraTurno:
    """UC-27 / HU-022."""
    exigir_administrador(administrador)
    operador = obtener_operador(operador_id)
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorNegocio("Escribe el motivo de la autorización.")
    if hasta <= desde:
        raise ErrorNegocio("La hora de fin debe ser posterior a la de inicio.")
    autorizacion = AutorizacionFueraTurno.objects.create(
        operador=operador, autorizado_por=administrador, motivo=motivo, desde=desde, hasta=hasta, fecha_registro=reloj.ahora()
    )
    bitacora.registrar(administrador, Accion.AUTORIZAR_FUERA_TURNO, Entidad.OPERADOR, operador.pk,
                       f"Autorizó a {operador.username} fuera de turno: {timezone.localtime(desde):%d/%m %H:%M} – {timezone.localtime(hasta):%d/%m %H:%M}",
                       {"motivo": ["", motivo]})
    return autorizacion


def autorizacion_vigente(usuario: Usuario, momento: datetime) -> AutorizacionFueraTurno | None:
    return usuario.autorizaciones.filter(desde__lte=momento, hasta__gt=momento).order_by("-hasta").first()


# ------------------------------------------------------------------ control de turno
def motivo_bloqueo(usuario: Usuario, momento: datetime) -> str | None:
    """None si puede ingresar; si no, el mensaje (UC-25: RN-31, RN-32, RN-36)."""
    if usuario.es_administrador():
        return None
    if autorizacion_vigente(usuario, momento):
        return None
    if not usuario.horarios.exists():
        return MSG_SIN_HORARIO
    if franja_actual(usuario, momento) is None:
        return MSG_FUERA_TURNO
    return None


def puede_ingresar(usuario: Usuario, momento: datetime) -> bool:
    return motivo_bloqueo(usuario, momento) is None


def fin_de_jornada(usuario: Usuario, momento: datetime) -> datetime | None:
    """Hasta cuándo puede trabajar sin interrupción: encadena franjas contiguas y autorizaciones.

    None si es administrador (sin restricción) o si en este momento está fuera de turno.
    """
    if usuario.es_administrador():
        return None
    franjas = list(usuario.horarios.all())
    autorizaciones = list(usuario.autorizaciones.filter(hasta__gt=momento))
    fin = None
    actual = momento
    for _ in range(20):  # límite: unas 10 jornadas encadenadas
        candidatos = [f.fin_en(actual) for f in franjas if f.cubre(actual)]
        candidatos += [a.hasta for a in autorizaciones if a.vigente(actual)]
        candidatos = [c for c in candidatos if c and c > actual]
        if not candidatos:
            break
        fin = max(candidatos)
        actual = fin
    return fin


def texto_turno(usuario: Usuario, momento: datetime) -> str:
    """Encabezado: 'Turno 06:00 – 14:00' (RF-107) o la autorización vigente."""
    if usuario.es_administrador():
        return ""
    franja = franja_actual(usuario, momento)
    if franja:
        return f"Turno {franja.hora_inicio:%H:%M} – {franja.hora_fin:%H:%M}"
    autorizacion = autorizacion_vigente(usuario, momento)
    if autorizacion:
        return f"Autorizado hasta {timezone.localtime(autorizacion.hasta):%H:%M}"
    return "Fuera de turno"
