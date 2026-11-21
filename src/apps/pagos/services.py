"""ServicioVigencia: vigencia de la mensualidad (RF-002, RF-009, RF-202, RN-03, RN-10, RN-38, RN-39, DM-12).

Solo cuentan los pagos REGISTRADOS: un pago corregido deja de contar para la entrada, los avisos y el mapa
sin cambiar el código de esos módulos (diseño iteración 3, sección 3.2).
"""
from dataclasses import dataclass
from datetime import date

from django.db.models import QuerySet

from apps.usuarios_celdas.models import Vehiculo

from . import calendario
from .models import EstadoPago, Pago

AL_DIA, VENCE_HOY, VENCIDA, SIN_PAGOS = "AL_DIA", "VENCE_HOY", "VENCIDA", "SIN_PAGOS"


@dataclass(frozen=True)
class EstadoVigencia:
    estado: str
    vencimiento: date | None = None
    dias_vencida: int = 0
    dia_cobro: int | None = None
    meses_pendientes: int = 0
    ultimo_pago: Pago | None = None

    @property
    def texto(self) -> str:
        if self.estado == AL_DIA:
            return "Al día"
        if self.estado == VENCE_HOY:
            return "Vence hoy"
        if self.estado == VENCIDA:
            return f"Vencida hace {self.dias_vencida} día{'s' if self.dias_vencida != 1 else ''}"
        return "Sin pagos"

    @property
    def puede_entrar(self) -> bool:
        return self.estado in (AL_DIA, VENCE_HOY)


def pagos_validos(vehiculo: Vehiculo) -> QuerySet[Pago]:
    return vehiculo.pagos.filter(estado=EstadoPago.REGISTRADO)


def ultimo_pago(vehiculo: Vehiculo) -> Pago | None:
    """Pago registrado con el periodo que termina más tarde (define el vencimiento actual)."""
    return pagos_validos(vehiculo).order_by("-periodo_fin", "-id").first()


def esta_vigente(vehiculo: Vehiculo, fecha: date) -> bool:
    """La mensualidad está vigente si algún pago registrado cubre la fecha (incluido el día de vencimiento)."""
    return pagos_validos(vehiculo).filter(periodo_inicio__lte=fecha, periodo_fin__gte=fecha).exists()


def ancla(vehiculo: Vehiculo) -> date | None:
    """DM-12: inicio del primer pago registrado; su día es el día de cobro."""
    primero = pagos_validos(vehiculo).order_by("periodo_inicio", "id").first()
    return primero.periodo_inicio if primero else None


def dia_cobro(vehiculo: Vehiculo) -> int | None:
    a = ancla(vehiculo)
    return a.day if a else None


def estado(vehiculo: Vehiculo, hoy: date) -> EstadoVigencia:
    """RF-202: al día, vence hoy, vencida hace N días o sin pagos, con los meses pendientes."""
    ultimo = ultimo_pago(vehiculo)
    if ultimo is None:
        return EstadoVigencia(SIN_PAGOS)
    a = ancla(vehiculo)
    fin = ultimo.periodo_fin
    comun = {"vencimiento": fin, "dia_cobro": a.day, "ultimo_pago": ultimo}
    if fin > hoy:
        return EstadoVigencia(AL_DIA, **comun)
    if fin == hoy:
        return EstadoVigencia(VENCE_HOY, **comun)
    return EstadoVigencia(VENCIDA, dias_vencida=(hoy - fin).days,
                          meses_pendientes=calendario.meses_pendientes(a, fin, hoy), **comun)
